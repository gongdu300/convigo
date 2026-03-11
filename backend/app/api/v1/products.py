from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from backend.database import get_db
from backend.models import Product
from backend.schemas import ProductListResponse, ProductResponse

router = APIRouter()

@router.get("/products", response_model=ProductListResponse)
def get_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    brand: Optional[str] = Query(None, description="편의점 브랜드: CU, GS25, 세븐일레븐"),
    db: Session = Depends(get_db)
):
    """
    행사상품 목록 조회
    
    - skip: 건너뛸 개수 (페이지네이션)
    - limit: 가져올 개수
    - brand: 브랜드 필터 (선택)
    """
    query = db.query(Product)
    
    # 브랜드 필터 적용
    if brand:
        query = query.filter(Product.brand == brand)
    
    # 최신순 정렬
    query = query.order_by(Product.created_at.desc())
    
    # 전체 개수 & 페이지네이션
    total = query.count()
    products = query.offset(skip).limit(limit).all()
    
    return ProductListResponse(total=total, products=products)


@router.get("/products/{product_id}", response_model=ProductResponse)
def get_product_detail(
    product_id: int,
    db: Session = Depends(get_db)
):
    """
    상품 상세 조회
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    
    if not product:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다")
    
    return product