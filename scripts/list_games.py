
import asyncio
import sys
import os
from sqlalchemy import text

# Add the backend directory to sys.path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.db.session import AsyncSessionLocal

async def list_games():
    async with AsyncSessionLocal() as db:
        result = await db.execute(text("SELECT id, name FROM games"))
        games = result.fetchall()
        for row in games:
            print(f"ID: {row[0]}, Name: {row[1]}")

if __name__ == "__main__":
    asyncio.run(list_games())
