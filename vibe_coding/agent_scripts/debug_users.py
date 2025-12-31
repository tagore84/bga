
import asyncio
import os
import sys

# Add backend path to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from app.models.player import Player, PlayerType

# Adjust DB URL for localhost access (assuming script runs on host)
# Default inside container is "db", but from host we need "localhost" if exposed
DB_HOST = "localhost" 
SQLALCHEMY_DATABASE_URL = f"postgresql+asyncpg://bga:secret@{DB_HOST}:5432/bga"

async def list_users():
    print(f"Connecting to {SQLALCHEMY_DATABASE_URL}...")
    engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            result = await session.execute(select(Player))
            players = result.scalars().all()
            
            print(f"\nFound {len(players)} players in the database:")
            print("-" * 60)
            print(f"{'ID':<5} | {'Name':<20} | {'Type':<10} | {'Description'}")
            print("-" * 60)
            for player in players:
                desc = player.description if player.description else ""
                print(f"{player.id:<5} | {player.name:<20} | {player.type.value:<10} | {desc}")
            print("-" * 60)
            
        except Exception as e:
            print(f"Error querying database: {e}")
            print("Make sure the database container is running and port 5432 is exposed to localhost.")
            
    await engine.dispose()

if __name__ == "__main__":
    try:
        asyncio.run(list_users())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Unexpected error: {e}")
