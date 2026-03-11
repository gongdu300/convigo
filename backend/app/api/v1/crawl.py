"""
크롤링 API 엔드포인트
- 수동 크롤링 실행
- 크롤링 상태 확인
"""
from fastapi import APIRouter, BackgroundTasks, Query, status
from backend.app.services.scheduler import trigger_crawl
from backend.schemas import MessageResponse
from typing import Dict, Any

router = APIRouter()


@router.post("/crawl", status_code=status.HTTP_202_ACCEPTED) # ⬅️ 상태 코드 변경
async def run_crawling(
    background_tasks: BackgroundTasks,
    use_dummy: bool = Query(True, description="더미 데이터 사용 (테스트용)"),
    max_products: int = Query(20, ge=1, le=100, description="브랜드당 최대 상품 개수")
):
    """
    크롤링 및 요약 작업을 백그라운드에서 실행
    """
    # ⬇️ 백그라운드에서 trigger_crawl 함수 실행
    background_tasks.add_task(trigger_crawl, use_dummy=use_dummy, max_products=max_products)
    
    # ⬇️ 즉시 응답 반환
    return {
        "message": "크롤링 및 요약 작업이 백그라운드에서 시작되었습니다. 완료까지 시간이 걸릴 수 있습니다."
    }

@router.get("/crawl/status")
async def get_crawl_status():
    """
    크롤링 상태 확인 (추후 구현)
    """
    return {
        "status": "ready",
        "message": "크롤링 대기 중"
    }