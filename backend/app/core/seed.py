import asyncio
import logging
import os
import torch

from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.player import Player, PlayerType
from app.models.game import Game
from app.core.ai_base import register_ai

# Chess Strategies
from app.core.chess.ai_chess_minimax import MinimaxChessAI
from app.core.chess.ai_chess_random import RandomChessAI

# TicTacToe Strategies
from app.core.tictactoe.ai_tictactoe_random import RandomTicTacToeAI

# Azul Strategies
from app.core.azul.ai_azul_random import RandomAzulAI
from app.core.azul.random_plus_adapter import RandomPlusAdapter
from app.core.azul.heuristic_min_max_mcts_adapter import HeuristicMinMaxMctsAdapter
from app.core.azul.deep_mcts_player_adapter import AIAzulDeepMCTS

# Determine model path for Azul DeepMCTS
AZUL_MODEL_PATH = os.path.join(os.path.dirname(__file__), "azul", "zero", "models", "best.pt")
AZUL_MODEL_DEVICE = 'cuda' if torch.cuda.is_available() else 'mps' if torch.backends.mps.is_available() else 'cpu'

# --- GLOBAL AI CONFIGURATION ---
# Centralized source of truth for all AI players in the platform.
# Format: "game_name": [ { "name", "description", "strategy" (optional) } ]
AI_PLAYER_CONFIG = {
    "tictactoe": [
        {
            "name": "RandomTicTacToe", 
            "description": "Elige movimientos válidos al azar",
            "strategy": RandomTicTacToeAI() 
        }
    ],
    "azul": [
        # Random
        {"name": "RandomAzul", "description": "Elige movimientos válidos al azar", "strategy": RandomAzulAI()},
        {"name": "RandomPlusAzul", "description": "IA aleatoria mejorada (evita penalizaciones obvias)", "strategy": RandomPlusAdapter()},
        
        # DeepMCTS
        {
            "name": "AzulZero_MCTS", 
            "description": "IA basada en AlphaZero (MCTS + Red Neuronal)", 
            "strategy": AIAzulDeepMCTS(model_path=AZUL_MODEL_PATH, device=AZUL_MODEL_DEVICE, mcts_iters=300, cpuct=1.0)
        },

        # Heuristics
        {"name": "MinMax2", "description": "Estrategia MinMax (Profundidad 2)", "strategy": HeuristicMinMaxMctsAdapter(strategy='minmax', depth=2)},
        {"name": "MinMax4", "description": "Estrategia MinMax (Profundidad 4)", "strategy": HeuristicMinMaxMctsAdapter(strategy='minmax', depth=4)},
    ],
    "chess": [
        {
            "name": "Muy Fácil (IA)",
            "description": "IA Aleatoria (Random)",
            "strategy": RandomChessAI()
        },
        {
            "name": "Fácil (IA)",
            "description": "IA Minimax (Profundidad 2)",
            "strategy": MinimaxChessAI(depth=2)
        },
        {
            "name": "Medio (IA)",
            "description": "IA Minimax (Profundidad 3)",
            "strategy": MinimaxChessAI(depth=3)
        },
        {
            "name": "Difícil (IA)",
            "description": "IA Minimax (Profundidad 4)",
            "strategy": MinimaxChessAI(depth=4)
        },
        {
            "name": "Extremo (IA)",
            "description": "IA Minimax (Profundidad 5)",
            "strategy": MinimaxChessAI(depth=5)
        }
    ]
}

def register_all_strategies():
    """
    Registers Python strategies (if available) into the AI factory.
    Called on startup.
    """
    print("Registering AI Strategies...")
    for game_name, ais in AI_PLAYER_CONFIG.items():
        for ai_conf in ais:
            if ai_conf.get("strategy"):
                register_ai(ai_conf["name"], ai_conf["strategy"])
                print(f"[{game_name}] Registered strategy code for: {ai_conf['name']}")

async def seed_games(db: AsyncSession):
    """
    Inserts default games if they don't exist.
    """
    juegos = [
        ("tictactoe", "Juego clásico de tres en raya"),
        ("azul", "Juego de losetas y patrones inspirado en el Palacio Real de Évora"),
        ("chess", "Clásico Juego de Ajedrez")
    ]
    for name, description in juegos:
        result = await db.execute(select(Game).where(Game.name == name))
        existing = result.scalar_one_or_none()
        if not existing:
            game = Game(name=name, description=description)
            db.add(game)
            await db.commit()
            await db.refresh(game)
            print(f"Juego {game.name} creado.")
        else:
            # Optional: update description? For now, leave as is.
            pass

async def sync_ai_players(db: AsyncSession):
    """
    Ensures that for every AI in CONFIG, a player exists in the DB.
    Also updates descriptions if changed.
    """
    print("Syncing AI Players to DB...")
    
    for game_name, ais in AI_PLAYER_CONFIG.items():
        # 1. Get Game ID
        result = await db.execute(select(Game).where(Game.name == game_name))
        game = result.scalar_one_or_none()
        
        if not game:
            print(f"Warning: Game '{game_name}' not found in DB. Skipping AI sync for it.")
            continue
            
        for ai_conf in ais:
            # Check if AI exists
            result = await db.execute(select(Player).where(Player.name == ai_conf["name"]))
            existing_ai = result.scalar_one_or_none()
            
            if not existing_ai:
                # Create
                new_ai = Player(
                    name=ai_conf["name"],
                    description=ai_conf["description"],
                    game_id=game.id,
                    hashed_password=None, # It's an AI
                    type=PlayerType.ai
                )
                db.add(new_ai)
                await db.commit()
                print(f"[{game_name}] Created AI Player: {ai_conf['name']}")
            else:
                # Update if needed (e.g. description changed)
                if existing_ai.description != ai_conf["description"] or existing_ai.game_id != game.id:
                    existing_ai.description = ai_conf["description"]
                    existing_ai.game_id = game.id # Should match
                    db.add(existing_ai)
                    await db.commit()
                    print(f"[{game_name}] Updated AI Player: {ai_conf['name']}")
                else:
                    # print(f"[{game_name}] AI {ai_conf['name']} already exists and is up to date.")
                    pass
    
    print("AI Player Sync Complete.")
