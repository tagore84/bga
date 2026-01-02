
import asyncio
import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.db.session import engine
from app.models.game import Game
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

async def seed_santorini():
    async with AsyncSession(engine) as session:
        # Check if game exists
        result = await session.execute(select(Game).where(Game.name == "santorini"))
        game = result.scalar_one_or_none()
        
        if not game:
            print("Seeding Santorini...")
            new_game = Game(name="santorini", type="strategy", description="Santorini board game")
            session.add(new_game)
            await session.commit()
            print("Santorini seeded!")
        else:
            print("Santorini already exists.")

if __name__ == "__main__":
    asyncio.run(seed_santorini())
