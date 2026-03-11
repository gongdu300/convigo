# backend/routers/ai.py
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel # 🔴 BaseModel 임포트가 더 이상 필요 없으면 삭제 가능
from typing import Optional
from backend.ai.emb import smart_query, refresh_index, similar_items

router = APIRouter(prefix="/ai", tags=["ai"])

@router.get("/search", summary="자연어/유사도 검색")
def ai_search(q: str = Query(..., description="예: '초코 2+1 GS25'"),
              top_k: int = Query(20, ge=1, le=100)):
    return smart_query(q, top_k=top_k)

@router.post("/reindex", summary="인덱스 재구축")
def ai_reindex():
    n = refresh_index()
    return {"ok": True, "indexed": n}

@router.get("/similar/{item_id}", summary="유사 상품 추천")
def ai_similar(item_id: str, top_k: int = Query(12, ge=1, le=100)):
    """
    item_id를 str로 받아서 숫자/문자열 모두 처리 가능하게 함.
    내부적으로 숫자로 캐스팅 가능한 경우 int로 변환해서 similar_items 호출.
    """
    lookup_id = int(item_id) if item_id.isdigit() else item_id

    items = similar_items(lookup_id, top_k=top_k)
    if items is None:
        raise HTTPException(404, "item not found")

    return {"item_id": item_id, "count": len(items), "items": items}


# ───────────── 🔴 삭제된 부분 🔴 ─────────────
# class AskIn(BaseModel):
#     ...
#
# @router.post("/ask", ...)
# def ai_ask(body: AskIn):
#     ...
# ──────────────────────────────────────