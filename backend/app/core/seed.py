import asyncio
import logging
import os
import torch

from sqlalchemy import delete, or_
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.player import Player, PlayerType
from app.models.game import Game
from app.core.ai_base import register_ai

# Game Models for cleanup
from app.models.tictactoe.tictactoe import TicTacToeGame
from app.models.chess.chess import ChessGame
from app.models.azul.azul import AzulGame
from app.models.connect4.connect4 import Connect4Game
from app.models.nim.nim import NimGame
from app.models.wythoff.wythoff import WythoffGame
from app.models.santorini.santorini import SantoriniGame

# Chess Strategies
from app.core.chess.ai_chess_minimax import MinimaxChessAI
from app.core.chess.ai_chess_random import RandomChessAI

# TicTacToe Strategies
from app.core.tictactoe.ai_tictactoe_random import RandomTicTacToeAI

# Connect4 Strategies
# Connect4 Strategies
from app.core.connect4.ai_connect4_random import RandomConnect4AI
from app.core.connect4.ai_connect4_negamax import NegamaxConnect4AI

# Azul Strategies
from app.core.azul.ai_azul_random import RandomAzulAI
from app.core.azul.random_plus_adapter import RandomPlusAdapter
from app.core.azul.heuristic_min_max_mcts_adapter import HeuristicMinMaxMctsAdapter
from app.core.azul.deep_mcts_player_adapter import AIAzulDeepMCTS

# Nim Strategies
from app.core.nim.ai_nim import NimAIExpert, NimAIIntermediate
from app.core.wythoff.ai_wythoff import WythoffAI
from app.core.santorini.ai_santorini_random import RandomSantoriniAI

# Determine model path for Azul DeepMCTS
AZUL_MODEL_PATH = os.path.join(os.path.dirname(__file__), "azul", "zero", "models", "best.pt")
AZUL_MODEL_DEVICE = 'cuda' if torch.cuda.is_available() else 'mps' if torch.backends.mps.is_available() else 'cpu'

# --- CONFIGURATION CONSTANTS ---
RESET_DB_ON_STARTUP = os.getenv("RESET_DB_ON_STARTUP", "False").lower() == "true"

# --- GLOBAL AI CONFIGURATION ---
# Centralized source of truth for all AI players in the platform.
# Format: "game_name": [ { "name", "description", "strategy" (optional) } ]

AI_PLAYER_CONFIG = {}

def safe_instantiate(strategy_ws_func):
    try:
        return strategy_ws_func()
    except Exception as e:
        print(f"⚠️ Failed to instantiate AI strategy: {e}")
        return None

# Re-build config safely
AI_PLAYER_CONFIG = {
    "tictactoe": [
        {"name": "RandomTicTacToe", "description": "Elige movimientos válidos al azar", "strategy": RandomTicTacToeAI()}
    ],
    "connect4": [
        {"name": "Connect4 Fácil (IA)", "description": "IA Negamax (Profundidad 1)", "strategy": NegamaxConnect4AI(depth=1)},
        {"name": "Connect4 Medio (IA)", "description": "IA Negamax (Profundidad 4)", "strategy": NegamaxConnect4AI(depth=4)},
        {"name": "Connect4 Difícil (IA)", "description": "IA Negamax (Profundidad 8)", "strategy": NegamaxConnect4AI(depth=8)},
    ],
    "azul": [
        {"name": "Azul Fácil (IA)", "description": "Estrategia MinMax (Profundidad 1)", "strategy": HeuristicMinMaxMctsAdapter(strategy='minmax', depth=1)},
        {"name": "Azul Medio (IA)", "description": "Estrategia MinMax (Profundidad 2)", "strategy": HeuristicMinMaxMctsAdapter(strategy='minmax', depth=2)},
        {"name": "Azul Difícil (IA)", "description": "Estrategia MinMax (Profundidad 4)", "strategy": HeuristicMinMaxMctsAdapter(strategy='minmax', depth=4)}
    ],
    "chess": [
         {"name": "Chess Fácil (IA)", "description": "IA Minimax (Profundidad 2)", "strategy": MinimaxChessAI(depth=2)},
         {"name": "Chess Medio (IA)", "description": "IA Minimax (Profundidad 3)", "strategy": MinimaxChessAI(depth=3)},
         {"name": "Chess Difícil (IA)", "description": "IA Minimax (Profundidad 4)", "strategy": MinimaxChessAI(depth=4)},
         {"name": "Chess Extremo (IA)", "description": "IA Minimax (Profundidad 5)", "strategy": MinimaxChessAI(depth=5)}
    ],
    "nim": [
         {"name": "Nim Misere (Experto)", "description": "IA Experta en Nim Misere", "strategy": NimAIExpert()},
         {"name": "Nim Misere (Intermedio)", "description": "IA Nivel Intermedio", "strategy": NimAIIntermediate()},
    ],
    "wythoff": [
        {"name": "Wythoff AI", "description": "IA Wythoff (Razón Áurea)", "strategy": WythoffAI()}
    ],
    "santorini": [
        {"name": "Santorini Random (IA)", "description": "IA Aleatoria (Pruebas)", "strategy": RandomSantoriniAI()}
    ]
}
# Append experimental safely
try:
    exp_strategy = AIAzulDeepMCTS(model_path=AZUL_MODEL_PATH, device=AZUL_MODEL_DEVICE, mcts_iters=300, cpuct=1.0, single_player_mode=True)
    AI_PLAYER_CONFIG["azul"].append(
        {"name": "Experimental (IA)", "description": "IA basada en AlphaZero (MCTS + Red Neuronal)", "strategy": exp_strategy}
    )
except Exception as e:
    print(f"⚠️  Skipping Experimental AI (DeepMCTS): {e}")

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
        ("chess", "Clásico Juego de Ajedrez"),
        ("connect4", "Juego de estrategia vertical para conectar cuatro fichas"),
        ("nim", "Nim Misere: Quien toma el último objeto pierde"),
        ("wythoff", "Wythoff Nim: Variante con dos montones y movimientos diagonales"),
        ("santorini", "Juego estratégico de construir torres y subir a sus cimas en una isla griega")
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
    # Check existence of any AI players
    result = await db.execute(select(Player.id).where(Player.type == PlayerType.ai))
    ai_ids = result.scalars().all()

    # If RESET is requested, or if we want to ensure we are clean, we delete.
    # But since we want to be smart, if NOT reset, we try to append missing ones.
    
    if RESET_DB_ON_STARTUP:
        print(f"RESET_DB_ON_STARTUP is True. Cleaning up AI players and games...")
        
        # Delete games involving AI players
        if ai_ids:
            await db.execute(delete(TicTacToeGame).where(or_(TicTacToeGame.player_x.in_(ai_ids), TicTacToeGame.player_o.in_(ai_ids))))
            await db.execute(delete(ChessGame).where(or_(ChessGame.player_white.in_(ai_ids), ChessGame.player_black.in_(ai_ids))))
            await db.execute(delete(Connect4Game).where(or_(Connect4Game.player_red.in_(ai_ids), Connect4Game.player_blue.in_(ai_ids))))
            await db.execute(delete(NimGame).where(or_(NimGame.player_1_id.in_(ai_ids), NimGame.player_2_id.in_(ai_ids))))
            await db.execute(delete(WythoffGame).where(or_(WythoffGame.player_1_id.in_(ai_ids), WythoffGame.player_2_id.in_(ai_ids))))
            await db.execute(delete(SantoriniGame).where(or_(SantoriniGame.player_p1.in_(ai_ids), SantoriniGame.player_p2.in_(ai_ids))))
        
        # Clean Azul games (Unconditional as per previous logic)
        await db.execute(delete(AzulGame)) 
        await db.commit()

        # Delete ALL AI players
        await db.execute(delete(Player).where(Player.type == PlayerType.ai))
        
        # Also clean up common test users as requested (exact matches and patterns)
        # Using specific patterns observed in user report
        await db.execute(delete(Player).where(
            or_(
                Player.name.in_(['tester', 'Test', 'pytest', 'chk_u1']),
                Player.name.like('chk_%'),
                Player.name.like('del_%')
            )
        ))
        
        await db.commit()
        print("All AI and Test players deleted.")
        ai_ids = [] # Reset list so we enter creation loop

    # If NOT reset, we just proceed to check/create each one.
    
    for game_name, ais in AI_PLAYER_CONFIG.items():
        # Get Game ID
        # Try exact match first
        result = await db.execute(select(Game).where(Game.name == game_name))
        game = result.scalar_one_or_none()
        
        # If not found, try case-insensitive
        if not game:
            result = await db.execute(select(Game).where(Game.name.ilike(game_name)))
            game = result.scalar_one_or_none()

        if not game:
            print(f"Warning: Game '{game_name}' not found in DB. Skipping AI sync for it.")
            continue
            
        game_id_val = game.id
        print(f"[{game_name}] Syncing AI players for Game ID: {game_id_val}")
            
        for ai_conf in ais:
            try:
                # Check if this specific AI player already exists
                stmt = select(Player).where(
                    Player.name == ai_conf["name"],
                    Player.game_id == game_id_val,
                    Player.type == PlayerType.ai
                )
                result = await db.execute(stmt)
                existing_ai = result.scalar_one_or_none()

                if existing_ai:
                    # Update description if needed, or just skip
                    # print(f"[{game_name}] AI Player '{ai_conf['name']}' already exists. Skipping.")
                    continue

                # Create if missing
                new_ai = Player(
                    name=ai_conf["name"],
                    description=ai_conf["description"],
                    game_id=game_id_val,
                    hashed_password=None,
                    type=PlayerType.ai
                )
                db.add(new_ai)
                await db.commit()
                print(f"[{game_name}] Created NEW AI Player: {ai_conf['name']}")
            except Exception as e:
                print(f"[{game_name}] ERROR creating AI '{ai_conf['name']}': {e}")
                await db.rollback()
    
    print("AI Player Sync Complete.")
