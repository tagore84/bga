
import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.abspath("backend"))

# Force DB_HOST to localhost
os.environ["DB_HOST"] = "localhost"

from app.db.session import AsyncSessionLocal
from app.models.player import Player
from sqlalchemy import select

async def add_experimental_player():
    print("Checking for Experimental player...")
    async with AsyncSessionLocal() as db:
        # Check if exists
        result = await db.execute(select(Player).where(Player.name == "Experimental"))
        existing = result.scalar_one_or_none()
        
        if existing:
            print("Player 'Experimental' already exists.")
            return

        print("Creating 'Experimental' player...")
        # Assuming game_id=2 is Azul based on context
        new_player = Player(
            name="Experimental",
            type="ai",
            game_id=2, 
            hashed_password="ai", # Dummy
            description="Experimental DeepMCTS Player"
        )
        db.add(new_player)
        await db.commit()
        print("Successfully added 'Experimental' player.")

if __name__ == "__main__":
    try:
        asyncio.run(add_experimental_player())
    except Exception as e:
        print(f"Error: {e}")
