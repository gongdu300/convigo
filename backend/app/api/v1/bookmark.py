from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Bookmark, Product
from backend.schemas import BookmarkCreate, BookmarkResponse, BookmarkListResponse, MessageResponse


router = APIRouter(prefix="/bookmark", tags=["Bookmark"])


@router.get("", response_model=BookmarkListResponse)
def get_bookmarks(
    user_id: str = Query("default_user", description="사용자 ID"),
    db: Session = Depends(get_db)
):
    """북마크 목록 조회"""
    bookmarks = db.query(Bookmark).filter(
        Bookmark.user_id == user_id
    ).order_by(Bookmark.created_at.desc()).all()
    
    return {
        "bookmarks": bookmarks,
        "total": len(bookmarks)
    }


@router.post("", response_model=BookmarkResponse, status_code=201)
def add_bookmark(
    bookmark_data: BookmarkCreate,
    db: Session = Depends(get_db)
):
    """북마크 추가"""
    product = db.query(Product).filter(Product.id == bookmark_data.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다")
    
    existing = db.query(Bookmark).filter(
        Bookmark.user_id == bookmark_data.user_id,
        Bookmark.product_id == bookmark_data.product_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="이미 북마크한 상품입니다")
    
    new_bookmark = Bookmark(**bookmark_data.model_dump())
    db.add(new_bookmark)
    db.commit()
    db.refresh(new_bookmark)
    
    return new_bookmark


@router.delete("/{bookmark_id}", response_model=MessageResponse)
def remove_bookmark(
    bookmark_id: int,
    user_id: str = Query("default_user", description="사용자 ID"),
    db: Session = Depends(get_db)
):
    """북마크 삭제"""
    bookmark = db.query(Bookmark).filter(
        Bookmark.id == bookmark_id,
        Bookmark.user_id == user_id
    ).first()
    
    if not bookmark:
        raise HTTPException(status_code=404, detail="북마크를 찾을 수 없습니다")
    
    db.delete(bookmark)
    db.commit()
    
    return {"message": "북마크가 삭제되었습니다", "success": True}


@router.delete("/product/{product_id}", response_model=MessageResponse)
def remove_bookmark_by_product(
    product_id: int,
    user_id: str = Query("default_user", description="사용자 ID"),
    db: Session = Depends(get_db)
):
    """상품 ID로 북마크 삭제"""
    bookmark = db.query(Bookmark).filter(
        Bookmark.product_id == product_id,
        Bookmark.user_id == user_id
    ).first()
    
    if not bookmark:
        raise HTTPException(status_code=404, detail="북마크를 찾을 수 없습니다")
    
    db.delete(bookmark)
    db.commit()
    
    return {"message": "북마크가 삭제되었습니다", "success": True}


@router.get("/check/{product_id}")
def check_bookmark(
    product_id: int,
    user_id: str = Query("default_user", description="사용자 ID"),
    db: Session = Depends(get_db)
):
    """북마크 여부 확인"""
    bookmark = db.query(Bookmark).filter(
        Bookmark.product_id == product_id,
        Bookmark.user_id == user_id
    ).first()
    
    return {
        "bookmarked": bookmark is not None,
        "bookmark_id": bookmark.id if bookmark else None
    }