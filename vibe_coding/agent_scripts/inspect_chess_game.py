
import asyncio
import sys
import os

print("Script started")

# Add the backend directory to sys.path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.db.session import AsyncSessionLocal
from app.models.chess.chess import ChessGame
from app.routes.chess.chess import ChessGameState
from app.models.player import Player
from sqlalchemy.future import select

async def inspect_game(game_id):
    async with AsyncSessionLocal() as db:
        # Get Game
        result = await db.execute(select(ChessGame).where(ChessGame.id == game_id))
        game = result.scalar_one_or_none()
        
        if not game:
            print(f"Game {game_id} not found")
            return

        print(f"Game ID: {game.id}")
        
        # Get Players
        w_name = None
        b_name = None
        if game.player_white:
            p = await db.get(Player, game.player_white)
            w_name = p.name if p else None
            
        if game.player_black:
            p = await db.get(Player, game.player_black)
            b_name = p.name if p else None
            
        # Simulate API Response creation
        try:
            game_state = ChessGameState(
                id=game.id,
                board_fen=game.board_fen,
                current_turn=game.current_turn,
                status=game.status,
                white_player_name=w_name,
                black_player_name=b_name,
                white_player_id=game.player_white,
                black_player_id=game.player_black,
                config=game.config
            )
            print("\nAPI Response Model Validation SUCCESS:")
            print(game_state.json(indent=2))
        except Exception as e:
            print(f"\nAPI Response Model Validation FAILED: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python inspect_chess_game.py <game_id>")
    else:
        asyncio.run(inspect_game(int(sys.argv[1])))
