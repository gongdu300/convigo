from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import UserPreference
from backend.schemas import (
    UserPreferenceCreate,
    UserPreferenceUpdate,
    UserPreferenceResponse,
    MessageResponse
)

router = APIRouter(prefix="/preferences", tags=["Preferences"])


@router.get("", response_model=UserPreferenceResponse)
def get_user_preference(
    user_id: str = Query("default_user", description="사용자 ID"),
    db: Session = Depends(get_db)
):
    """사용자 취향 설정 조회"""
    preference = db.query(UserPreference).filter(
        UserPreference.user_id == user_id
    ).first()
    
    if not preference:
        raise HTTPException(status_code=404, detail="취향 설정을 찾을 수 없습니다")
    
    return preference


@router.post("", response_model=UserPreferenceResponse, status_code=201)
def create_user_preference(
    preference_data: UserPreferenceCreate,
    db: Session = Depends(get_db)
):
    """사용자 취향 설정 생성"""
    existing = db.query(UserPreference).filter(
        UserPreference.user_id == preference_data.user_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail="이미 취향 설정이 존재합니다. PUT 메서드로 업데이트하세요."
        )
    
    preference_dict = preference_data.model_dump()
    if preference_dict.get('preferred_brands'):
        preference_dict['preferred_brands'] = ','.join(preference_dict['preferred_brands'])
    
    new_preference = UserPreference(**preference_dict)
    db.add(new_preference)
    db.commit()
    db.refresh(new_preference)
    
    return new_preference


@router.put("", response_model=UserPreferenceResponse)
def update_user_preference(
    preference_data: UserPreferenceUpdate,
    user_id: str = Query("default_user", description="사용자 ID"),
    db: Session = Depends(get_db)
):
    """사용자 취향 설정 업데이트 (없으면 생성)"""
    preference = db.query(UserPreference).filter(
        UserPreference.user_id == user_id
    ).first()
    
    if not preference:
        preference_dict = preference_data.model_dump()
        preference_dict['user_id'] = user_id
        
        if preference_dict.get('preferred_brands'):
            preference_dict['preferred_brands'] = ','.join(preference_dict['preferred_brands'])
        
        preference = UserPreference(**preference_dict)
        db.add(preference)
    else:
        update_data = preference_data.model_dump(exclude_unset=True)
        
        if 'preferred_brands' in update_data and update_data['preferred_brands']:
            update_data['preferred_brands'] = ','.join(update_data['preferred_brands'])
        
        for key, value in update_data.items():
            setattr(preference, key, value)
    
    db.commit()
    db.refresh(preference)
    
    return preference


@router.delete("", response_model=MessageResponse)
def delete_user_preference(
    user_id: str = Query("default_user", description="사용자 ID"),
    db: Session = Depends(get_db)
):
    """사용자 취향 설정 삭제"""
    preference = db.query(UserPreference).filter(
        UserPreference.user_id == user_id
    ).first()
    
    if not preference:
        raise HTTPException(status_code=404, detail="취향 설정을 찾을 수 없습니다")
    
    db.delete(preference)
    db.commit()
    
    return {
        "message": "취향 설정이 삭제되었습니다",
        "success": True
    }