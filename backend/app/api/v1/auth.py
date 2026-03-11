from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from backend.database import get_db
from backend.models import User
from backend.app.core.security import hash_password, verify_password
from backend.app.core.jwt import create_access_token
from backend.schemas import UserCreate, UserOut
from sqlalchemy.exc import IntegrityError
import traceback

# 설정
SECRET_KEY = "grZkSrVqEwn6IrTZ8xw_sQ-fLBEXx-HE6tMwBsUshrgoMqKBP8pKMEkM2NmqEQCM2f7oLxS9Cqcu8uVAKhqNYw"  # 환경변수로 관리 필수!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7일

# OAuth2 스키마
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

router = APIRouter(prefix="/auth", tags=["auth"])


# ===== Schemas =====
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    username: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    token: str
    user: UserResponse


class MessageResponse(BaseModel):
    message: str
    success: bool = True

class VerifyPasswordIn(BaseModel):
    password: str

class ProfileUpdateIn(BaseModel):
    username: str

class PasswordChangeIn(BaseModel):
    current_password: str
    new_password: str


# ===== Helper Functions =====
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """현재 로그인한 사용자 가져오기"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="인증 정보가 유효하지 않습니다",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    
    return user


# ===== Routes =====
@router.post("/register")
def register(payload: UserCreate, db: Session = Depends(get_db)):
    try:
        # (1) 중복 이메일 사전 체크  → 400으로 즉시 반환
        if db.query(User).filter(User.email == payload.email).first():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="이미 존재하는 이메일입니다.")

        # (2) 유저 생성
        user = User(
            email=payload.email,
            username=payload.username,
            hashed_password=hash_password(payload.password),
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        token = create_access_token(subject=str(user.id))
        return {"user": UserOut.model_validate(user).model_dump(), "token": token}

    except IntegrityError:
        db.rollback()
        # UNIQUE(email) 충돌도 400으로
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="이미 존재하는 이메일입니다.")

    except HTTPException as e:
        # 우리가 명시적으로 던진 건 그대로 통과시킴 (500으로 덮어쓰지 않음)
        raise e

    except Exception as e:
        db.rollback()
        print("REGISTER_ERROR:", repr(e))
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="register_internal_error")


@router.post("/login")
def login(payload: dict, db: Session = Depends(get_db)):
    email = payload.get("email")
    password = payload.get("password")

    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        # 에러는 모호하게 (계정 유무/비번 오류를 구분해 주지 않기)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="이메일 또는 비밀번호가 올바르지 않습니다")

    token = create_access_token(subject=str(user.id))
    # 프론트가 기대하는 응답 형태에 맞춤 (user + token)
    return {
        "user": {"id": user.id, "email": user.email, "username": user.username},
        "token": token,
    }


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """현재 사용자 정보 조회"""
    return current_user


@router.post("/logout", response_model=MessageResponse)
def logout():
    """로그아웃 (클라이언트에서 토큰 삭제)"""
    return {
        "message": "로그아웃 되었습니다",
        "success": True
    }

@router.delete("/withdrawal", response_model=MessageResponse)
def delete_me(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    현재 로그인한 사용자를 삭제(탈퇴)합니다.
    프론트는 성공 후 로컬 토큰/유저 캐시를 삭제하고 리다이렉트합니다.
    """
    # 필요 시: 관계/외래키 제약이 있다면 '연쇄 삭제' 또는 '소프트 삭제'로 변경하세요.
    db.delete(current_user)
    db.commit()
    return {"message": "탈퇴가 완료되었습니다", "success": True}

@router.post("/verify-password")
def verify_password_route(
    payload: VerifyPasswordIn,
    current_user: User = Depends(get_current_user),
):
    """현재 비밀번호가 맞는지 확인"""
    ok = verify_password(payload.password, current_user.hashed_password)
    if not ok:
        # 400으로 명확히 반환
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="비밀번호가 일치하지 않습니다")
    return {"success": True}

@router.patch("/me", response_model=UserResponse)
def update_profile(
    payload: ProfileUpdateIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """사용자 이름 변경"""
    if not payload.username.strip():
        raise HTTPException(status_code=400, detail="username is required")
    current_user.username = payload.username.strip()
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user

@router.patch("/password")
def change_password(
    payload: PasswordChangeIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """비밀번호 변경 (현재 비밀번호 검증 포함)"""
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="현재 비밀번호가 올바르지 않습니다")
    if payload.current_password == payload.new_password:
        raise HTTPException(status_code=400, detail="새 비밀번호가 현재 비밀번호와 같습니다")
    current_user.hashed_password = hash_password(payload.new_password)
    db.add(current_user)
    db.commit()
    return {"success": True, "message": "비밀번호가 변경되었습니다"}