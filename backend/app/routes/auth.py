# backend/app/routes/auth.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.deps import get_db
from app.models.user import User
from app.utils.auth import hash_password, verify_password, create_access_token, decode_access_token
from pydantic import BaseModel

router = APIRouter()

class SignupRequest(BaseModel):
    username: str
    email: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

@router.post("/signup", response_model=TokenResponse)
async def signup(data: SignupRequest, db: AsyncSession = Depends(get_db)):
    # Comprueba que el usuario no exista
    result = await db.execute(select(User).where(User.username == data.username))
    if result.scalar():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Username already taken")
    # (Opcional) Comprueba que el email no exista
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Email already registered")
    # Crea el usuario con contraseña hasheada
    user = User(
        username=data.username,
        email=data.email,
        hashed_password=hash_password(data.password)
    )
    db.add(user)
    await db.commit()
    # Devuelve token JWT
    return TokenResponse(access_token=create_access_token({"sub": user.username}))

@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == data.username))
    user = result.scalar()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid credentials")
    return TokenResponse(access_token=create_access_token({"sub": user.username}))

@router.get("/me")
async def get_me(token: str, db: AsyncSession = Depends(get_db)):
    try:
        payload = decode_access_token(token)
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Invalid token")
        result = await db.execute(select(User).where(User.username == username))
        user = result.scalar()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="User not found")
        return {"id": user.id, "username": user.username, "email": user.email}
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid token")