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

MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6-sol")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
MAX_VIDEOS = int(os.getenv("MAX_VIDEOS", "250"))
MAX_AI_CALLS = int(os.getenv("MAX_AI_CALLS", "400"))
MAX_DISCOVERY_CALLS = int(os.getenv("MAX_DISCOVERY_CALLS", "18"))
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
    rows = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                rows.append(json.loads(line))
            except Exception:
                pass
    return rows


def video_id_from_url(url: str):
    if not url:
        return None
    if "youtu.be/" in url:
        return url.split("youtu.be/", 1)[1].split("?", 1)[0].split("/", 1)[0]
    p = urlparse(url)
    if p.netloc.endswith("youtube.com"):
        if p.path == "/watch":
            return parse_qs(p.query).get("v", [None])[0]
        if p.path.startswith("/shorts/"):
            return p.path.split("/shorts/", 1)[1].split("/", 1)[0]
    return None


def clean_youtube_url(url: str):
    vid = video_id_from_url(url)
    return f"https://www.youtube.com/watch?v={vid}" if vid else None


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
    if c in PREFERRED:
        return True
    return any(k in text for k in KEYWORDS)


def extract_json_array(text: str):
    if not text:
        return []
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.I | re.S).strip()
    try:
        value = json.loads(text)
        return value if isinstance(value, list) else []
    except Exception:
        pass
    m = re.search(r"\[.*\]", text, re.S)
    if not m:
        return []
    try:
        value = json.loads(m.group(0))
        return value if isinstance(value, list) else []
    except Exception:
        return []


def oembed(url: str):
    endpoint = "https://www.youtube.com/oembed?format=json&url=" + quote(url, safe="")
    req = Request(endpoint, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urlopen(req, timeout=15) as r:
            data = json.loads(r.read().decode("utf-8"))
        return {
            "title": data.get("title", ""),
            "channel": data.get("author_name", ""),
        }
    except Exception as ex:
        append_jsonl(ERROR_PATH, {"stage": "oembed", "url": url, "error": str(ex)[:500], "at": now()})
        return None


def discover_with_web(client):
    found = {}
    for url in DISCOVERY.get("seed_videos", []):
        clean = clean_youtube_url(url)
        if clean:
            found[video_id_from_url(clean)] = {"url": clean, "discovered_by": "seed"}

    queries = DISCOVERY.get("youtube_search_queries", [])
    calls = 0
    for i in range(0, len(queries), SEARCH_BATCH_SIZE):
        if calls >= MAX_DISCOVERY_CALLS or len(found) >= MAX_VIDEOS * 3:
            break
        batch = queries[i:i + SEARCH_BATCH_SIZE]
        prompt = (
            "웹에서 아이유(IU/이지은)가 직접 말하는 인터뷰, 토크, 공식 비하인드, 콘서트 멘트, 수상소감 YouTube 영상을 찾아라. "
            "가능하면 이지금 [IU Official], 1theK, tvN, JTBC, KBS, SBS, MBC, Mnet, Billboard, Vogue, ELLE, GQ, Bazaar, Marie Claire, Netflix Korea, TEO 같은 공식/언론 채널을 우선한다. "
            "음악 무대/뮤직비디오만 있는 영상은 제외한다. 검색 주제는 다음과 같다: " + ", ".join(batch) + "\n"
            "반드시 실제 검색결과에서 확인한 YouTube watch URL만 사용하라. 출력은 JSON 배열만: "
            "[{\"url\":\"https://www.youtube.com/watch?v=...\",\"why\":\"짧은 이유\"}] 최대 30개."
        )
        try:
            resp = client.responses.create(
                model=MODEL,
                tools=[{"type": "web_search_preview"}],
                input=prompt,
                max_output_tokens=2200,
            )
            items = extract_json_array(resp.output_text)
            calls += 1
            for item in items:
                clean = clean_youtube_url((item or {}).get("url", ""))
                vid = video_id_from_url(clean or "")
                if clean and vid:
                    found.setdefault(vid, {"url": clean, "discovered_by": "web_search:" + " | ".join(batch)})
            print(f"web discovery {calls}/{MAX_DISCOVERY_CALLS}: candidates={len(found)}")
        except Exception as ex:
            calls += 1
            append_jsonl(ERROR_PATH, {"stage": "web_discovery", "queries": batch, "error": str(ex)[:800], "at": now()})
        time.sleep(0.25)
    return list(found.values()), calls


def transcript_rows(video_id: str):
    if YouTubeTranscriptApi is None:
        return [], "library_unavailable"
    languages = ["ko", "en", "ko-KR", "en-US"]
    try:
        api = YouTubeTranscriptApi()
        fetched = api.fetch(video_id, languages=languages)
        rows = [{
            "text": getattr(x, "text", ""),
            "start": float(getattr(x, "start", 0)),
            "duration": float(getattr(x, "duration", 0)),
        } for x in fetched]
        return rows, None
    except Exception as ex:
        msg = str(ex)
        return [], msg


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


EXTRACT_INSTRUCTIONS = """당신은 IU Brain Corpus의 엄격한 연구 보조자다.
주어진 자막에서 아이유(IU/이지은)가 직접 말한 것으로 충분히 판단되는 발언만 추출한다.
게스트/MC/나레이션, 노래 가사, 광고 문구는 버린다. 화자를 확신할 수 없으면 버린다.
임상 진단이나 사적 심리를 추측하지 않는다.
short_quote는 최대 20단어, 나머지는 한국어 상세 요약으로 쓴다.
자기애, 자기수용, 사람, 관계, 경계, 신뢰, 사랑, 일, 성공/실패, 비판, 불안, 공허함, 슬럼프, 상실, 휴식, 야망, 완벽주의, 통제, 불확실성, 창작, 성장, 일기, 기억, 회복을 우선한다.
JSON 배열만 출력한다. 각 객체 필드: context, short_quote, paraphrase, principles(array), topics(array), speaker_confidence(0~1), timestamp_start, timestamp_end.
"""


def extract_observations(client, meta, rows):
    text = "\n".join(f"[{r['start']:.1f}] {re.sub(r'\\s+', ' ', r['text']).strip()}" for r in rows if r.get("text"))
    if len(text) < 80:
        return []
    prompt = f"SOURCE TITLE: {meta['title']}\nCHANNEL: {meta['channel']}\nTRANSCRIPT CHUNK:\n{text[:24000]}"
    try:
        resp = client.responses.create(
            model=MODEL,
            instructions=EXTRACT_INSTRUCTIONS,
            input=prompt,
            max_output_tokens=3500,
        )
        return extract_json_array(resp.output_text)
    except Exception as ex:
        append_jsonl(ERROR_PATH, {"stage": "openai_extract", "source_id": meta["source_id"], "error": str(ex)[:800], "at": now()})
        return []


def main():
    if not OPENAI_API_KEY:
        raise SystemExit("OPENAI_API_KEY is required for v2 web-first discovery")

    client = OpenAI(api_key=OPENAI_API_KEY)
    existing_sources = {x.get("source_id"): x for x in load_jsonl(SOURCES_PATH) if x.get("source_id")}
    existing_obs = load_jsonl(OBS_PATH)
    known_obs = {x.get("id") for x in existing_obs if x.get("id")}

    candidates, discovery_calls = discover_with_web(client)
    new_sources = 0
    validated = []

    for c in candidates:
        if len(validated) >= MAX_VIDEOS:
            break
        vid = video_id_from_url(c["url"])
        sid = f"yt_{vid}" if vid else None
        if not sid:
            continue
        if sid in existing_sources:
            validated.append(existing_sources[sid])
            continue
        info = oembed(c["url"])
        if not info or not relevant(info.get("title"), info.get("channel")):
            continue
        meta = {
            "source_id": sid,
            "platform": "youtube",
            "video_id": vid,
            "url": c["url"],
            "title": info.get("title", ""),
            "channel": info.get("channel", ""),
            "published_at": None,
            "evidence_tier": tier_for(info.get("channel", "")),
            "discovered_by": c.get("discovered_by", "web_search"),
            "discovered_at": now(),
            "metadata_method": "youtube_oembed",
        }
        append_jsonl(SOURCES_PATH, meta)
        existing_sources[sid] = meta
        validated.append(meta)
        new_sources += 1

    # Also retry previously known YouTube sources, even if they were added in an earlier run.
    for meta in existing_sources.values():
        if len(validated) >= MAX_VIDEOS:
            break
        if meta.get("platform") == "youtube" and all(x.get("source_id") != meta.get("source_id") for x in validated):
            validated.append(meta)

    ai_calls = 0
    transcript_ok = 0
    transcript_fail = 0
    transcript_blocked = False
    consecutive_blocked = 0
    observations_added = 0

    for meta in validated:
        if ai_calls >= MAX_AI_CALLS:
            break
        if transcript_blocked:
            break
        rows, err = transcript_rows(meta.get("video_id", ""))
        if not rows:
            transcript_fail += 1
            append_jsonl(ERROR_PATH, {"stage": "transcript", "video_id": meta.get("video_id"), "error": (err or "unknown")[:800], "at": now()})
            if looks_ip_blocked(err or ""):
                consecutive_blocked += 1
                if consecutive_blocked >= 3:
                    transcript_blocked = True
                    print("Transcript requests appear blocked from GitHub runner; stopping transcript stage for this run.")
            else:
                consecutive_blocked = 0
            continue

        transcript_ok += 1
        consecutive_blocked = 0
        for chunk in chunks(rows):
            if ai_calls >= MAX_AI_CALLS:
                break
            ai_calls += 1
            for o in extract_observations(client, meta, chunk):
                try:
                    ts = float(o.get("timestamp_start") or chunk[0]["start"])
                except Exception:
                    ts = float(chunk[0]["start"])
                oid = f"{meta['source_id']}_{int(ts * 10)}"
                if oid in known_obs:
                    continue
                item = {
                    "id": oid,
                    "source_id": meta["source_id"],
                    "published_at": meta.get("published_at"),
                    "source_url": meta.get("url"),
                    "source_title": meta.get("title"),
                    "channel": meta.get("channel"),
                    "evidence_tier": meta.get("evidence_tier", "C"),
                    "timestamp_start": o.get("timestamp_start"),
                    "timestamp_end": o.get("timestamp_end"),
                    "context": o.get("context", ""),
                    "short_quote": o.get("short_quote", ""),
                    "paraphrase": o.get("paraphrase", ""),
                    "principles": o.get("principles", []),
                    "topics": o.get("topics", []),
                    "speaker_confidence": o.get("speaker_confidence", 0),
                    "extracted_at": now(),
                    "extractor_model": MODEL,
                    "transcript_method": "youtube_transcript_api",
                }
                append_jsonl(OBS_PATH, item)
                known_obs.add(oid)
                observations_added += 1
            time.sleep(0.12)

    summary = {
        "finished_at": now(),
        "model": MODEL,
        "discovery_calls": discovery_calls,
        "candidate_count": len(candidates),
        "validated_sources_this_run": len(validated),
        "new_sources_added": new_sources,
        "transcript_successes": transcript_ok,
        "transcript_failures": transcript_fail,
        "transcript_stage_blocked": transcript_blocked,
        "ai_extraction_calls": ai_calls,
        "observations_added": observations_added,
        "note": "Discovery is web-first. YouTube transcript stage stops early if GitHub runner IP appears blocked.",
    }
    SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
