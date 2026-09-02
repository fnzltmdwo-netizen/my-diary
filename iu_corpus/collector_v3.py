import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, quote, urlparse
from urllib.request import Request, urlopen

from openai import OpenAI

try:
    from youtube_transcript_api import YouTubeTranscriptApi
except Exception:
    YouTubeTranscriptApi = None

ROOT = Path(__file__).resolve().parent
DISCOVERY = json.loads((ROOT / "discovery.json").read_text(encoding="utf-8"))
SOURCES_PATH = ROOT / "source_registry.jsonl"
OBS_PATH = ROOT / "observations.jsonl"
ERROR_PATH = ROOT / "errors.jsonl"
SUMMARY_PATH = ROOT / "run_summary.json"

MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
MAX_VIDEOS = int(os.getenv("MAX_VIDEOS", "150"))
MAX_AI_CALLS = int(os.getenv("MAX_AI_CALLS", "220"))
MAX_DISCOVERY_CALLS = int(os.getenv("MAX_DISCOVERY_CALLS", "14"))
SEARCH_BATCH_SIZE = int(os.getenv("SEARCH_BATCH_SIZE", "5"))

PREFERRED = {x.lower() for x in DISCOVERY.get("preferred_channels", [])}
KEYWORDS = ["아이유", " iu ", "iu(", "iu ", "이지금", "lee jieun", "lee ji-eun"]


def now():
    return datetime.now(timezone.utc).isoformat()


def append_jsonl(path: Path, obj: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def load_jsonl(path: Path):
    out = []
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            out.append(json.loads(line))
        except Exception:
            pass
    return out


def video_id_from_url(url: str):
    if not url:
        return None
    url = url.strip().rstrip(').,]\"\'')
    if "youtu.be/" in url:
        return url.split("youtu.be/", 1)[1].split("?", 1)[0].split("/", 1)[0]
    p = urlparse(url)
    host = (p.netloc or "").lower()
    if host.endswith("youtube.com"):
        if p.path == "/watch":
            return parse_qs(p.query).get("v", [None])[0]
        if p.path.startswith("/shorts/"):
            return p.path.split("/shorts/", 1)[1].split("/", 1)[0]
    return None


def clean_youtube_url(url: str):
    vid = video_id_from_url(url)
    if not vid or not re.fullmatch(r"[A-Za-z0-9_-]{6,20}", vid):
        return None
    return f"https://www.youtube.com/watch?v={vid}"


def tier_for(channel: str):
    c = (channel or "").lower()
    if "iu official" in c or "이지금" in c or "1thek" in c:
        return "A++"
    if any(x in c for x in ["tvn", "jtbc", "kbs", "sbs", "mbc", "mnet", "billboard", "vogue", "elle", "gq", "bazaar", "marie claire", "netflix", "teo", "백상"]):
        return "A++"
    return "C"


def relevant(title: str, channel: str):
    c = (channel or "").lower()
    text = f" {title or ''} {channel or ''} ".lower()
    return c in PREFERRED or any(k in text for k in KEYWORDS)


def oembed(url: str):
    endpoint = "https://www.youtube.com/oembed?format=json&url=" + quote(url, safe="")
    req = Request(endpoint, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urlopen(req, timeout=12) as r:
            data = json.loads(r.read().decode("utf-8"))
        return {"title": data.get("title", ""), "channel": data.get("author_name", "")}
    except Exception as ex:
        append_jsonl(ERROR_PATH, {"stage": "oembed", "url": url, "error": str(ex)[:500], "at": now()})
        return None


def response_dump(resp):
    try:
        return resp.model_dump()
    except Exception:
        try:
            return json.loads(resp.model_dump_json())
        except Exception:
            return {}


def collect_urls(obj, out=None):
    if out is None:
        out = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in {"url", "link", "href"} and isinstance(v, str):
                out.add(v)
            collect_urls(v, out)
    elif isinstance(obj, list):
        for v in obj:
            collect_urls(v, out)
    elif isinstance(obj, str):
        for u in re.findall(r"https?://[^\s<>\"']+", obj):
            out.add(u.rstrip(').,];'))
    return out


def discover_with_web(client):
    found = {}
    for url in DISCOVERY.get("seed_videos", []):
        clean = clean_youtube_url(url)
        if clean:
            found[video_id_from_url(clean)] = {"url": clean, "discovered_by": "seed"}

    queries = DISCOVERY.get("youtube_search_queries", [])
    calls = 0
    for i in range(0, len(queries), SEARCH_BATCH_SIZE):
        if calls >= MAX_DISCOVERY_CALLS or len(found) >= MAX_VIDEOS * 4:
            break
        batch = queries[i:i + SEARCH_BATCH_SIZE]
        prompt = (
            "Search the public web for YouTube videos where IU (아이유/이지은/Lee Ji-eun) herself speaks at meaningful length: interviews, talk shows, official behind-the-scenes, concert talking segments, acceptance speeches, press interviews. "
            "Prioritize official IU, broadcasters, major magazines/newspapers, Billboard, Netflix, TEO, 1theK. Exclude pure music videos and performance-only clips. "
            "Topics: " + ", ".join(batch) + ". Find real YouTube watch URLs. In the final answer, list the useful YouTube URLs plainly."
        )
        try:
            resp = client.responses.create(
                model=MODEL,
                tools=[{"type": "web_search"}],
                include=["web_search_call.action.sources"],
                input=prompt,
                max_output_tokens=1800,
            )
            calls += 1
            text = getattr(resp, "output_text", "") or ""
            dump = response_dump(resp)
            raw_urls = collect_urls(dump) | collect_urls(text)
            yt_urls = set()
            for raw in raw_urls:
                clean = clean_youtube_url(raw)
                if clean:
                    yt_urls.add(clean)
            for clean in yt_urls:
                vid = video_id_from_url(clean)
                found.setdefault(vid, {"url": clean, "discovered_by": "web_search:" + " | ".join(batch)})
            print(f"DISCOVERY call={calls}/{MAX_DISCOVERY_CALLS} text_chars={len(text)} source_urls={len(raw_urls)} youtube_urls={len(yt_urls)} candidates_total={len(found)}", flush=True)
        except Exception as ex:
            calls += 1
            append_jsonl(ERROR_PATH, {"stage": "web_discovery_v3", "queries": batch, "error": str(ex)[:1200], "at": now()})
            print(f"DISCOVERY call={calls} ERROR {str(ex)[:240]}", flush=True)
        time.sleep(0.2)
    return list(found.values()), calls


def transcript_rows(video_id: str):
    if YouTubeTranscriptApi is None:
        return [], "library_unavailable"
    try:
        api = YouTubeTranscriptApi()
        fetched = api.fetch(video_id, languages=["ko", "en", "ko-KR", "en-US"])
        rows = [{"text": getattr(x, "text", ""), "start": float(getattr(x, "start", 0)), "duration": float(getattr(x, "duration", 0))} for x in fetched]
        return rows, None
    except Exception as ex:
        return [], str(ex)


def looks_ip_blocked(msg: str):
    s = (msg or "").lower()
    return any(x in s for x in ["ipblocked", "requestblocked", "too many requests", "sign in to confirm", "not a bot", "429"])


def chunks(rows, seconds=300):
    out, cur, start = [], [], None
    for r in rows:
        if start is None:
            start = r["start"]
        if r["start"] - start >= seconds and cur:
            out.append(cur)
            cur, start = [], r["start"]
        cur.append(r)
    if cur:
        out.append(cur)
    return out


def extract_json_array(text: str):
    if not text:
        return []
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.I | re.S).strip()
    try:
        x = json.loads(text)
        return x if isinstance(x, list) else []
    except Exception:
        m = re.search(r"\[.*\]", text, re.S)
        if not m:
            return []
        try:
            x = json.loads(m.group(0))
            return x if isinstance(x, list) else []
        except Exception:
            return []


EXTRACT_INSTRUCTIONS = """You are a strict research assistant building an IU (아이유/이지은) public-statement corpus. From the transcript chunk, extract only statements that are sufficiently likely to be spoken by IU herself. Exclude guests/MC/narration, song lyrics, ads, and uncertain speakers. Do not diagnose or speculate about private psychology. Keep short_quote under 20 words; use Korean paraphrases for meaning. Prioritize self-acceptance, self-criticism, people, relationships, boundaries, trust, love, work, success/failure, criticism, anxiety, emptiness, slump, loss, rest, ambition, perfectionism, control, uncertainty, creativity, growth, diary, memory, recovery. Return JSON array only. Fields: context, short_quote, paraphrase, principles(array), topics(array), speaker_confidence(0~1), timestamp_start, timestamp_end."""


def extract_observations(client, meta, rows):
    text = "\n".join(f"[{r['start']:.1f}] {re.sub(r'\\s+', ' ', r['text']).strip()}" for r in rows if r.get("text"))
    if len(text) < 80:
        return []
    try:
        resp = client.responses.create(
            model=MODEL,
            instructions=EXTRACT_INSTRUCTIONS,
            input=f"SOURCE TITLE: {meta['title']}\nCHANNEL: {meta['channel']}\nTRANSCRIPT:\n{text[:24000]}",
            max_output_tokens=3200,
        )
        return extract_json_array(getattr(resp, "output_text", "") or "")
    except Exception as ex:
        append_jsonl(ERROR_PATH, {"stage": "openai_extract_v3", "source_id": meta["source_id"], "error": str(ex)[:1000], "at": now()})
        return []


def write_summary(**kwargs):
    SUMMARY_PATH.write_text(json.dumps({"version": 3, "at": now(), **kwargs}, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    if not OPENAI_API_KEY:
        raise SystemExit("OPENAI_API_KEY is required")
    client = OpenAI(api_key=OPENAI_API_KEY)
    existing_list = load_jsonl(SOURCES_PATH)
    existing_sources = {x.get("source_id"): x for x in existing_list if x.get("source_id")}
    known_obs = {x.get("id") for x in load_jsonl(OBS_PATH) if x.get("id")}

    candidates, discovery_calls = discover_with_web(client)
    print(f"PHASE discovery_done candidates={len(candidates)}", flush=True)
    validated = []
    new_sources = 0
    seen = set()
    for c in candidates:
        if len(validated) >= MAX_VIDEOS:
            break
        vid = video_id_from_url(c.get("url", ""))
        if not vid or vid in seen:
            continue
        seen.add(vid)
        sid = f"yt_{vid}"
        if sid in existing_sources:
            validated.append(existing_sources[sid])
            continue
        info = oembed(c["url"])
        if not info or not relevant(info.get("title"), info.get("channel")):
            continue
        meta = {"source_id": sid, "platform": "youtube", "video_id": vid, "url": c["url"], "title": info.get("title", ""), "channel": info.get("channel", ""), "published_at": None, "evidence_tier": tier_for(info.get("channel", "")), "discovered_by": c.get("discovered_by", "web_search"), "discovered_at": now(), "metadata_method": "youtube_oembed"}
        append_jsonl(SOURCES_PATH, meta)
        existing_sources[sid] = meta
        validated.append(meta)
        new_sources += 1
        print(f"VALIDATED {len(validated)} new={new_sources} {meta['channel']} | {meta['title'][:80]}", flush=True)

    for meta in existing_sources.values():
        if len(validated) >= MAX_VIDEOS:
            break
        if meta.get("platform") == "youtube" and meta.get("source_id") not in {x.get("source_id") for x in validated}:
            validated.append(meta)

    print(f"PHASE validation_done validated={len(validated)} new_sources={new_sources}", flush=True)
    ai_calls = transcript_ok = transcript_fail = observations_added = 0
    blocked_streak = 0
    transcript_blocked = False

    for idx, meta in enumerate(validated, 1):
        if ai_calls >= MAX_AI_CALLS or transcript_blocked:
            break
        rows, err = transcript_rows(meta.get("video_id", ""))
        if not rows:
            transcript_fail += 1
            append_jsonl(ERROR_PATH, {"stage": "transcript_v3", "video_id": meta.get("video_id"), "error": (err or "unknown")[:800], "at": now()})
            if looks_ip_blocked(err or ""):
                blocked_streak += 1
                if blocked_streak >= 3:
                    transcript_blocked = True
                    print("TRANSCRIPT GitHub runner blocked; stopping transcript phase after 3 consecutive blocks", flush=True)
            else:
                blocked_streak = 0
            print(f"TRANSCRIPT {idx}/{len(validated)} fail ok={transcript_ok} fail={transcript_fail}", flush=True)
            continue
        blocked_streak = 0
        transcript_ok += 1
        print(f"TRANSCRIPT {idx}/{len(validated)} OK rows={len(rows)} ok_total={transcript_ok}", flush=True)
        for chunk in chunks(rows):
            if ai_calls >= MAX_AI_CALLS:
                break
            ai_calls += 1
            obs = extract_observations(client, meta, chunk)
            for o in obs:
                try:
                    ts = float(o.get("timestamp_start") or chunk[0]["start"])
                except Exception:
                    ts = float(chunk[0]["start"])
                oid = f"{meta['source_id']}_{int(ts*10)}"
                if oid in known_obs:
                    continue
                item = {"id": oid, "source_id": meta["source_id"], "published_at": meta.get("published_at"), "source_url": meta.get("url"), "source_title": meta.get("title"), "channel": meta.get("channel"), "evidence_tier": meta.get("evidence_tier", "C"), "timestamp_start": o.get("timestamp_start"), "timestamp_end": o.get("timestamp_end"), "context": o.get("context", ""), "short_quote": o.get("short_quote", ""), "paraphrase": o.get("paraphrase", ""), "principles": o.get("principles", []), "topics": o.get("topics", []), "speaker_confidence": o.get("speaker_confidence", 0), "extracted_at": now(), "extractor_model": MODEL, "transcript_method": "youtube_transcript_api"}
                append_jsonl(OBS_PATH, item)
                known_obs.add(oid)
                observations_added += 1
        print(f"OBS observations_added={observations_added} ai_calls={ai_calls}", flush=True)

    write_summary(discovery_calls=discovery_calls, candidate_videos=len(candidates), validated_videos=len(validated), new_sources=new_sources, transcript_ok=transcript_ok, transcript_fail=transcript_fail, transcript_blocked=transcript_blocked, ai_extract_calls=ai_calls, observations_added=observations_added, total_sources=len(load_jsonl(SOURCES_PATH)), total_observations=len(load_jsonl(OBS_PATH)))
    print("SUMMARY", SUMMARY_PATH.read_text(encoding="utf-8"), flush=True)


if __name__ == "__main__":
    main()
