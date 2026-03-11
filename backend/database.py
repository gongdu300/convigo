# backend/database.py
# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import sys
from datetime import datetime
from typing import Generator

# Windows 환경 인코딩 강제 설정
if sys.platform == 'win32':
    os.environ['PGCLIENTENCODING'] = 'UTF8'
    os.environ['LANG'] = 'C'
    os.environ['LC_ALL'] = 'C'

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Boolean,
    TIMESTAMP,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.sql import func
from dotenv import load_dotenv

load_dotenv()

# ──────────────────────────────────────────────────────────────────────────────
# DB 연결 설정
# ✅ pg8000 사용 (psycopg2 대신)
# ──────────────────────────────────────────────────────────────────────────────

# .env에서 DATABASE_URL 읽기
DATABASE_URL = os.getenv('DATABASE_URL')

# psycopg2를 사용 중이라면 자동으로 pg8000으로 변경
if DATABASE_URL and 'psycopg2' in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace('postgresql+psycopg2://', 'postgresql+pg8000://')
    # client_encoding 파라미터 제거 (pg8000은 불필요)
    DATABASE_URL = DATABASE_URL.split('?')[0]
    print(f"⚠️  DATABASE_URL을 pg8000으로 자동 변경")

# .env에 없으면 기본값 사용
if not DATABASE_URL:
    DATABASE_URL = "postgresql+pg8000://postgres:1234@localhost:5432/convigo"

print(f"📊 DATABASE_URL: {DATABASE_URL}")

# pool_pre_ping: 끊어진 커넥션을 사전에 감지해 재연결
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # 연결 상태 확인
    pool_size=10,        # 커넥션 풀 크기
    max_overflow=20,     # 추가 연결 허용
    echo=False           # SQL 로깅 (개발 시 True)
)

# 세션 팩토리
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)
Base = declarative_base()


# ──────────────────────────────────────────────────────────────────────────────
# ORM 모델
# ──────────────────────────────────────────────────────────────────────────────
class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    store = Column(String(20), nullable=False)      # GS25 | CU | SEVEN
    name = Column(Text, nullable=False)
    price = Column(Integer, nullable=False)
    image_url = Column(Text)
    is_promo = Column(Boolean, default=False)
    promotion_type = Column(String(20))             # "1+1" | "2+1" | "증정" | NULL
    is_new = Column(Boolean, default=False)
    # DB 서버시간을 기본값으로 사용 (타임존 포함)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("store", "name", "promotion_type", name="uniq_item"),
    )


# ──────────────────────────────────────────────────────────────────────────────
# 초기화 & DI 헬퍼
# ──────────────────────────────────────────────────────────────────────────────
def init_db() -> None:
    """테이블이 없으면 생성한다 (idempotent)."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI Depends에서 쓸 세션 제공자."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        