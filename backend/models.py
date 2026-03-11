from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql import func
from backend.database import Base


class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    brand = Column(String(50), nullable=False, index=True)
    category = Column(String(100), index=True)
    price = Column(Integer, nullable=False, index=True)
    original_price = Column(Integer)
    discount_rate = Column(Float)
    calories = Column(Integer)
    protein = Column(Float)
    sugar = Column(Float)
    image_url = Column(Text)
    source_url = Column(Text)
    summary = Column(Text)
    pros = Column(Text)
    cons = Column(Text)
    taste_score = Column(Float)
    value_score = Column(Float)
    health_score = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', brand='{self.brand}')>"

# Bookmark 모델 수정 - user_id를 Integer로 변경하고 FK 추가
class Bookmark(Base):
    __tablename__ = "bookmarks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)  # String -> Integer
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", backref="bookmarks")
    product = relationship("Product", backref="bookmarks")

# --- NEW USER PREFERENCE MODEL ---
class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), unique=True, index=True, nullable=False)
    # 선호하는 브랜드와 카테고리를 JSON 형태로 저장
    preferred_brands = Column(JSON)
    preferred_categories = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<UserPreference(id={self.id}, user_id='{self.user_id}')>"
    
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
