import hashlib
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path

from openai import OpenAI

ROOT = Path(__file__).resolve().parent
OBS_PATH = ROOT / "observations.jsonl"
SOURCES_PATH = ROOT / "source_registry.jsonl"
ERROR_PATH = ROOT / "errors.jsonl"
SUMMARY_PATH = ROOT / "web_run_summary.json"
COST_PATH = ROOT / "cost_ledger.json"

MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
TARGET = int(os.getenv("TARGET_OBSERVATIONS", "5000"))
MAX_REQUESTS = int(os.getenv("MAX_REQUESTS", "60"))
BUDGET_USD = float(os.getenv("TOTAL_BUDGET_USD", "3.50"))
OBS_PER_REQUEST = int(os.getenv("OBS_PER_REQUEST", "120"))

INPUT_RATE = 0.20 / 1_000_000
OUTPUT_RATE = 1.20 / 1_000_000
WEB_RUN_RATE = 10.0 / 1000

TOPIC_BATCHES = [
    "2008 2009 2010 2011 데뷔 초기, 자신감, 연습, 행복, 인기, 가족, 학교, 실패, 사람",
    "2012 2013 2014 명성, 과대평가 불안, 성장, 대중 평가, 음악, 연기, 자기객관화",
    "2015 2016 Chat-Shire, 비판, 해석의 자유, 공허함, 우울감, 일기, 자기방어, 인간관계",
    "2017 Palette, 25살, 자기수용, 자기이해, 취향, 자기 데이터를 쌓는다는 말, 관계",
    "2018 수상소감, 슬픔, 상실, 동료, 감정을 충분히 느끼는 시간, 책임감",
    "2019 Persona, Hotel del Luna, 연기, 사람, 일, 창작, 팬, 투어, 콘서트 멘트",
    "2020 자기애와 자존감, 자기기준, 관계를 끊는 방식, 자기비판, 나이듦",
    "2021 LILAC, 성공 실패, 운, 과정의 행복, 사랑을 받는 법, 자기혐오에서 자기수용",
    "2022 Broker, 콘서트, 팬, 과거와 현재, 통제, 불안, 도전, 휴식",
    "2023 30대, 부유, 사랑이 미움을 이긴다, 일기, 슬럼프, 일, 경쟁, 승부욕",
    "2024 The Winning, 승리, 계획, 자기 기준, 후회, 도전, 창작의 진정성, 월드투어",
    "2025 폭싹 속았수다, 성공의 정의, 사람, 관계, 감정, 인생의 보물, 악플",
    "2026 사람 일은 모른다, 자기관대함, 자신감과 두려움, 사랑, 일, 유연함",
    "친구 우정 인간관계 가까워지는 법 먼저 연락하기 오래 관계 유지하기 신뢰",
    "경계 선 넘는 사람 실망 관계 거리두기 용서 신뢰 회복 떠나는 사람 남는 사람",
    "사랑 연애 사랑받기 사랑 주기 편안함 동행 상대를 이해하기 관계의 상호성",
    "악플 비판 논란 대중평가 평판 오해 인격공격 표현의 자유 타인의 해석",
    "성공 실패 운 노력 협업 결과 집착 과정 만족 성취 경쟁 야망 완벽주의",
    "불안 두려움 공허함 슬럼프 외로움 분노 슬픔 상실 회복 감정 다루기",
    "일기 기록 기억 과거의 나 현재의 나 자기관찰 메타인지 자기수용 자기애",
    "일 직업 가수 배우 창작 작사 작곡 연기 일중심 삶 휴식 번아웃 의미",
    "팬 유애나 팬에게 한 말 콘서트 엔딩 멘트 팬미팅 메시지 감사 사랑 책임",
    "아이유의 팔레트에서 IU 본인이 한 인생관 사람관 관계관 자기관찰 발언",
    "IU TV 공식 비하인드에서 IU 본인이 한 일상 생각 사람 관계 일 창작 발언",
    "유퀴즈 뉴스룸 살롱드립 핑계고 라디오 장문 토크에서 아이유 직접 발언",
    "골든디스크 멜론뮤직어워드 MAMA 백상 등 수상소감에서 아이유 직접 발언",
    "GQ W Vogue ELLE Harper's Bazaar Marie Claire Billboard TIME Korea Times IU 인터뷰",
    "영어권 해외 인터뷰 IU Lee Ji-eun self love relationships success failure anxiety fame",
    "콘서트 멘트 밤편지 아이와 나의 바다 Palette Love wins all 관련 본인 설명과 가치관",
    "배우 이지은 나의 아저씨 호텔델루나 브로커 드림 폭싹속았수다 관련 인터뷰의 사람관"
]

SCHEMA = {
    "type": "object",
    "properties": {
        "observations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "source_url": {"type": "string"},
                    "source_title": {"type": "string"},
                    "publisher": {"type": "string"},
                    "published_at": {"type": ["string", "null"]},
                    "source_kind": {"type": "string", "enum": ["video", "interview", "speech", "article", "press_conference", "radio", "other"]},
                    "context": {"type": "string"},
                    "short_quote": {"type": "string"},
                    "paraphrase": {"type": "string"},
                    "principles": {"type": "array", "items": {"type": "string"}},
                    "topics": {"type": "array", "items": {"type": "string"}},
                    "directness": {"type": "string", "enum": ["direct_video", "direct_interview", "direct_speech", "reported_quote", "paraphrase_only"]},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1}
                },
                "required": ["source_url", "source_title", "publisher", "published_at", "source_kind", "context", "short_quote", "paraphrase", "principles", "topics", "directness", "confidence"],
                "additionalProperties": False
            }
        }
    },
    "required": ["observations"],
    "additionalProperties": False
}

INSTRUCTIONS = """당신은 IU Brain Corpus 연구 보조자다. 웹검색으로 공개된 자료를 직접 확인하고 아이유(IU/이지은)의 공개 발언에서 사고방식 관찰치를 추출한다.
엄격한 규칙:
1) 아이유 본인이 말한 내용이 확인되는 자료를 최우선으로 한다. 공식 YouTube/방송/잡지 장문 인터뷰/기자간담회/수상소감/공식 비하인드를 우선한다.
2) 실제 발언이 아닌 기자의 추측, 팬의 해석, 가사만으로 심리를 추정한 것은 제외한다.
3) short_quote는 원문을 확인할 수 있을 때만 쓰고 최대 20단어. 확신이 없으면 빈 문자열.
4) paraphrase는 원문을 베끼지 말고 한국어로 상세 요약한다.
5) source_url은 이번 웹검색에서 실제 확인한 URL만 쓴다. 존재하지 않는 URL을 만들지 않는다.
6) 동일한 한 문장을 억지로 여러 관찰치로 쪼개지 않는다. 서로 독립적인 생각일 때만 분리한다.
7) 임상진단·사적 심리 추측 금지. 공개 발언에서 확인되는 가치관/대처법/관계관만 기록한다.
8) 음악 무대나 MV 자체는 제외하되, 영상 안에서 아이유가 직접 설명/멘트를 한 경우는 포함한다.
9) 최대한 다양한 연도와 매체를 사용한다.
10) confidence 0.75 미만이면 제외한다.
"""


def now():
    return datetime.now(timezone.utc).isoformat()


def load_jsonl(path):
    out = []
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            out.append(json.loads(line))
        except Exception:
            pass
    return out


def append_jsonl(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def load_cost():
    if not COST_PATH.exists():
        return {"estimated_usd": 0.0, "input_tokens": 0, "output_tokens": 0, "web_runs": 0, "requests": 0}
    try:
        return json.loads(COST_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"estimated_usd": 0.0, "input_tokens": 0, "output_tokens": 0, "web_runs": 0, "requests": 0}


def save_cost(c):
    c["updated_at"] = now()
    COST_PATH.write_text(json.dumps(c, ensure_ascii=False, indent=2), encoding="utf-8")


def normalized_hash(o):
    key = "|".join([
        re.sub(r"\s+", " ", str(o.get("source_url", "")).strip().lower()),
        re.sub(r"\s+", " ", str(o.get("paraphrase", "")).strip().lower())[:500]
    ])
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:24]


def response_dump(resp):
    try:
        return resp.model_dump(mode="json")
    except Exception:
        try:
            return json.loads(resp.model_dump_json())
        except Exception:
            return {}


def count_web_runs(node):
    n = 0
    if isinstance(node, dict):
        if node.get("type") == "web_search_call":
            n += 1
        for v in node.values():
            n += count_web_runs(v)
    elif isinstance(node, list):
        for v in node:
            n += count_web_runs(v)
    return n


def collect_source_urls(node, out=None):
    if out is None:
        out = set()
    if isinstance(node, dict):
        u = node.get("url")
        if isinstance(u, str) and u.startswith("http"):
            out.add(u.rstrip("/"))
        for v in node.values():
            collect_source_urls(v, out)
    elif isinstance(node, list):
        for v in node:
            collect_source_urls(v, out)
    return out


def usage_cost(resp):
    usage = getattr(resp, "usage", None)
    it = int(getattr(usage, "input_tokens", 0) or 0)
    ot = int(getattr(usage, "output_tokens", 0) or 0)
    dump = response_dump(resp)
    wr = count_web_runs(dump)
    return it, ot, wr, it * INPUT_RATE + ot * OUTPUT_RATE + wr * WEB_RUN_RATE


def tier_for(o):
    d = o.get("directness")
    u = o.get("source_url", "").lower()
    p = o.get("publisher", "").lower()
    official_video = "youtube.com" in u and any(x in p for x in ["iu official", "이지금", "1thek", "jtbc", "kbs", "sbs", "mbc", "tvn", "billboard", "vogue", "elle", "gq", "bazaar", "netflix", "teo"])
    if d == "direct_video" and official_video:
        return "A++"
    if d in ["direct_interview", "direct_speech", "direct_video"]:
        return "A+"
    if d == "reported_quote":
        return "B"
    return "C"


def build_prompt(topic, current_count, request_no):
    return f"""이번 배치 주제: {topic}
현재 코퍼스에는 약 {current_count}개의 관찰치가 있다. 이번 요청은 배치 #{request_no}다.
웹을 폭넓게 검색해서 이전에 흔히 반복된 대표 명언 몇 개만 되풀이하지 말고, 서로 다른 인터뷰/영상/수상소감에서 최대 {OBS_PER_REQUEST}개의 독립적인 관찰치를 찾아라.
특히 아이유 본인이 직접 말하는 영상 자료와 원문 인터뷰를 우선한다. 각 관찰치는 하나의 구체적인 생각 또는 대처 원칙이어야 한다.
가능하면 2008~2026의 연도 범위를 넓게 커버하고, 한국어/영어권 자료를 모두 활용하라."""


def main():
    if not OPENAI_API_KEY:
        raise SystemExit("OPENAI_API_KEY required")

    existing = load_jsonl(OBS_PATH)
    seen = {x.get("content_hash") or normalized_hash(x) for x in existing}
    cost = load_cost()
    client = OpenAI(api_key=OPENAI_API_KEY)
    added = 0
    requests_done = 0

    print(f"START observations={len(existing)} estimated_cost=${cost.get('estimated_usd', 0):.4f} budget=${BUDGET_USD:.2f}", flush=True)

    if len(existing) >= TARGET:
        print("TARGET already reached", flush=True)
        return
    if float(cost.get("estimated_usd", 0)) >= BUDGET_USD:
        print("BUDGET already reached", flush=True)
        return

    for i in range(MAX_REQUESTS):
        total_now = len(existing) + added
        if total_now >= TARGET:
            break
        if float(cost.get("estimated_usd", 0)) >= BUDGET_USD:
            break

        topic = TOPIC_BATCHES[i % len(TOPIC_BATCHES)]
        try:
            resp = client.responses.create(
                model=MODEL,
                reasoning={"effort": "none"},
                tools=[{"type": "web_search_preview", "search_context_size": "low"}],
                include=["web_search_call.action.sources"],
                instructions=INSTRUCTIONS,
                input=build_prompt(topic, total_now, i + 1),
                text={"format": {"type": "json_schema", "name": "iu_observations", "schema": SCHEMA, "strict": True}},
                max_output_tokens=16000,
                store=False,
            )
            requests_done += 1
            it, ot, wr, c = usage_cost(resp)
            cost["input_tokens"] = int(cost.get("input_tokens", 0)) + it
            cost["output_tokens"] = int(cost.get("output_tokens", 0)) + ot
            cost["web_runs"] = int(cost.get("web_runs", 0)) + wr
            cost["requests"] = int(cost.get("requests", 0)) + 1
            cost["estimated_usd"] = float(cost.get("estimated_usd", 0)) + c
            save_cost(cost)

            source_urls = collect_source_urls(response_dump(resp))
            source_urls_norm = {u.rstrip("/") for u in source_urls}

            try:
                payload = json.loads(resp.output_text or "{}")
            except Exception:
                payload = {}
            rows = payload.get("observations", []) if isinstance(payload, dict) else []

            kept = 0
            for o in rows:
                if not isinstance(o, dict):
                    continue
                if float(o.get("confidence", 0) or 0) < 0.75:
                    continue
                url = str(o.get("source_url", "")).rstrip("/")
                if not url or (source_urls_norm and url not in source_urls_norm):
                    continue
                h = normalized_hash(o)
                if h in seen:
                    continue
                item = {
                    "id": f"web_{h}",
                    "content_hash": h,
                    "source_id": "web_" + hashlib.sha1(url.encode("utf-8")).hexdigest()[:16],
                    "published_at": o.get("published_at"),
                    "source_url": url,
                    "source_title": o.get("source_title", ""),
                    "channel": o.get("publisher", ""),
                    "source_kind": o.get("source_kind", "other"),
                    "evidence_tier": tier_for(o),
                    "timestamp_start": None,
                    "timestamp_end": None,
                    "context": o.get("context", ""),
                    "short_quote": o.get("short_quote", ""),
                    "paraphrase": o.get("paraphrase", ""),
                    "principles": o.get("principles", []),
                    "topics": o.get("topics", []),
                    "speaker_confidence": o.get("confidence", 0),
                    "directness": o.get("directness"),
                    "extracted_at": now(),
                    "extractor_model": MODEL,
                    "extraction_method": "openai_web_search_structured",
                }
                append_jsonl(OBS_PATH, item)
                seen.add(h)
                kept += 1
                added += 1
                if len(existing) + added >= TARGET:
                    break

            print(
                f"BATCH {i+1}/{MAX_REQUESTS} topic={topic[:30]} raw={len(rows)} kept={kept} total={len(existing)+added} "
                f"tokens={it}/{ot} web_runs={wr} batch_cost=${c:.4f} cumulative=${cost['estimated_usd']:.4f}",
                flush=True,
            )

        except Exception as ex:
            append_jsonl(ERROR_PATH, {"stage": "web_v4", "request": i + 1, "topic": topic, "error": str(ex)[:1500], "at": now()})
            print(f"ERROR batch={i+1}: {str(ex)[:300]}", flush=True)

        time.sleep(0.2)

    final_total = len(load_jsonl(OBS_PATH))
    summary = {
        "version": 4,
        "mode": "web_only_budget",
        "at": now(),
        "target": TARGET,
        "total_observations": final_total,
        "observations_added_this_run": added,
        "requests_this_run": requests_done,
        "budget_usd": BUDGET_USD,
        "estimated_cumulative_usd": round(float(cost.get("estimated_usd", 0)), 6),
        "input_tokens": cost.get("input_tokens", 0),
        "output_tokens": cost.get("output_tokens", 0),
        "web_runs": cost.get("web_runs", 0),
        "budget_stopped": float(cost.get("estimated_usd", 0)) >= BUDGET_USD,
        "target_reached": final_total >= TARGET,
    }
    SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print("SUMMARY " + json.dumps(summary, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
