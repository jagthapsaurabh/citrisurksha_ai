from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import User
from ..schemas import ChangePasswordIn, LoginIn, RegisterIn, TokenOut, UserProfileOut, UserProfileUpdate
from ..security import create_access_token, hash_password, verify_password, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

PROFILE_FIELDS = [
    "name", "district", "language", "email", "village", "state", "address",
    "acres_land", "plants", "citrus_varieties", "irrigation_type", "farming_experience_years",
]

@router.post("/register", response_model=TokenOut)
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    if len(payload.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    if payload.confirm_password is not None and payload.password != payload.confirm_password:
        raise HTTPException(status_code=400, detail="Password and confirm password do not match")
    if db.query(User).filter(User.phone == payload.phone).first():
        raise HTTPException(status_code=409, detail="Phone already registered")
    user = User(
        name=payload.name,
        phone=payload.phone,
        password_hash=hash_password(payload.password),
        district=payload.district,
        language=payload.language,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenOut(access_token=create_access_token(user), role=user.role, name=user.name)

@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.phone == payload.phone).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid phone or password")
    if user.is_active is False:
        raise HTTPException(status_code=403, detail="Account is disabled. Contact support.")
    return TokenOut(access_token=create_access_token(user), role=user.role, name=user.name)

@router.get("/me", response_model=UserProfileOut)
def me(user: User = Depends(get_current_user)):
    return user

@router.patch("/me", response_model=UserProfileOut)
def update_me(payload: UserProfileUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    data = payload.model_dump(exclude_unset=True)
    for field in PROFILE_FIELDS:
        if field in data:
            setattr(user, field, data[field])
    required = [user.name, user.district, user.village, user.state, user.acres_land, user.plants]
    user.profile_completed = all(v not in (None, "") for v in required)
    db.commit()
    db.refresh(user)
    return user

@router.post("/change-password")
def change_password(payload: ChangePasswordIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    if len(payload.new_password) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters")
    if payload.confirm_password is not None and payload.new_password != payload.confirm_password:
        raise HTTPException(status_code=400, detail="New password and confirm password do not match")
    user.password_hash = hash_password(payload.new_password)
    db.commit()
    return {"status": "password_changed"}
