# backend/app/db/session.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

# URL de conexión a PostgreSQL en modo async con asyncpg
SQLALCHEMY_DATABASE_URL = "postgresql+asyncpg://bga:secret@db:5432/bga"


# Crear el motor asíncrono
engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=True,  # Puedes ponerlo en False si no quieres ver los logs de SQL
)

# Crear el sessionmaker asíncrono
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)
