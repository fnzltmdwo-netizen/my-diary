import json
import os
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

app = FastAPI(title="나의 바다", version="3.3-server")

class AppState(Base):
    __tablename__ = "app_state"
    id = Column(Integer, primary_key=True, default=1)
    payload = Column(Text, nullable=False, default="{}")
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

class StateBody(BaseModel):
    state: dict

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
    return {"ok": True, "service": "my-sea", "version": "3.3-server"}

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
