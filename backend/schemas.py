# backend/schemas.py
from pydantic import BaseModel, Field, ConfigDict, validator, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

class ItemOut(BaseModel):
    id: int
    store: str
    name: str
    price: int
    image_url: Optional[str] = None
    is_promo: bool
    promotion_type: Optional[str] = None
    is_new: bool

    class Config:
        from_attributes = True  # SQLAlchemy 객체 -> Pydantic 변환

class ItemsPage(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[ItemOut]


# ==================== Product 스키마 ====================
class ProductBase(BaseModel):
    """상품 기본 정보"""
    name: str = Field(..., description="상품명")
    brand: str = Field(..., description="브랜드")
    category: Optional[str] = Field(None, description="카테고리")
    price: int = Field(..., ge=0, description="판매가")
    original_price: Optional[int] = Field(None, ge=0, description="정가")
    discount_rate: Optional[float] = Field(None, ge=0, le=100, description="할인율 (%)")
    calories: Optional[int] = Field(None, ge=0, description="칼로리 (kcal)")
    protein: Optional[float] = Field(None, ge=0, description="단백질 (g)")
    sugar: Optional[float] = Field(None, ge=0, description="당류 (g)")
    image_url: Optional[str] = Field(None, description="이미지 URL")
    source_url: Optional[str] = Field(None, description="출처 URL")
    summary: Optional[str] = Field(None, description="요약")
    pros: Optional[str] = Field(None, description="장점")
    cons: Optional[str] = Field(None, description="단점")
    taste_score: Optional[float] = Field(None, ge=0, le=10, description="맛 점수 (0-10)")
    value_score: Optional[float] = Field(None, ge=0, le=10, description="가성비 점수 (0-10)")
    health_score: Optional[float] = Field(None, ge=0, le=10, description="건강 점수 (0-10)")

    # 필요시 검증자 등 추가 가능
    # @validator("discount_rate")
    # def check_discount_rate(cls, v):
    #     if v is not None and (v < 0 or v > 100):
    #         raise ValueError("discount_rate must be between 0 and 100")
    #     return v

class ProductCreate(ProductBase):
    """상품 생성 요청 스키마 (모든 필수 필드은 ProductBase가 이미 다 명시)"""
    pass

class ProductUpdate(BaseModel):
    """상품 수정 요청: 선택적 필드들"""
    name: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    price: Optional[int] = Field(None, ge=0)
    original_price: Optional[int] = Field(None, ge=0)
    discount_rate: Optional[float] = Field(None, ge=0, le=100)
    calories: Optional[int] = Field(None, ge=0)
    protein: Optional[float] = Field(None, ge=0)
    sugar: Optional[float] = Field(None, ge=0)
    image_url: Optional[str] = None
    source_url: Optional[str] = None
    summary: Optional[str] = None
    pros: Optional[str] = None
    cons: Optional[str] = None
    taste_score: Optional[float] = Field(None, ge=0, le=10)
    value_score: Optional[float] = Field(None, ge=0, le=10)
    health_score: Optional[float] = Field(None, ge=0, le=10)

class ProductResponse(ProductBase):
    """상품 응답 스키마 (DB 포함)"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    # Pydantic v2 설정: DB 모델의 속성으로부터 값을 채워주도록
    model_config = ConfigDict(from_attributes=True)

class ProductListResponse(BaseModel):
    """상품 목록 응답"""
    total: int = Field(..., description="전체 상품 개수")
    products: List[ProductResponse] = Field(..., description="상품 목록")
    page: Optional[int] = Field(1, ge=1, description="현재 페이지")
    page_size: Optional[int] = Field(20, ge=1, le=100, description="페이지당 개수")


# ==================== Bookmark 스키마 ====================
class BookmarkBase(BaseModel):
    """북마크 기본 정보"""
    product_id: int = Field(..., description="상품 ID")

class BookmarkCreate(BookmarkBase):
    """북마크 생성 요청"""
    user_id: str = Field(..., description="사용자 ID")

class BookmarkResponse(BookmarkBase):
    """북마크 응답 스키마 (상품 정보 포함)"""
    id: int
    user_id: str
    created_at: datetime
    product: ProductResponse

    model_config = ConfigDict(from_attributes=True)

class BookmarkListResponse(BaseModel):
    total: int
    bookmarks: List[BookmarkResponse]


# ==================== User Preference 스키마 ====================
class UserPreferenceBase(BaseModel):
    preferred_brands: Optional[List[str]] = Field(
        None, description="선호 브랜드 리스트"
    )
    preferred_categories: Optional[List[str]] = Field(
        None, description="선호 카테고리 리스트"
    )

class UserPreferenceCreate(UserPreferenceBase):
    user_id: str = Field(..., description="사용자 ID")

class UserPreferenceUpdate(UserPreferenceBase):
    pass

class UserPreferenceResponse(UserPreferenceBase):
    id: int
    user_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str

class UserOut(BaseModel):
    id: int
    email: EmailStr
    username: str

    class Config:
        from_attributes = True  # SQLAlchemy -> Pydantic 변환



# ==================== 필터 / 공통 / 기타 스키마 ====================
class ProductFilter(BaseModel):
    brand: Optional[str] = Field(None, description="브랜드 필터")
    category: Optional[str] = Field(None, description="카테고리 필터")
    min_price: Optional[int] = Field(None, ge=0, description="최소 가격")
    max_price: Optional[int] = Field(None, ge=0, description="최대 가격")
    min_calories: Optional[int] = Field(None, ge=0, description="최소 칼로리")
    max_calories: Optional[int] = Field(None, ge=0, description="최대 칼로리")
    min_discount: Optional[float] = Field(None, ge=0, le=100, description="최소 할인율")
    sort_by: Optional[str] = Field("created_at", description="정렬 기준")
    order: Optional[str] = Field("desc", description="정렬 방향 (asc 또는 desc)")
    page: int = Field(1, ge=1, description="페이지 번호")
    page_size: int = Field(20, ge=1, le=100, description="페이지당 개수")

class MessageResponse(BaseModel):
    message: str = Field(..., description="응답 메시지")
    success: Optional[bool] = Field(True, description="성공 여부")

class ErrorResponse(BaseModel):
    error: str = Field(..., description="에러 메시지")
    detail: Optional[str] = Field(None, description="상세 정보")

class CrawlResponse(BaseModel):
    message: str = Field(..., description="크롤링 상태 메시지")
    saved_counts: Optional[Dict[str, int]] = Field(
        None, description="각 출처별 저장된 개수 예: {'CU': 10, 'GS25': 8}"
    )

class SummaryRequest(BaseModel):
    product_id: int = Field(..., description="상품 ID")

class SummaryResponse(BaseModel):
    product_id: int
    summary: str = Field(..., description="한줄 요약")
    pros: str = Field(..., description="장점")
    cons: str = Field(..., description="단점")
    taste_score: float = Field(..., ge=0, le=10, description="맛 점수")
    value_score: float = Field(..., ge=0, le=10, description="가성비 점수")
    health_score: float = Field(..., ge=0, le=10, description="건강 점수")