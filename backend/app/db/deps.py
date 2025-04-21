# backend/app/db/deps.py

from app.db.session import AsyncSessionLocal
from sqlalchemy.ext.asyncio import AsyncSession

async def get_db() -> AsyncSession:
    #"Dependency que provee una sesión de base de datos.
    async with AsyncSessionLocal() as session:
        yield session