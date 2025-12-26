# backend/app/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from jose import JWTError, jwt
from pydantic import BaseModel
from datetime import timedelta

from app.db.deps import get_db
from app.models.player import Player, PlayerType  # Import the Player model
from app.utils.auth import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    get_player_by_name,
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)

router = APIRouter(tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Pydantic schemas
typing_union = None  # placeholder to satisfy code pattern
class SignupRequest(BaseModel):
    name: str
    password: str

class LoginRequest(BaseModel):
    name: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

# Dependency: obtener usuario actual
async def get_current_player(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> Player:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        name: str | None = payload.get("sub")
        if not name:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    player = await get_player_by_name(db, name)
    if not player:
        raise credentials_exception
    return player

# Signup endpoint
@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    data: SignupRequest,
    db: AsyncSession = Depends(get_db)
):
    # Verificar name único
    result = await db.execute(select(Player).where(Player.name == data.name))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Name already taken")
    # Crear usuario
    hashed_pwd = hash_password(data.password)
    player = Player(name=data.name, hashed_password=hashed_pwd, type=PlayerType.human)
    db.add(player)
    await db.commit()
    await db.refresh(player)
    # Crear token
    access_token = create_access_token(data={"sub": player.name})
    return TokenResponse(access_token=access_token)

# Login endpoint
@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Player).where(Player.name == data.name))
    player = result.scalar_one_or_none()
    if not player or not verify_password(data.password, player.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    access_token = create_access_token(data={"sub": player.name})
    return TokenResponse(access_token=access_token)

# Obtener datos del usuario autenticado
@router.get("/me")
async def me(
    current_player: Player = Depends(get_current_player)
):
    return {"id": current_player.id, "name": current_player.name}
