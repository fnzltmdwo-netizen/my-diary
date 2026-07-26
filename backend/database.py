import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


# =========================
# 경로 / ENV
# =========================

BASE_DIR = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

load_dotenv(
    BASE_DIR / ".env"
)


# =========================
# DATABASE URL
# =========================

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./diary.db",
).strip()


# Render 또는 일부 서비스에서
# postgres:// 로 제공하는 경우 SQLAlchemy용으로 변경
if DATABASE_URL.startswith(
    "postgres://"
):
    DATABASE_URL = (
        DATABASE_URL.replace(
            "postgres://",
            "postgresql://",
            1,
        )
    )


# =========================
# Engine
# =========================

if DATABASE_URL.startswith(
    "sqlite"
):
    engine = create_engine(
        DATABASE_URL,
        connect_args={
            "check_same_thread": False
        },
    )

else:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
    )


# =========================
# Session
# =========================

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


Base = declarative_base()


def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()