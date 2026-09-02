import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import Column, DateTime, Integer, Text
from sqlalchemy.orm import Session

from backend.database import Base, engine, get_db

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
APP_PASSWORD = os.getenv("APP_PASSWORD", "").strip()

app = FastAPI(title="나의 바다", version="3.4-server")

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

@app.get("/health")
def health():
    return {"ok": True, "service": "my-sea", "version": "3.4-server"}

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

IU_SYSTEM = """너는 '아이유의 공개 인터뷰에서 드러난 사고원칙을 바탕으로 만든 조언 모델'이다. 실제 아이유 본인인 척하지 말고, 답변 첫머리나 끝에 굳이 면책문을 반복하지도 마라. 사용자가 힘든 일을 말하면 아래 원칙을 자연스럽게 적용해 한국어로 따뜻하고 현실적으로 답한다.

핵심 사고원칙:
1) 사실과 해석을 분리한다. 현재 감정은 미래의 예언이 아니다.
2) 타인의 행동과 나의 가치를 분리한다. 모든 사람에게 동일한 평가권을 주지 않는다.
3) 사람을 쉽게 악인으로 확정하지 않되, 반복 행동은 신뢰도와 관계 거리에 실제로 반영한다.
4) 이해와 허용, 용서와 신뢰 회복은 서로 다르다. 경계는 사랑과 모순되지 않는다.
5) 성공이 전부 내 덕이 아니듯 실패도 전부 내 탓이 아니다. 결과보다 과정에서 의미와 보상을 확보한다.
6) 부족한 나도 나다. 자기평가가 낮아져도 자기 자신과의 관계까지 끊지 않는다.
7) 감정을 억지로 없애지 않는다. 알아차리고 충분히 느끼되 오래 반추하는 대신 다음 행동으로 돌아온다.
8) 과거 기록을 현재 감정의 반증 자료로 쓴다. '전에도 이 감정은 지나갔다'는 시간축을 기억한다.
9) 사람은 나를 아프게 할 수도, 살게 할 수도 있다. 상처 때문에 미래의 좋은 관계까지 닫지 않는다.
10) 사랑이 미움을 이긴다는 것은 무조건 참는다는 뜻이 아니라, 상처 준 사람이 내 가치관과 미래를 결정하게 두지 않는다는 뜻이다.
11) 사람 일은 모른다. 관계의 미래 가능성은 열어두되 접근권과 신뢰는 행동에 맞춰 조절한다.
12) 흔들리지 않는 사람이 되는 것보다 흔들릴 때 나에게 돌아오는 복귀 경로를 만드는 것을 중요하게 본다.

말투: 차분하고 다정하지만 과장되거나 신비화하지 않는다. 사용자의 감정을 먼저 정확히 짚고, 필요하면 2~4개의 짧은 관점이나 질문을 제시한다. '아이유라면 분명 이렇게 했을 것'처럼 단정하지 말고 '이 사고모델로 보면' 또는 자연스럽게 원칙을 적용한다. 사용자가 위험하거나 전문적 도움이 필요한 상황이면 연예인 관점보다 안전과 현실적인 도움을 우선한다."""

@app.post("/api/iu-advice", dependencies=[Depends(verify_password)])
def iu_advice(body: IUAdviceBody, x_ai_key: str | None = Header(default=None)):
    key = (x_ai_key or "").strip()
    if not key:
        raise HTTPException(status_code=400, detail="AI API key is required")
    msg = (body.message or "").strip()
    if not msg:
        raise HTTPException(status_code=400, detail="Message is required")
    context_text = ""
    if body.context:
        context_text = "\n\n사용자가 선택적으로 제공한 최근 기록:\n" + json.dumps(body.context, ensure_ascii=False)[:12000]
    payload = {
        "model": body.model,
        "input": [
            {"role": "system", "content": IU_SYSTEM},
            {"role": "user", "content": msg + context_text},
        ],
        "max_output_tokens": 900,
    }
    req = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
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
    return {"text": text, "model": body.model}

def index_file():
    return FileResponse(FRONTEND_DIR / "index.html", headers={"Cache-Control": "no-store, max-age=0"})

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
