import json
import os
import re
import urllib.error
import urllib.request
from collections import Counter
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

app = FastAPI(title="나의 바다", version="4.0-iu-brain-emotion")


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
    for path in sorted(IU_BRAIN_DIR.glob("verified_observations*.jsonl")):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except Exception:
            continue
        for line in lines:
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except Exception:
                continue
            if row.get("id") and row.get("observation"):
                row.setdefault("brain_file", path.name)
                by_id[str(row["id"])] = row
    return list(by_id.values())


IU_BRAIN = load_iu_brain()

TOPIC_ALIASES = {
    # 사람 · 관계 · 경계
    "경계": ["relationships", "closure", "self-protection", "interpretation", "future", "boundaries", "respect"],
    "거리": ["relationships", "closure", "self-protection", "boundaries"],
    "선": ["boundaries", "relationships", "respect", "closeness"],
    "신뢰": ["relationships", "feedback", "future", "trust", "psychological-safety"],
    "떠났": ["relationships", "loss", "closure", "future"],
    "버림": ["relationships", "loss", "self-protection", "future"],
    "악마화": ["evaluation", "interpretation", "complexity", "emotion", "rumination"],
    "미워": ["evaluation", "interpretation", "emotion", "love", "self-dislike"],
    "친구": ["relationships", "people", "feedback", "future", "friendship"],
    "친밀": ["relationships", "closeness", "boundaries", "trust", "respect"],
    "사람": ["relationships", "people", "evaluation", "future", "personhood"],
    "가치관": ["values", "moral-alignment", "relationships", "friendship"],
    "오해": ["interpretation", "projection", "categorization", "relationships"],
    "먼저 연락": ["initiative", "agency", "friendship", "relationships"],
    "증명": ["proof", "action", "commitment", "relationships"],
    "팬": ["fans", "relationships", "gratitude", "reciprocity", "responsibility"],

    # 자기애 · 자기수용 · 자기비난
    "자존감": ["self-esteem", "self-love", "self-image", "evaluation", "self-standard"],
    "자기수용": ["self-acceptance", "self-love", "self-friendship", "imperfection", "contentment"],
    "자기혐오": ["self-dislike", "self-acceptance", "self-love", "self-doubt"],
    "자기비난": ["self-esteem", "self-compassion", "evaluation", "perfectionism", "self-criticism"],
    "자책": ["self-criticism", "self-compassion", "failure", "evaluation"],
    "부족": ["imperfection", "self-acceptance", "self-evaluation", "growth"],
    "엄격": ["self-standard", "self-compassion", "perfection", "standards"],
    "게으": ["self-criticism", "self-evaluation", "work", "activation"],
    "무기력": ["lethargy", "self-observation", "activation", "acceptance", "recovery"],
    "자격": ["self-worth", "receiving-love", "approval", "responsibility"],
    "완벽": ["perfection", "perfectionism", "perspective", "flexibility", "self-standard", "completion"],

    # 성공 · 실패 · 비교 · 타인의 평가
    "실패": ["failure", "success", "effort", "uncertainty", "self-standard", "fairness", "attribution"],
    "성공": ["success", "attribution", "collaboration", "self-standard", "career", "luck", "agency"],
    "성과": ["success", "achievement", "attribution", "evaluation", "process"],
    "실적": ["success", "ranking", "evaluation", "achievement"],
    "순위": ["ranking", "popularity", "success", "status", "evaluation"],
    "1등": ["ranking", "success", "status", "goals"],
    "일등": ["ranking", "success", "status", "goals"],
    "비교": ["comparison", "evaluation", "self-standard", "self-image", "admiration"],
    "남들은": ["comparison", "evaluation", "self-standard", "self-image"],
    "남보다": ["comparison", "evaluation", "ranking", "self-standard"],
    "부럽": ["comparison", "admiration", "individuality", "self-context"],
    "열등": ["comparison", "self-image", "evaluation", "self-worth"],
    "평가": ["evaluation", "self-standard", "identity", "feedback", "scope"],
    "칭찬": ["evaluation", "feedback", "recognition", "self-evaluation"],
    "악플": ["evaluation", "feedback", "self-protection", "selective-attention"],
    "인정": ["recognition", "self-standard", "success", "evaluation"],
    "무시": ["evaluation", "status", "self-standard", "recognition"],
    "평판": ["evaluation", "popularity", "fame", "status"],
    "기대": ["expectations", "evaluation", "fear", "responsibility"],
    "실망": ["feedback", "evaluation", "relationships", "expectations"],
    "인기": ["fame", "popularity", "success", "fear", "self-protection", "evaluation"],

    # 감정 · 불안 · 공허 · 반추 · 회복
    "사랑": ["love", "receiving", "reciprocity", "relationships", "confidence", "fear", "care"],
    "일": ["work", "motivation", "success", "effort", "regulation", "activation"],
    "휴식": ["rest", "self-care", "limits", "sustainability", "recovery"],
    "쉬": ["rest", "self-care", "limits", "recovery"],
    "책임": ["responsibility", "accountability", "fans", "work"],
    "부담": ["burden", "responsibility", "fear", "expectations"],
    "불안": ["fear", "uncertainty", "self-protection", "emotion", "anxiety", "recovery"],
    "걱정": ["worry", "anxiety", "reflection", "emotion", "rumination"],
    "두려": ["fear", "uncertainty", "self-protection", "confidence", "emotion"],
    "외로": ["loneliness", "emotion", "relationships", "success", "recovery"],
    "공허": ["emotion", "avoidance", "recovery", "work", "emptiness", "cycles"],
    "허무": ["emptiness", "emotion", "avoidance", "recovery", "cycles"],
    "허전": ["emptiness", "emotion", "recovery", "cycles"],
    "감정": ["emotion", "acceptance", "rumination", "recovery"],
    "반추": ["rumination", "emotion", "recovery", "feedback", "letting-go"],
    "계속 생각": ["rumination", "worry", "emotion", "recovery"],
    "생각이 멈": ["rumination", "worry", "emotion", "recovery"],
    "매몰": ["rumination", "emotion", "problem-solving", "recovery"],
    "번아웃": ["burnout", "depletion", "rest", "recovery", "limits", "creativity"],
    "소진": ["burnout", "depletion", "rest", "recovery", "limits"],
    "권태": ["malaise", "lethargy", "emotion", "change", "recovery"],
    "지쳤": ["depletion", "rest", "recovery", "self-care", "limits"],
    "지쳐": ["depletion", "rest", "recovery", "self-care", "limits"],
    "아무것도 하기 싫": ["lethargy", "emotion", "activation", "acceptance", "recovery"],
    "포기하고 싶": ["persistence", "limits", "self-compassion", "progress", "recovery"],
    "억누": ["emotion", "avoidance", "acceptance", "recovery"],
    "참고 있": ["emotion", "avoidance", "acceptance", "limits"],
    "회복": ["recovery", "emotion", "acceptance", "cycles", "self-care"],
    "다시 돌아": ["recovery", "return", "emotion", "cycles", "self-compassion"],
    "위로": ["care", "companionship", "emotion", "relationships", "reciprocity"],
    "상실": ["loss", "grief", "continuity", "care", "emotion", "recovery"],
    "슬프": ["grief", "emotion", "acceptance", "time", "recovery"],
    "울고": ["emotion", "acceptance", "grief", "recovery"],
    "일기": ["journaling", "memory", "emotion", "time", "self-observation"],
    "기록": ["journaling", "memory", "records", "time", "self-observation"],
    "과거": ["past", "letting-go", "growth", "closure", "hindsight"],
    "후회": ["past", "decision", "effort", "closure", "regret"],
    "행복": ["happiness", "contentment", "meaning", "self-acceptance", "wellbeing"],
    "꿈": ["dreams", "future", "coping", "identity"],
}


EMOTION_QUERY_TRIGGERS = (
    "불안", "걱정", "두려", "외로", "공허", "허무", "허전", "감정", "반추",
    "계속 생각", "생각이 멈", "매몰", "번아웃", "소진", "권태", "지쳤", "지쳐",
    "무기력", "아무것도 하기 싫", "포기하고 싶", "억누", "참고 있", "회복", "슬프", "울고",
)
EMOTION_PRIORITY_TOPICS = {
    "emotion", "acceptance", "recovery", "rumination", "emptiness", "anxiety", "worry",
    "cycles", "self-care", "limits", "grief", "lethargy", "malaise", "persistence",
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

    emotion_query = any(trigger in query for trigger in EMOTION_QUERY_TRIGGERS)

    scored: list[tuple[float, dict]] = []
    for row in IU_BRAIN:
        topics = {str(x).lower() for x in row.get("topics", [])}
        hay = " ".join([
            str(row.get("observation", "")),
            str(row.get("quote", "")),
            " ".join(topics),
            str(row.get("source", "")),
            str(row.get("publisher", "")),
        ]).lower()
        h_terms = normalized_terms(hay)
        overlap = len(q_terms & h_terms)
        topic_overlap = len(wanted_topics & topics)
        score = overlap * 1.0 + topic_overlap * 5.0

        tier = row.get("tier")
        if tier == "A++":
            score += 0.5
        elif tier == "A+":
            score += 0.35
        elif tier in {"A", "B+"}:
            score += 0.15

        for topic in wanted_topics:
            if topic in hay:
                score += 1.5

        if emotion_query:
            score += len(EMOTION_PRIORITY_TOPICS & topics) * 1.1

        scored.append((score, row))

    scored.sort(key=lambda x: (x[0], x[1].get("year", 0)), reverse=True)

    chosen: list[dict] = []
    seen_ids: set[str] = set()
    year_counts: Counter = Counter()

    # 관련성은 유지하되 한 시기의 발언만 과대표집하지 않는다.
    for score, row in scored:
        if score <= 0 or row.get("id") in seen_ids:
            continue
        year = row.get("year")
        if year and year_counts[year] >= 3:
            continue
        chosen.append(row)
        seen_ids.add(row["id"])
        if year:
            year_counts[year] += 1
        if len(chosen) >= limit:
            break

    # 질문이 넓거나 직접 일치 자료가 적으면 시간축 앵커를 보충한다.
    if len(chosen) < min(8, limit):
        anchors = sorted(IU_BRAIN, key=lambda r: (r.get("year", 0), r.get("id", "")))
        target_years = list(range(2010, 2027))
        for year in target_years:
            candidates = [
                r for r in anchors
                if r.get("year") == year and r.get("id") not in seen_ids
            ]
            if not candidates:
                continue
            row = candidates[0]
            chosen.append(row)
            seen_ids.add(row["id"])
            year_counts[year] += 1
            if len(chosen) >= min(8, limit):
                break

    return chosen[:limit]


IU_SYSTEM = """너는 'IU Brain'이라는 연구 기반 조언 엔진이다.
실제 아이유 본인인 척하거나 아이유가 사용자의 상황을 직접 봤다고 주장하지 않는다. 말투를 복제하는 챗봇도 아니다.
아래 EVIDENCE PACK은 아이유의 공개 인터뷰·직접 발언을 검증해 요약한 관찰치다. 답변은 이 자료에서 드러나는 사고방식과 시간에 따른 변화를 우선 근거로 삼는다.

원칙:
- 사용자의 감정을 먼저 정확히 이해하되 사실과 해석을 구분한다.
- 한 시기의 발언 하나를 '아이유의 영원한 성격'으로 일반화하지 않는다.
- 서로 다른 시기의 관찰치가 다르면 변화·모순·양가성을 그대로 보여준다.
- 아이유의 사적 심리, 진단, 숨은 의도는 추측하지 않는다.
- 공개 자료가 뒷받침하지 않는 조언은 '일반적인 관점'이라고 구분한다.
- 이해와 허용, 용서와 신뢰 회복, 감정과 행동을 서로 구분한다.
- 성공·실패·평가를 다룰 때 외부 결과와 자기 가치, 주관적 안녕을 자동으로 같은 축으로 취급하지 않는다.
- 비교를 다룰 때 타인의 강점을 인정하는 것과 자신을 열등하다고 판결하는 것을 구분한다.
- 감정은 실제 경험이지만 미래의 예언이나 자기 존재에 대한 판결로 자동 변환하지 않는다.
- 불안·슬픔·공허를 빨리 제거하는 것만 회복으로 취급하지 않는다. 필요하면 감정을 알아차리고 충분히 느끼는 시간과 다음 행동으로 복귀하는 과정을 함께 본다.
- 감정을 느끼는 것과 같은 장면·반응을 반복 확인하는 반추를 구분한다. 반추가 커진 상황에서는 더 많은 해석보다 현재로 돌아오는 작은 행동을 우선할 수 있다.
- 회복을 '완전히 괜찮아짐'으로만 정의하지 않는다. 오늘 자기 자신을 버리지 않고 가능한 다음 행동을 하는 것도 회복의 일부다.
- 일이나 일정으로 감정을 덮는 전략을 무조건 권하지 않는다. 공개 자료에서도 그 방식의 단기 효과와 한계가 함께 드러난다.
- 불면·신체 증상에 관한 아이유의 공개 경험을 사용자의 의료 상태에 적용하거나 진단 근거로 사용하지 않는다.
- 사용자의 최근 기록이 제공되면 현재 상황의 맥락으로만 사용한다.
- 짧은 원문 문구는 필요할 때만 1개 정도 사용하고 대부분은 요약한다.

답변 흐름:
1. 지금 네 마음에서 보이는 것
2. IU Brain 자료를 시간축으로 겹쳐 보면
3. 지금 적용할 수 있는 관점
4. 오늘 할 한 가지 또는 스스로에게 던질 한 질문

따뜻하지만 현실적이고, 지나친 위로나 단정은 피한다. 답변은 900자 안팎을 우선한다."""


@app.get("/health")
def health():
    return {
        "ok": True,
        "service": "my-sea",
        "version": "4.0-iu-brain-emotion",
        "iu_brain_observations": len(IU_BRAIN),
    }


@app.get("/api/iu-brain/status", dependencies=[Depends(verify_password)])
def iu_brain_status():
    years = sorted({x.get("year") for x in IU_BRAIN if x.get("year")})
    files = sorted({x.get("brain_file") for x in IU_BRAIN if x.get("brain_file")})
    return {
        "observations": len(IU_BRAIN),
        "years": years,
        "brain_files": files,
        "server_key_configured": bool(SERVER_OPENAI_API_KEY),
    }


@app.get("/api/state", dependencies=[Depends(verify_password)])
def get_state(db: Session = Depends(get_db)):
    row = db.get(AppState, 1)
    if not row:
        return {"state": None, "updated_at": None}
    try:
        state = json.loads(row.payload)
    except Exception:
        state = {}
    return {
        "state": state,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


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
        raise HTTPException(
            status_code=400,
            detail="OPENAI_API_KEY is not configured on the server; a temporary browser API key is required",
        )

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
        context_text = (
            "\n\n사용자가 선택적으로 제공한 최근 기록:\n"
            + json.dumps(body.context, ensure_ascii=False)[:10000]
        )

    user_input = (
        f"사용자의 현재 고민:\n{msg}{context_text}\n\n"
        "EVIDENCE PACK — 이번 고민과 관련성이 높은 검증 관찰치:\n"
        + "\n\n".join(evidence_lines)
        + "\n\n이 자료를 단순 나열하지 말고, 시기별 공통점·변화·긴장을 비교해 사용자의 상황에 적용해라."
    )

    model = (
        body.model
        if body.model in {"gpt-5.6-luna", "gpt-5.6-terra", "gpt-5.6-sol"}
        else "gpt-5.6-luna"
    )
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
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
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
    addon = '<script src="/ai-addon.js?v=40"></script>'
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
