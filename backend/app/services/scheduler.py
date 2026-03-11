"""
크롤링 스케줄러 및 실행 관리
- 주기적 크롤링 실행
- 수동 크롤링 트리거
- DB 저장 및 AI 요약 연동
"""
import asyncio
from typing import Dict, List
from sqlalchemy.orm import Session
from backend.database import SessionLocal
from backend.models import Product
from backend.app.services.crawler import ConvenienceStoreCrawler, DummyCrawler
import logging

logger = logging.getLogger(__name__)


async def trigger_crawl(use_dummy: bool = True, max_products: int = 20) -> Dict[str, int]:
    """
    크롤링 실행 및 DB 저장
    
    Args:
        use_dummy: True면 더미 데이터 사용, False면 실제 크롤링
        max_products: 브랜드당 최대 상품 개수
        
    Returns:
        저장된 상품 개수 {'CU': 3, 'GS25': 2, ...}
    """
    logger.info(f"🚀 크롤링 시작 - 더미모드: {use_dummy}, 최대: {max_products}개/브랜드")
    
    try:
        # 크롤링 실행
        if use_dummy:
            crawler = DummyCrawler()
        else:
            crawler = ConvenienceStoreCrawler(headless=True, delay=1.5)
        
        results = await crawler.crawl_all(max_per_brand=max_products)
        
        # DB 저장
        saved_counts = await save_products_to_db(results)
        
        logger.info(f"✅ 크롤링 및 저장 완료: {saved_counts}")
        return saved_counts
        
    except Exception as e:
        logger.error(f"❌ 크롤링 실패: {e}")
        raise


async def save_products_to_db(crawled_data: Dict[str, List[Dict]]) -> Dict[str, int]:
    """
    크롤링된 데이터를 DB에 저장
    
    Args:
        crawled_data: {'CU': [...], 'GS25': [...], '세븐일레븐': [...]}
        
    Returns:
        {'CU': 저장된개수, 'GS25': 저장된개수, ...}
    """
    db: Session = SessionLocal()
    saved_counts = {}
    
    try:
        for brand, products in crawled_data.items():
            saved_count = 0
            
            for product_data in products:
                try:
                    # 중복 체크 (같은 브랜드, 상품명)
                    existing = db.query(Product).filter(
                        Product.brand == product_data['brand'],
                        Product.name == product_data['name']
                    ).first()
                    
                    if existing:
                        # 기존 상품 업데이트 (가격 등 변경될 수 있음)
                        for key, value in product_data.items():
                            if key not in ['created_at']:  # created_at은 유지
                                setattr(existing, key, value)
                        logger.debug(f"   📝 업데이트: {product_data['name']}")
                    else:
                        # 새 상품 추가
                        new_product = Product(**product_data)
                        db.add(new_product)
                        logger.debug(f"   ✨ 신규 추가: {product_data['name']}")
                    
                    saved_count += 1
                    
                except Exception as e:
                    logger.error(f"   ❌ 상품 저장 실패: {product_data.get('name', 'Unknown')} - {e}")
                    continue
            
            db.commit()
            saved_counts[brand] = saved_count
            logger.info(f"✅ {brand}: {saved_count}개 저장 완료")
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ DB 저장 실패: {e}")
        raise
    finally:
        db.close()
    
    return saved_counts


async def crawl_and_summarize(use_dummy: bool = True, max_products: int = 20):
    """
    크롤링 + AI 요약 통합 실행 (향후 구현)
    
    1. 크롤링 실행
    2. DB 저장
    3. AI 요약 생성 (summarizer.py 연동)
    4. 감성 분석 실행
    """
    logger.info("🤖 크롤링 + AI 요약 작업 시작")
    
    try:
        # 1단계: 크롤링 및 저장
        saved_counts = await trigger_crawl(use_dummy=use_dummy, max_products=max_products)
        
        # 2단계: AI 요약 (향후 구현)
        # TODO: summarizer.py와 연동
        logger.info("⏭️  AI 요약 기능은 추후 구현 예정")
        
        logger.info(f"✅ 전체 작업 완료: {sum(saved_counts.values())}개 상품 처리")
        
    except Exception as e:
        logger.error(f"❌ 작업 실패: {e}")
        raise


# ==================== 스케줄러 설정 (추후 활성화) ====================
"""
APScheduler를 사용한 주기적 크롤링 예시:

from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

# 매일 오전 9시에 실행
scheduler.add_job(
    crawl_and_summarize,
    'cron',
    hour=9,
    minute=0,
    args=[False, 50]  # use_dummy=False, max_products=50
)

# 매주 월요일 오전 6시에 실행
scheduler.add_job(
    crawl_and_summarize,
    'cron',
    day_of_week='mon',
    hour=6,
    minute=0,
    args=[False, 100]
)

scheduler.start()
"""


# ==================== 테스트 ====================
async def test_scheduler():
    """스케줄러 테스트"""
    print("\n" + "="*60)
    print("🧪 스케줄러 테스트")
    print("="*60 + "\n")
    
    # 더미 데이터로 테스트
    saved_counts = await trigger_crawl(use_dummy=True, max_products=5)
    
    print("\n📊 저장 결과:")
    for brand, count in saved_counts.items():
        print(f"   - {brand}: {count}개")
    
    print("\n✅ 테스트 완료!\n")


if __name__ == "__main__":
    asyncio.run(test_scheduler())