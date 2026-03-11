# backend/main.py
from backend.routers.ai_chat import router as ai_chat_router

from fastapi import FastAPI, Depends, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import select, func, text
from typing import Optional, Literal
import asyncio
import logging
from backend.app.core.config import settings
from backend.app.api.v1 import products, bookmark, preferences, crawl, auth
from backend.database import engine, Base, get_db, Item
from backend.schemas import ItemOut, ItemsPage
from backend.routers.ai import router as ai_router

# 스케줄러
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger


# 크롤러
from crawler.cu_crawler import crawl_one_tab as cu_crawl, save_to_db as cu_save
from crawler.seven_crawler import crawl_one_tab as seven_crawl, save_to_db as seven_save
from crawler.gs25_crawler import crawl_one_tab as gs_crawl, save_to_db as gs_save

# ES 헬스체크
# import subprocess  <- 제거
# import time          <- 제거
import requests

ES_URL = "http://127.0.0.1:9200"

def _es_up() -> bool:
    try:
        r = requests.get(ES_URL, timeout=2)
        return r.status_code == 200
    except Exception:
        return False


# def _start_es_via_docker():  <- 제거
#     cmd = ["docker", "compose", "-f", "docker-compose.elasticsearch.yml", "up", "-d"]
#     subprocess.run(cmd, check=False)

# ⭐️ 수정된 함수: ES가 실행 중인지 '확인'만 하도록 변경
def ensure_elasticsearch():
    """ES가 실행 중인지 확인합니다. (Windows 환경)"""
    logger.info("Checking if Elasticsearch is running at %s...", ES_URL)
    if not _es_up():
        logger.error("=" * 50)
        logger.error("  Elasticsearch가 실행되고 있지 않습니다.")
        logger.error("  Windows에서 서버를 시작하기 전, 먼저 Elasticsearch를 수동으로 실행해야 합니다.")
        logger.error("  (예: Docker Desktop에서 ES 컨테이너를 실행하거나, .bat 파일로 직접 실행)")
        logger.error("=" * 50)
        raise RuntimeError(f"Elasticsearch가 {ES_URL}에서 응답하지 않습니다. ES를 먼저 실행해주세요.")
    
    logger.info("✅ Elasticsearch is running.")


# 테이블 생성
Base.metadata.create_all(bind=engine)

app = FastAPI(title="ConviGo API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger("convigo")
logger.setLevel(logging.INFO)

@app.get("/health")
def health():
    return {"status": "ok"}

# /items 라우트
@app.get("/items", response_model=ItemsPage)
def list_items(
    store: Optional[str] = Query(default=None, description="GS25 | CU | SEVEN"),
    promo: Optional[str] = Query(default=None, description="1+1 | 2+1 | 증정 | 할인"),
    promotion_type: Optional[str] = Query(default=None, description="1+1 | 2+1 | 증정 | 할인"),
    is_new: Optional[bool] = Query(default=None),
    min_price: Optional[int] = Query(default=None, ge=0),
    max_price: Optional[int] = Query(default=None, ge=0),
    sort: Optional[Literal["newest", "price_asc", "price_desc", "name_asc"]] = Query("newest"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    item_id: Optional[int] = Query(default=None, description="🔎 단건 조회용 id")
):
    # 단건 조회 모드
    if item_id is not None:
        obj = db.query(Item).filter(Item.id == item_id).first()
        if not obj:
            return {"total": 0, "page": 1, "page_size": 1, "items": []}
        return {"total": 1, "page": 1, "page_size": 1, "items": [obj]}

    filters = []
    if store:
        filters.append(Item.store == store)

    eff_promo = promo or promotion_type
    if eff_promo:
        filters.append(Item.promotion_type == eff_promo)

    if is_new is not None:
        filters.append(Item.is_new == is_new)

    if min_price is not None:
        filters.append(Item.price >= min_price)
    if max_price is not None:
        filters.append(Item.price <= max_price)

    if sort == "price_asc":
        order_expr = Item.price.asc()
    elif sort == "price_desc":
        order_expr = Item.price.desc()
    elif sort == "name_asc":
        order_expr = Item.name.asc()
    else:
        order_expr = Item.id.desc()

    total = db.scalar(select(func.count()).select_from(Item).where(*filters)) or 0
    offset = (page - 1) * page_size

    rows = (
        db.execute(
            select(Item)
            .where(*filters)
            .order_by(order_expr)
            .offset(offset)
            .limit(page_size)
        )
        .scalars()
        .all()
    )

    return {"total": total, "page": page, "page_size": page_size, "items": rows}

# 단건 상세
@app.get("/items/{item_id}", response_model=ItemOut)
def get_item_detail(item_id: int, db: Session = Depends(get_db)):
    obj = db.query(Item).filter(Item.id == item_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Item not found")
    return obj

# 라우터 등록
app.include_router(ai_chat_router)  # ✅ 새로 추가
app.include_router(ai_router)
app.include_router(auth.router, prefix=settings.API_V1_PREFIX, tags=["auth"])
app.include_router(products.router, prefix=settings.API_V1_PREFIX, tags=["products"])
app.include_router(bookmark.router, prefix=settings.API_V1_PREFIX, tags=["bookmark"])
app.include_router(preferences.router, prefix=settings.API_V1_PREFIX, tags=["preferences"])
app.include_router(crawl.router, prefix=settings.API_V1_PREFIX, tags=["crawl"])

# DB 리셋 함수 (✅ text() 사용)
def wipe_items():
    """items 테이블 전체 삭제 (PK 리셋) — Postgres 기준"""
    with engine.begin() as conn:
        conn.execute(text('TRUNCATE TABLE "items" RESTART IDENTITY CASCADE'))

# 전체 크롤링
def crawl_all_unlimited():
    """전 편의점 × 전 행사 무제한 크롤링 → DB upsert"""
    total = 0
    # CU
    for t in ["1+1", "2+1"]:
        data = cu_crawl(t, max_pages=0)
        cu_save(data)
        total += len(data)
    # 7-ELEVEN
    for t in ["1+1", "2+1", "할인"]:
        data = seven_crawl(t, max_clicks=0)
        seven_save(data)
        total += len(data)
    # GS25
    for t in ["1+1", "2+1", "증정"]:
        data = gs_crawl(t, max_pages=0)
        gs_save(data)
        total += len(data)
    logger.info(f"[CRAWL] upsert 완료 추정: {total}건")

async def _async_job(func):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, func)

# 서버 시작 이벤트
@app.on_event("startup")
async def on_startup():
    """
    서버 기동 시:
      1) ES 실행 '확인' (⭐️ 수정됨)
      2) 즉시 1회 풀크롤링
      3) 매일 04:00 DB wipe → 풀크롤링
    """
    ensure_elasticsearch()  # ⭐️ 자동 시작 대신 '확인'만 수행
    
    # 즉시 1회 크롤링
    logger.info("서버 시작: 1회성 전체 크롤링을 백그라운드에서 시작합니다...")
    asyncio.create_task(_async_job(crawl_all_unlimited))
    
    # 04:00 스케줄
    scheduler = AsyncIOScheduler(timezone="Asia/Seoul")
    def scheduled_reindex():
        logger.info("[SCHEDULER] 매일 04:00 정기 크롤링 작업을 시작합니다.")
        ensure_elasticsearch()  # ⭐️ 스케줄 작업 전에도 ES가 켜져 있는지 확인
        wipe_items()
        crawl_all_unlimited()
        logger.info("[SCHEDULER] 정기 크롤링 작업 완료.")
    
    scheduler.add_job(scheduled_reindex, CronTrigger(hour=4, minute=0))
    scheduler.start()
    logger.info("매일 04:00 자동 크롤링 스케줄이 등록되었습니다.")


# 관리용 수동 트리거
@app.post("/admin/reindex")
async def admin_reindex():
    logger.info("[ADMIN] 수동 Re-index 요청 수신")
    await _async_job(lambda: (wipe_items(), crawl_all_unlimited()))
    return {"status": "ok", "message": "reindexed"}