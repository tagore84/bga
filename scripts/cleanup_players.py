
import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.abspath("backend"))

# Force DB_HOST to localhost for local execution
os.environ["DB_HOST"] = "localhost"

from app.db.session import AsyncSessionLocal
from app.models.player import Player
from sqlalchemy import select, delete

async def cleanup_players():
    print("Starting player cleanup...")
    async with AsyncSessionLocal() as db:
        # Fetch all players
        result = await db.execute(select(Player))
        players = result.scalars().all()
        
        users_to_delete = []
        for p in players:
            name = p.name
            if name == "verify_user" or name == "Test_human" or name.startswith("TestHuman_"):
                users_to_delete.append(p.id)
                print(f"Marking for deletion: {name} (ID: {p.id})")
        
        if not users_to_delete:
            print("No players found to delete.")
            return

        # Delete players
        # DELETE FROM players WHERE id IN (...)
        await db.execute(delete(Player).where(Player.id.in_(users_to_delete)))
        await db.commit()
        print(f"Successfully deleted {len(users_to_delete)} players.")

if __name__ == "__main__":
    try:
        asyncio.run(cleanup_players())
    except Exception as e:
        print(f"Error during cleanup: {e}")
