
import asyncio
import os
import sys
from sqlalchemy import select
from sqlalchemy.future import select

# Add project root to path
sys.path.append(os.getcwd())

# Need to import models and db
from app.db.session import engine
from app.db.base import Base
from app.models.game import Game
from app.models.player import Player, PlayerType
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession

async def check_db():
    async with AsyncSession(engine) as session:
        print("Checking Games...")
        result = await session.execute(select(Game))
        games = result.scalars().all()
        azul_game = None
        for g in games:
            print(f"Game ID: {g.id}, Name: '{g.name}'")
            if g.name.lower() == 'azul':
                azul_game = g
        
        if not azul_game:
            print("CRITICAL: Game 'azul' NOT found!")
        else:
            print(f"Found Azul game with ID: {azul_game.id}")
            
            # Check players for this game
            print(f"Checking Players for Game ID {azul_game.id}...")
            result = await session.execute(select(Player).where(Player.game_id == azul_game.id))
            players = result.scalars().all()
            print(f"Found {len(players)} players.")
            for p in players:
                print(f"Player: {p.name}, Type: {p.type}")

if __name__ == "__main__":
    asyncio.run(check_db())
