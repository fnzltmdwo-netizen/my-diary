import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse, parse_qs

import yt_dlp
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

MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6-sol")
MAX_VIDEOS = int(os.getenv("MAX_VIDEOS", "250"))
SEARCH_PER_QUERY = int(os.getenv("SEARCH_PER_QUERY", "40"))
MAX_AI_CALLS = int(os.getenv("MAX_AI_CALLS", "400"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()

PREFERRED = {x.lower() for x in DISCOVERY.get("preferred_channels", [])}
KEYWORDS = ["아이유", " iu ", "iu(", "iu ", "이지금", "lee jieun", "lee ji-eun"]


def now():
    return datetime.now(timezone.utc).isoformat()


def append_jsonl(path: Path, obj: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def load_ids(path: Path, key: str):
    ids = set()
    if not path.exists():
        return ids
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                obj = json.loads(line)
                if obj.get(key):
                    ids.add(str(obj[key]))
            except Exception:
                pass
    return ids


def video_id_from_url(url: str):
    if "youtu.be/" in url:
        return url.split("youtu.be/", 1)[1].split("?", 1)[0]
    q = parse_qs(urlparse(url).query)
    return q.get("v", [None])[0]


def ydl_opts(flat=False):
    return {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "extract_flat": "in_playlist" if flat else False,
        "ignoreerrors": True,
        "socket_timeout": 20,
    }


def compact_meta(info: dict, discovered_by: str):
    if not info:
        return None
    vid = info.get("id") or video_id_from_url(info.get("webpage_url", ""))
    if not vid:
        return None
    url = info.get("webpage_url") or f"https://www.youtube.com/watch?v={vid}"
    title = info.get("title") or ""
    channel = info.get("channel") or info.get("uploader") or ""
    upload_date = info.get("upload_date")
    published_at = None
    if upload_date and len(str(upload_date)) == 8:
        published_at = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:8]}"
    return {
        "source_id": f"yt_{vid}",
        "platform": "youtube",
        "video_id": vid,
        "url": url,
        "title": title,
        "channel": channel,
        "channel_id": info.get("channel_id") or info.get("uploader_id"),
        "published_at": published_at,
        "duration": info.get("duration"),
        "description": (info.get("description") or "")[:1200],
        "discovered_by": discovered_by,
        "discovered_at": now(),
        "evidence_tier": tier_for(channel, title, url),
    }


def tier_for(channel: str, title: str, url: str):
    c = (channel or "").lower()
    if "iu official" in c or "이지금" in c or "1thek" in c:
        return "A++"
    if any(p in c for p in ["tvn", "jtbc", "kbs", "sbs", "mbc", "mnet", "billboard", "vogue", "elle", "gq", "bazaar", "marie claire", "netflix", "teo"]):
        return "A++"
    return "C"


def relevant(meta: dict):
    text = f" {meta.get('title','')} {meta.get('channel','')} ".lower()
    if meta.get("channel", "").lower() in PREFERRED:
        return True
    return any(k in text for k in KEYWORDS)


def discover():
    found = {}
    with yt_dlp.YoutubeDL(ydl_opts(flat=True)) as ydl:
        for ch in DISCOVERY.get("channels", []):
            try:
                info = ydl.extract_info(ch["url"], download=False)
                for e in (info or {}).get("entries") or []:
                    if not e:
                        continue
                    vid = e.get("id")
                    if vid:
                        found[vid] = {"url": f"https://www.youtube.com/watch?v={vid}", "discovered_by": ch.get("label", "channel")}
            except Exception as ex:
                append_jsonl(ERROR_PATH, {"stage": "channel_discovery", "url": ch["url"], "error": str(ex), "at": now()})

        for url in DISCOVERY.get("seed_videos", []):
            vid = video_id_from_url(url)
            if vid:
                found[vid] = {"url": url, "discovered_by": "seed"}

        for q in DISCOVERY.get("youtube_search_queries", []):
            try:
                info = ydl.extract_info(f"ytsearch{SEARCH_PER_QUERY}:{q}", download=False)
                for e in (info or {}).get("entries") or []:
                    if not e:
                        continue
                    vid = e.get("id")
                    if vid and vid not in found:
                        found[vid] = {"url": f"https://www.youtube.com/watch?v={vid}", "discovered_by": f"search:{q}"}
            except Exception as ex:
                append_jsonl(ERROR_PATH, {"stage": "search_discovery", "query": q, "error": str(ex), "at": now()})
    return list(found.values())


def enrich(candidate):
    try:
        with yt_dlp.YoutubeDL(ydl_opts(flat=False)) as ydl:
            info = ydl.extract_info(candidate["url"], download=False)
        meta = compact_meta(info, candidate["discovered_by"])
        if meta and relevant(meta):
            return meta
    except Exception as ex:
        append_jsonl(ERROR_PATH, {"stage": "metadata", "url": candidate["url"], "error": str(ex), "at": now()})
    return None


def get_transcript(video_id: str):
    if YouTubeTranscriptApi is None:
        return []
    languages = ["ko", "en", "ko-KR", "en-US"]
    try:
        api = YouTubeTranscriptApi()
        fetched = api.fetch(video_id, languages=languages)
        rows = []
        for x in fetched:
            rows.append({"text": getattr(x, "text", ""), "start": float(getattr(x, "start", 0)), "duration": float(getattr(x, "duration", 0))})
        return rows
    except Exception:
        try:
            rows = YouTubeTranscriptApi.get_transcript(video_id, languages=languages)
            return [{"text": x.get("text", ""), "start": float(x.get("start", 0)), "duration": float(x.get("duration", 0))} for x in rows]
        except Exception as ex:
            append_jsonl(ERROR_PATH, {"stage": "transcript", "video_id": video_id, "error": str(ex), "at": now()})
            return []


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
주어진 자막 조각에서 '아이유(IU/이지은)가 직접 말한 것으로 충분히 판단되는 발언'만 추출한다.
게스트/MC/나레이션의 발언은 버린다. 누가 말했는지 불확실하면 버린다.
노래 가사, 공연 중 노래, 광고 문구는 버린다.
임상진단·성격추측을 하지 않는다.
각 관찰치는 독립적으로 의미가 있어야 한다.
원문을 길게 복제하지 말고 short_quote는 최대 20단어만, 나머지는 상세한 한국어 요약으로 쓴다.
특히 자기애, 자기수용, 사람, 관계, 경계, 신뢰, 사랑, 일, 성공/실패, 비판, 불안, 공허함, 슬럼프, 상실, 휴식, 야망, 완벽주의, 통제, 불확실성, 창작, 성장, 일기, 기억, 회복과 관련된 사고를 우선한다.
출력은 JSON 배열만 반환한다.
각 객체 필드: context, short_quote, paraphrase, principles(array), topics(array), speaker_confidence(0~1), timestamp_start, timestamp_end.
"""


def extract_observations(client, meta, rows):
    text = "\n".join(f"[{r['start']:.1f}] {re.sub(r'\\s+', ' ', r['text']).strip()}" for r in rows if r.get("text"))
    if len(text) < 80:
        return []
    prompt = f"SOURCE TITLE: {meta['title']}\nCHANNEL: {meta['channel']}\nEVIDENCE: {meta['evidence_tier']}\nTRANSCRIPT CHUNK:\n{text[:24000]}"
    try:
        resp = client.responses.create(model=MODEL, instructions=EXTRACT_INSTRUCTIONS, input=prompt, max_output_tokens=3500)
        raw = resp.output_text.strip()
        raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.I|re.S).strip()
        data = json.loads(raw)
        return data if isinstance(data, list) else []
    except Exception as ex:
        append_jsonl(ERROR_PATH, {"stage": "openai_extract", "source_id": meta["source_id"], "error": str(ex), "at": now()})
        return []


def main():
    known_sources = load_ids(SOURCES_PATH, "source_id")
    known_obs = load_ids(OBS_PATH, "id")
    candidates = discover()
    print(f"discovered candidates: {len(candidates)}")

    metas = []
    for c in candidates:
        if len(metas) >= MAX_VIDEOS:
            break
        vid = video_id_from_url(c["url"])
        sid = f"yt_{vid}" if vid else None
        if sid in known_sources:
            continue
        meta = enrich(c)
        if meta:
            append_jsonl(SOURCES_PATH, meta)
            known_sources.add(meta["source_id"])
            metas.append(meta)
            print("source", meta["source_id"], meta["title"][:70])
        time.sleep(0.05)

    if not OPENAI_API_KEY:
        print("OPENAI_API_KEY not set: metadata collection only")
        return

    client = OpenAI(api_key=OPENAI_API_KEY)
    calls = 0
    for meta in metas:
        rows = get_transcript(meta["video_id"])
        if not rows:
            continue
        for chunk in chunks(rows):
            if calls >= MAX_AI_CALLS:
                print("MAX_AI_CALLS reached")
                return
            calls += 1
            obs = extract_observations(client, meta, chunk)
            for o in obs:
                ts = float(o.get("timestamp_start") or chunk[0]["start"])
                oid = f"{meta['source_id']}_{int(ts*10)}"
                if oid in known_obs:
                    continue
                item = {
                    "id": oid,
                    "source_id": meta["source_id"],
                    "published_at": meta.get("published_at"),
                    "source_url": meta["url"],
                    "source_title": meta["title"],
                    "channel": meta["channel"],
                    "evidence_tier": meta["evidence_tier"],
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
                }
                append_jsonl(OBS_PATH, item)
                known_obs.add(oid)
            time.sleep(0.15)


if __name__ == "__main__":
    main()
