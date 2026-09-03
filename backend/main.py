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
PRINCIPLES_PATH = BASE_DIR / "knowledge" / "iu_principles_kb.v1.json"
PRINCIPLES_PROMPT_PATH = BASE_DIR / "prompts" / "my_sea_ai_system_prompt.v1.md"
APP_PASSWORD = os.getenv("APP_PASSWORD", "").strip()
SERVER_OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
DEFAULT_OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6-luna").strip()

app = FastAPI(title="나의 바다", version="4.1-iu-brain-love")


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
    model: str = DEFAULT_OPENAI_MODEL
    mode: str = "counseling"


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


def load_principles_kb() -> dict:
    try:
        return json.loads(PRINCIPLES_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"situations": [], "core_principles": []}


PRINCIPLES_KB = load_principles_kb()
PRINCIPLE_SITUATIONS = PRINCIPLES_KB.get("situations", [])
try:
    PRINCIPLES_PROMPT = PRINCIPLES_PROMPT_PATH.read_text(encoding="utf-8")
except Exception:
    PRINCIPLES_PROMPT = ""

TOPIC_ALIASES = {
    # 사람 · 관계 · 경계
    "경계": ["relationships", "closure", "self-protection", "interpretation", "future", "boundaries", "respect"],
    "거리": ["relationships", "closure", "self-protection", "boundaries"],
    "선": ["boundaries", "relationships", "respect", "closeness"],
    "신뢰": ["relationships", "feedback", "future", "trust", "psychological-safety"],
    "떠났": ["relationships", "loss", "closure", "future"],
    "버림": ["relationships", "loss", "self-protection", "future"],
    "악마화": ["evaluation", "interpretation", "complexity", "emotion", "rumination"],
    "미워": ["evaluation", "interpretation", "emotion", "love", "hate", "self-dislike"],
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

    # 사랑 · 미움 · 받는 사랑 · 주는 사랑 · 위로 · 동행
    "사랑": ["love", "receiving", "receiving-love", "giving", "reciprocity", "relationships", "confidence", "fear", "care", "companionship"],
    "사랑받": ["love", "receiving", "receiving-love", "relationships", "self-worth", "gratitude"],
    "사랑해": ["love", "expression", "giving", "relationships", "care"],
    "애정": ["love", "attachment", "care", "relationships", "commitment"],
    "보답": ["reciprocity", "receiving-love", "giving", "responsibility", "love"],
    "동행": ["companionship", "love", "care", "support", "relationships"],
    "곁": ["companionship", "care", "support", "love", "relationships"],
    "돌봄": ["care", "love", "support", "self-care", "relationships"],
    "친절": ["kindness", "love", "social-contagion", "values", "restraint"],
    "혐오": ["hate", "love", "kindness", "self-awareness", "restraint", "values"],
    "서운": ["emotion", "ambivalence", "relationships", "love", "interpretation"],
    "미안": ["guilt", "gratitude", "love", "relationships", "ambivalence"],
    "고마": ["gratitude", "love", "reciprocity", "relationships"],
    "응원": ["support", "reciprocity", "love", "companionship", "relationships"],

    # 감정 · 불안 · 공허 · 반추 · 회복
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
    "위로": ["care", "companionship", "emotion", "relationships", "reciprocity", "support", "love"],
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

LOVE_QUERY_TRIGGERS = (
    "사랑", "사랑받", "사랑해", "애정", "보답", "동행", "곁", "돌봄", "친절",
    "혐오", "미워", "서운", "미안", "고마", "응원", "위로",
)
LOVE_PRIORITY_TOPICS = {
    "love", "receiving", "receiving-love", "giving", "reciprocity", "care", "companionship",
    "support", "kindness", "attachment", "commitment", "gratitude", "ambivalence", "hate",
    "self-awareness", "restraint", "nonpossessive-love", "shared-emotion",
}


def normalized_terms(text: str) -> set[str]:
    return {x.lower() for x in re.findall(r"[가-힣A-Za-z0-9_-]{2,}", text or "")}


PRINCIPLE_ALIASES = {
    "답장": ["무응답", "읽씹", "연락 지연"],
    "연락": ["답장", "무응답", "반복 연락"],
    "단톡": ["단체 채팅방", "무반응", "소외감"],
    "성진": ["조성진", "악마화", "상대가 잘 지내는 모습"],
    "동환": ["가까운 사람", "답장 지연", "확인 욕구"],
    "게임": ["상대가 잘 지내는 모습", "악마화"],
    "경계": ["거절", "죄책감", "관계 상실"],
    "회사": ["직장", "실수", "전산 담당자"],
    "졸려": ["수면 부족", "집중 안 됨", "몸"],
    "잠": ["수면 부족", "불면", "몸"],
    "돈": ["카드 한도", "부채", "대출", "지출"],
    "빚": ["부채", "대출", "개인회생"],
    "카드": ["카드 한도", "금융 통보", "지출"],
    "개발자": ["직무 전환", "연봉", "나이 비교"],
    "연봉": ["직무 전환", "4000만원", "목표"],
    "무기력": ["아무것도 하기 싫음", "게으름", "에너지"],
    "완벽": ["완벽한 준비", "시작 못함", "계획"],
    "쳐다": ["시선", "주목", "타인의 평가", "내가 잘못했나"],
    "시선": ["쳐다봄", "주목", "타인의 평가", "자의식"],
    "사람들이": ["타인의 시선", "사회적 평가", "주목"],
    "무서": ["불안", "위험", "경계", "시선"],
}


def search_principle_situations(query: str, limit: int = 3) -> list[dict]:
    raw = re.sub(r"\s+", " ", (query or "").lower()).strip()
    additions = []
    for key, values in PRINCIPLE_ALIASES.items():
        if key in raw:
            additions.extend(values)
    expanded = " ".join([raw, *additions])
    raw_terms = normalized_terms(raw)
    query_terms = normalized_terms(expanded)
    if not query_terms:
        return []

    ranked = []
    for item in PRINCIPLE_SITUATIONS:
        hay = str(item.get("retrieval_text", "")).lower()
        item_terms = normalized_terms(hay)
        overlap = query_terms & item_terms
        raw_overlap = raw_terms & item_terms
        raw_recall = len(raw_overlap) / max(1, len(raw_terms))
        expanded_recall = len(overlap) / max(1, len(query_terms))
        precision = len(overlap) / max(1, min(len(item_terms), 30))
        scenario = str(item.get("scenario", "")).lower()
        phrase_bonus = 0.45 if scenario and (scenario in expanded or expanded in scenario) else 0.0
        phrase_bonus += sum(0.035 for term in query_terms if len(term) >= 3 and term in scenario)
        score = min(1.0, raw_recall * 0.55 + expanded_recall * 0.25 + precision * 0.20 + phrase_bonus)
        if score >= 0.055:
            ranked.append((score, item))

    ranked.sort(key=lambda pair: pair[0], reverse=True)
    return [
        {
            "id": item.get("id"),
            "category": item.get("category"),
            "scenario": item.get("scenario"),
            "first_response": item.get("first_response"),
            "reality_check_and_action": item.get("reality_check_and_action"),
            "evidence_refs": item.get("evidence_refs", []),
            "score": round(score, 3),
        }
        for score, item in ranked[: max(1, min(limit, 3))]
    ]


def local_principle_answer(matches: list[dict]) -> str:
    if not matches:
        return (
            "승재야, 지금 마음이 꽤 복잡한 것 같아. 현재 장면에서 실제로 일어난 일과 "
            "마음이 예상한 결론을 먼저 나눠보자. 지금 확인된 사실 하나만 말해줄래?"
        )
    item = matches[0]
    refs = ", ".join(str(x) for x in item.get("evidence_refs", []))
    suffix = f"\n\n연결된 원칙: {item.get('id')} · 근거 카드 {refs}" if refs else ""
    return f"{item.get('first_response', '')}\n\n{item.get('reality_check_and_action', '')}{suffix}".strip()


def retrieve_iu_evidence(message: str, context: dict | None, limit: int = 14) -> list[dict]:
    context_text = json.dumps(context or {}, ensure_ascii=False)
    query = f"{message}\n{context_text}".lower()
    q_terms = normalized_terms(query)

    wanted_topics: set[str] = set()
    for trigger, topics in TOPIC_ALIASES.items():
        if trigger in query:
            wanted_topics.update(topics)

    emotion_query = any(trigger in query for trigger in EMOTION_QUERY_TRIGGERS)
    love_query = any(trigger in query for trigger in LOVE_QUERY_TRIGGERS)

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
        if love_query:
            score += len(LOVE_PRIORITY_TOPICS & topics) * 1.1

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
- 사랑을 무조건 참기, 무제한 접근 허용, 자기희생과 동일시하지 않는다. 사랑과 경계·신뢰 조정은 동시에 가능하다.
- 받은 사랑을 반드시 같은 양으로 갚아야 하는 빚으로 취급하지 않는다. 공개 자료에는 잘 받아주는 것, 서로 응원하는 것, 상대의 독립적인 행복을 바라는 것도 사랑의 형태로 나타난다.
- 위로와 사랑을 다룰 때 상대의 문제를 대신 해결하는 것과 감당 가능한 범위에서 곁에 머무는 것을 구분한다.
- 미움·짜증·서운함이 생겼다는 사실만으로 사랑이나 관계의 과거 전체를 무효화하지 않는다. 복합감정의 가능성을 보되 반복 행동과 현실적 경계는 별도로 판단한다.
- '사랑이 미움을 이긴다'는 공개 가치관을 사용자의 안전을 희생하거나 해로운 관계를 유지해야 한다는 뜻으로 해석하지 않는다.
- 불면·신체 증상에 관한 아이유의 공개 경험을 사용자의 의료 상태에 적용하거나 진단 근거로 사용하지 않는다.
- 사용자의 최근 기록이 제공되면 현재 상황의 맥락으로만 사용한다.
- 짧은 원문 문구는 필요할 때만 1개 정도 사용하고 대부분은 요약한다.

답변 흐름:
1. 지금 네 마음에서 보이는 것
2. IU Brain 자료를 시간축으로 겹쳐 보면
3. 지금 적용할 수 있는 관점
4. 오늘 할 한 가지 또는 스스로에게 던질 한 질문

따뜻하지만 현실적이고, 지나친 위로나 단정은 피한다. 답변은 900자 안팎을 우선한다."""

if PRINCIPLES_PROMPT:
    IU_SYSTEM += "\n\n---\n\n" + PRINCIPLES_PROMPT


@app.get("/health")
def health():
    return {
        "ok": True,
        "service": "my-sea",
        "version": "4.1-iu-brain-love",
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
        "principles": len(PRINCIPLE_SITUATIONS),
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
    msg = (body.message or "").strip()
    if not msg:
        raise HTTPException(status_code=400, detail="Message is required")

    evidence = retrieve_iu_evidence(msg, body.context, limit=14)
    principle_matches = search_principle_situations(
        msg + "\n" + json.dumps(body.context or {}, ensure_ascii=False), limit=3
    )
    public_principles = [
        {
            "id": item.get("id"),
            "category": item.get("category"),
            "scenario": item.get("scenario"),
            "evidence_refs": item.get("evidence_refs", []),
            "score": item.get("score"),
        }
        for item in principle_matches
    ]

    if not key:
        return {
            "text": local_principle_answer(principle_matches),
            "model": "local-principles",
            "mode": "local_principles",
            "brain_total": len(IU_BRAIN),
            "evidence_used": 0,
            "evidence": [],
            "principles_total": len(PRINCIPLE_SITUATIONS),
            "principles_used": len(principle_matches),
            "principles": public_principles,
        }

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
        f"응답 모드: {body.mode}\n\n"
        "PRINCIPLE MATCHES — 승재의 반복 장면용 원칙 DB:\n"
        + json.dumps(principle_matches, ensure_ascii=False)
        + "\n\n"
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
        "store": False,
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
        "principles_total": len(PRINCIPLE_SITUATIONS),
        "principles_used": len(principle_matches),
        "principles": public_principles,
    }


def index_file():
    html = (FRONTEND_DIR / "index.html").read_text(encoding="utf-8")
    addon = '<script src="/ai-addon.js?v=70"></script>'
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
