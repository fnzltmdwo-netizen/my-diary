import json
import os
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel
from sqlalchemy import Column, DateTime, Integer, Text
from sqlalchemy.orm import Session

from backend.database import Base, engine, get_db

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
IU_BRAIN_DIR = BASE_DIR / "iu_brain"
APP_PASSWORD = os.getenv("APP_PASSWORD", "").strip()
SERVER_OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()

app = FastAPI(title="나의 바다", version="3.8-iu-brain-retrieval")


class AppState(Base):
    __tablename__ = "app_state"
    id = Column(Integer, primary_key=True, default=1)
    payload = Column(Text, nullable=False, default="{}")
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class StateBody(BaseModel):
    state: dict


class IUAdviceBody(BaseModel):
    message: str
    context: dict | None = None
    model: str = "gpt-5.6-luna"


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)


def verify_password(x_app_password: str | None = Header(default=None)):
    if not APP_PASSWORD:
        raise HTTPException(status_code=503, detail="APP_PASSWORD is not configured")
    if x_app_password != APP_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid app password")


def load_iu_brain() -> list[dict]:
    by_id: dict[str, dict] = {}
    if not IU_BRAIN_DIR.exists():
        return []
    files = sorted(IU_BRAIN_DIR.glob("verified_observations*.jsonl"))
    for path in files:
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except Exception:
            continue
        for line in lines:
            if not line.strip():
                continue
            try:
                row = json.loads(line)
                if row.get("id") and row.get("observation"):
                    row.setdefault("brain_file", path.name)
                    by_id[str(row["id"])] = row
            except Exception:
                continue
    return list(by_id.values())


IU_BRAIN = load_iu_brain()

TOPIC_ALIASES = {
    "경계": ["relationships", "closure", "self-protection", "interpretation", "future", "boundaries", "respect"],
    "거리": ["relationships", "closure", "self-protection", "boundaries"],
    "선": ["boundaries", "relationships", "respect", "closeness"],
    "신뢰": ["relationships", "feedback", "future", "trust"],
    "떠났": ["relationships", "loss", "closure", "future"],
    "버림": ["relationships", "loss", "self-protection", "future"],
    "악마화": ["evaluation", "interpretation", "complexity", "emotion", "rumination"],
    "미워": ["evaluation", "interpretation", "emotion", "love", "self-dislike"],
    "자존감": ["self-esteem", "self-love", "self-image", "evaluation", "self-standard"],
    "자기수용": ["self-acceptance", "self-love", "self-friendship", "imperfection", "contentment"],
    "자기혐오": ["self-dislike", "self-acceptance", "self-love", "self-doubt"],
    "자기비난": ["self-esteem", "self-compassion", "evaluation", "perfectionism", "self-criticism"],
    "사랑": ["love", "receiving", "reciprocity", "relationships", "confidence", "fear", "care"],
    "친구": ["relationships", "people", "feedback", "future", "friendship"],
    "친밀": ["relationships", "closeness", "boundaries", "trust", "respect"],
    "사람": ["relationships", "people", "evaluation", "future", "personhood"],
    "팬": ["fans", "relationships", "gratitude", "reciprocity", "responsibility"],
    "실패": ["failure", "success", "effort", "uncertainty", "self-standard", "fairness"],
    "성공": ["success", "attribution", "collaboration", "self-standard", "career", "luck"],
    "일": ["work", "motivation", "success", "effort", "regulation", "activation"],
    "휴식": ["rest", "self-care", "limits", "sustainability", "recovery"],
    "쉬": ["rest", "self-care", "limits", "recovery"],
    "책임": ["responsibility", "accountability", "fans", "work"],
    "부담": ["burden", "responsibility", "fear", "expectations"],
    "완벽": ["perfection", "perfectionism", "perspective", "flexibility", "self-standard"],
    "불안": ["fear", "uncertainty", "self-protection", "emotion"],
    "두려": ["fear", "uncertainty", "self-protection", "confidence"],
    "외로": ["loneliness", "emotion", "relationships", "success"],
    "공허": ["emotion", "avoidance", "recovery", "work", "emptiness"],
    "감정": ["emotion", "acceptance", "rumination", "recovery"],
    "위로": ["care", "companionship", "emotion", "relationships", "reciprocity"],
    "상실": ["loss", "grief", "continuity", "care", "emotion"],
    "일기": ["journaling", "memory", "emotion", "time", "self-observation"],
    "기록": ["journaling", "memory", "records", "time", "self-observation"],
    "과거": ["past", "letting-go", "growth", "closure", "hindsight"],
    "후회": ["past", "decision", "effort", "closure", "regret"],
    "비교": ["evaluation", "self-standard", "self-image", "comparison"],
    "평가": ["evaluation", "self-standard", "identity"],
    "인정": ["recognition", "self-standard", "success", "evaluation"],
    "행복": ["happiness", "contentment", "meaning", "self-acceptance"],
    "인기": ["fame", "success", "fear", "self-protection", "evaluation"],
    "꿈": ["dreams", "future", "coping", "identity"],
}


def normalized_terms(text: str) -> set[str]:
    return {x.lower() for x in re.findall(r"[가-힣A-Za-z0-9_-]{2,}", text or "")}


def retrieve_iu_evidence(message: str, context: dict | None, limit: int = 14) -> list[dict]:
    context_text = json.dumps(context or {}, ensure_ascii=False)
    query = f"{message}\n{context_text}".lower()
    q_terms = normalized_terms(query)
    wanted_topics: set[str] = set()
    for trigger, topics in TOPIC_ALIASES.items():
        if trigger in query:
            wanted_topics.update(topics)

    scored: list[tuple[float, dict]] = []
    for row in IU_BRAIN:
        topics = {str(x).lower() for x in row.get("topics", [])}
        hay = " ".join([
            str(row.get("observation", "")),
            str(row.get("quote", "")),
            " ".join(topics),
            str(row.get("source", "")),
        ]).lower()
        h_terms = normalized_terms(hay)
        overlap = len(q_terms & h_terms)
        topic_overlap = len(wanted_topics & topics)
        score = overlap * 1.0 + topic_overlap * 5.0
        tier = row.get("tier")
        if tier == "A++":
            score += 0.4
        elif tier == "A+":
            score += 0.3
        elif tier in {"A", "B+"}:
            score += 0.1
        for t in wanted_topics:
            if t in hay:
                score += 1.5
        scored.append((score, row))

    scored.sort(key=lambda x: (x[0], x[1].get("year", 0)), reverse=True)
    chosen: list[dict] = []
    seen_ids: set[str] = set()

    for score, row in scored:
        if score <= 0 or row["id"] in seen_ids:
            continue
        chosen.append(row)
        seen_ids.add(row["id"])
        if len(chosen) >= limit:
            break

    if len(chosen) < min(8, limit):
        anchors = sorted(IU_BRAIN, key=lambda r: (r.get("year", 0), r.get("id", "")))
        target_years = [2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026]
        for year in target_years:
            candidates = [r for r in anchors if r.get("year") == year and r.get("id") not in seen_ids]
            if candidates:
                row = candidates[0]
                chosen.append(row)
                seen_ids.add(row["id"])
            if len(chosen) >= min(8, limit):
                break

    return chosen[:limit]


IU_SYSTEM = """너는 'IU Brain'이라는 연구 기반 조언 엔진이다.
실제 아이유 본인인 척하거나 아이유가 사용자의 상황을 직접 봤다고 주장하지 않는다. 말투를 복제하는 챗봇도 아니다.
아래에 제공되는 EVIDENCE PACK은 아이유의 공개 인터뷰·직접 발언을 검증해 요약한 관찰치다. 답변은 이 자료에서 드러나는 사고방식과 시간에 따른 변화를 우선 근거로 삼는다.

원칙:
- 사용자의 감정을 먼저 정확히 이해하되 사실과 해석을 구분한다.
- 한 시기의 발언 하나를 '아이유의 영원한 성격'으로 일반화하지 않는다.
- 서로 다른 시기의 관찰치가 다르면 변화·모순·양가성을 그대로 보여준다.
- 아이유의 사적 심리, 진단, 숨은 의도는 추측하지 않는다.
- 공개 자료가 뒷받침하지 않는 조언은 '일반적인 관점'이라고 구분한다.
- 이해와 허용, 용서와 신뢰 회복, 감정과 행동을 서로 구분한다.
- 사용자의 최근 기록이 제공되면 그것을 현재 상황의 맥락으로만 사용하고, 아이유 자료보다 우위의 사실로 취급한다.
- 짧은 원문 문구는 필요할 때만 1개 정도 사용하고 대부분은 요약한다.

답변 형식은 자연스럽게 다음 흐름을 따른다.
1. 지금 네 마음에서 보이는 것
2. IU Brain 자료를 시간축으로 겹쳐 보면
3. 지금 적용할 수 있는 관점
4. 오늘 할 한 가지 또는 스스로에게 던질 한 질문

따뜻하지만 현실적이고, 지나친 위로나 단정은 피한다. 답변은 900자 안팎을 우선한다."""


@app.get("/health")
def health():
    return {"ok": True, "service": "my-sea", "version": "3.8-iu-brain-retrieval", "iu_brain_observations": len(IU_BRAIN)}


@app.get("/api/iu-brain/status", dependencies=[Depends(verify_password)])
def iu_brain_status():
    years = sorted({x.get("year") for x in IU_BRAIN if x.get("year")})
    files = sorted({x.get("brain_file") for x in IU_BRAIN if x.get("brain_file")})
    return {"observations": len(IU_BRAIN), "years": years, "brain_files": files, "server_key_configured": bool(SERVER_OPENAI_API_KEY)}


@app.get("/api/state", dependencies=[Depends(verify_password)])
def get_state(db: Session = Depends(get_db)):
    row = db.get(AppState, 1)
    if not row:
        return {"state": None, "updated_at": None}
    try:
        state = json.loads(row.payload)
    except Exception:
        state = {}
    return {"state": state, "updated_at": row.updated_at.isoformat() if row.updated_at else None}


@app.put("/api/state", dependencies=[Depends(verify_password)])
def put_state(body: StateBody, db: Session = Depends(get_db)):
    payload = json.dumps(body.state, ensure_ascii=False, separators=(",", ":"))
    if len(payload.encode("utf-8")) > 8 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="State is too large")
    now = datetime.now(timezone.utc)
    row = db.get(AppState, 1)
    if row:
        row.payload = payload
        row.updated_at = now
    else:
        row = AppState(id=1, payload=payload, updated_at=now)
        db.add(row)
    db.commit()
    return {"ok": True, "updated_at": now.isoformat()}


@app.post("/api/iu-advice", dependencies=[Depends(verify_password)])
def iu_advice(body: IUAdviceBody, x_ai_key: str | None = Header(default=None)):
    key = SERVER_OPENAI_API_KEY or (x_ai_key or "").strip()
    if not key:
        raise HTTPException(status_code=400, detail="OPENAI_API_KEY is not configured on the server; a temporary browser API key is required")

    msg = (body.message or "").strip()
    if not msg:
        raise HTTPException(status_code=400, detail="Message is required")

    evidence = retrieve_iu_evidence(msg, body.context, limit=14)
    evidence_lines = []
    for i, e in enumerate(evidence, 1):
        evidence_lines.append(
            f"[{i}] {e.get('year')} | {e.get('publisher')} | topics={','.join(e.get('topics', []))}\n"
            f"관찰: {e.get('observation')}\n"
            f"짧은 근거문구: {e.get('quote', '')}"
        )

    context_text = ""
    if body.context:
        context_text = "\n\n사용자가 선택적으로 제공한 최근 기록:\n" + json.dumps(body.context, ensure_ascii=False)[:10000]

    user_input = (
        f"사용자의 현재 고민:\n{msg}{context_text}\n\n"
        "EVIDENCE PACK — 이번 고민과 관련성이 높은 검증 관찰치:\n"
        + "\n\n".join(evidence_lines)
        + "\n\n이 자료를 단순 나열하지 말고, 시기별 공통점·변화·긴장을 비교해 사용자의 상황에 적용해라."
    )

    model = body.model if body.model in {"gpt-5.6-luna", "gpt-5.6-terra", "gpt-5.6-sol"} else "gpt-5.6-luna"
    payload = {
        "model": model,
        "instructions": IU_SYSTEM,
        "input": user_input,
        "reasoning": {"effort": "low"},
        "max_output_tokens": 900,
    }

    req = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            data = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            detail = json.loads(e.read().decode("utf-8"))
            detail = detail.get("error", {}).get("message", str(detail))
        except Exception:
            detail = f"OpenAI API error {e.code}"
        raise HTTPException(status_code=502, detail=detail)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI request failed: {e}")

    parts = []
    for item in data.get("output", []):
        for content in item.get("content", []):
            if content.get("type") == "output_text" and content.get("text"):
                parts.append(content["text"])
    text = "\n".join(parts).strip()
    if not text:
        text = data.get("output_text", "") or "답변을 불러오지 못했어요."

    public_evidence = [
        {
            "id": e.get("id"),
            "year": e.get("year"),
            "source": e.get("source"),
            "publisher": e.get("publisher"),
            "url": e.get("url"),
            "tier": e.get("tier"),
            "topics": e.get("topics", []),
            "quote": e.get("quote", ""),
        }
        for e in evidence[:10]
    ]
    return {
        "text": text,
        "model": model,
        "brain_total": len(IU_BRAIN),
        "evidence_used": len(evidence),
        "evidence": public_evidence,
    }


def index_file():
    html = (FRONTEND_DIR / "index.html").read_text(encoding="utf-8")
    addon = '<script src="/ai-addon.js?v=37"></script>'
    if addon not in html:
        html = html.replace("</body>", addon + "</body>")
    return HTMLResponse(html, headers={"Cache-Control": "no-store, max-age=0"})


@app.get("/")
def index():
    return index_file()


@app.get("/login")
def login_alias():
    return index_file()


@app.get("/login.html")
def login_html_alias():
    return index_file()


@app.get("/{path:path}")
def spa_fallback(path: str):
    candidate = (FRONTEND_DIR / path).resolve()
    try:
        candidate.relative_to(FRONTEND_DIR.resolve())
    except ValueError:
        return index_file()
    if candidate.is_file() and candidate.name != "login.html":
        return FileResponse(candidate, headers={"Cache-Control": "no-store, max-age=0"})
    return index_file()