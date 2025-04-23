# backend/app/utils/auth.py
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.user import User

# Configuración de hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = "supersecret"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Funciones de utilidad
def hash_password(password: str) -> str:
    """Genera un hash seguro para la contraseña dada."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica que la contraseña plana coincide con el hash."""
    return pwd_context.verify(plain_password, hashed_password)


async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    """
    Devuelve la instancia User cuyo username coincida, o None si no existe.
    """
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Crea un JWT con los datos dados y tiempo de expiración opcional.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    """
    Decodifica un JWT y devuelve el payload. Lanza HTTPException si es inválido o expirado.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e
