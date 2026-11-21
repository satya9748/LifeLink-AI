from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models import User
from app.schemas.dto import RegisterIn, UserOut
from app.core.security import hash_password, verify_password, create_access_token
from app.routers.deps import current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
ALLOWED_ROLES = {"hospital", "blood_bank", "donor"}

@router.post("/register", response_model=UserOut, status_code=201)
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    if payload.role not in ALLOWED_ROLES:
        raise HTTPException(status_code=400, detail="Public registration supports hospital, blood_bank or donor roles")
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(full_name=payload.full_name, email=payload.email.lower(),
                password_hash=hash_password(payload.password), role=payload.role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form.username.lower()).first()
    if not user or not verify_password(form.password, user.password_hash) or not user.is_active:
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    return {"access_token": create_access_token(str(user.id)), "token_type": "bearer"}

@router.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return user
