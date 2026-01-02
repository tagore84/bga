# backend/app/routes/chess/chess.py
from typing import Optional, List, Literal
import json
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime
import chess
import random

from app.db.deps import get_db
from app.models.chess.chess import ChessGame
from app.routes.auth import get_current_player
from app.models.player import Player
from app.models.game import Game
import app.core.redis as core_redis
from app.db.session import AsyncSessionLocal

import logging
logger = logging.getLogger(__name__)

from app.core.ai_base import get_ai
from app.core.chess.ai_chess_minimax import MinimaxChessAI
from sqlalchemy.orm.attributes import flag_modified

# Strategies are registered in main.py via seed.register_all_strategies()

router = APIRouter(tags=["chess"])


# Helper for evaluation
evaluator = MinimaxChessAI(depth=0)

def get_board_evaluation(fen: str) -> float:
    try:
        board = chess.Board(fen)
        score = evaluator.evaluate_board(board)
        logger.info(f"Evaluation for FEN {fen[:20]}... : {score}")
        return score
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        return 0.0
# --- Schemas ---
class ChessCreateGameRequest(BaseModel):
    game_name: Optional[str] = None
    white_player_id: Optional[int]
    black_player_id: Optional[int]
    opponent_type: Literal["human", "ai"] = "human" # Simplified config
    variant: Literal["standard", "chess960"] = "standard"

class ChessGameState(BaseModel):
    id: int
    board_fen: str
    current_turn: str
    status: str
    white_player_name: Optional[str]
    black_player_name: Optional[str]
    white_player_id: Optional[int]
    black_player_id: Optional[int]
    config: dict
    evaluation: float = 0.0
    is_check: bool = False


class ChessMoveRequest(BaseModel):
    move_uci: str # e2e4

# --- Routes ---

@router.get("/", response_model=List[ChessGameState])
async def list_games(db: AsyncSession = Depends(get_db)):
    q = await db.execute(select(ChessGame).where(ChessGame.status == "in_progress"))
    games = q.scalars().all()
    
    out = []
    for g in games:
        w_name = None
        b_name = None
        if g.player_white:
            p = await db.get(Player, g.player_white)
            w_name = p.name
        if g.player_black:
            p = await db.get(Player, g.player_black)
            b_name = p.name
            
        out.append(ChessGameState(
            id=g.id,
            board_fen=g.board_fen,
            current_turn=g.current_turn,
            status=g.status,
            white_player_name=w_name,
            black_player_name=b_name,
            white_player_id=g.player_white,
            black_player_id=g.player_black,
            config=g.config,
            evaluation=get_board_evaluation(g.board_fen),
            is_check=chess.Board(g.board_fen).is_check()
        ))
    return out

@router.post("/", response_model=ChessGameState)
async def create_game(
    req: ChessCreateGameRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_player = Depends(get_current_player)
):
    # 1. Get Game Definition
    result = await db.execute(select(Game).where(Game.name == "chess"))
    base_game = result.scalar_one_or_none()
    if not base_game:
        raise HTTPException(500, "Game definition 'chess' not found (run seed)")

    # 2. Determine Players
    # Very simple logic: Creator plays White, requested opponent plays Black
    # Or based on req inputs.
    
    # Let's assume req.white_player_id is set or current_player takes it
    p_white = req.white_player_id
    p_black = req.black_player_id

    # Create Game
    game_config = req.dict()
    game_config["moves"] = []
    
    # Ensure opponent_type is preserved
    if not game_config.get("opponent_type"):
        # Infer from players
        p1 = await db.get(Player, p_white) if p_white else None
        p2 = await db.get(Player, p_black) if p_black else None
        if (p1 and p1.type == "ai") or (p2 and p2.type == "ai"):
            game_config["opponent_type"] = "ai"
        else:
            game_config["opponent_type"] = "human"

    if req.variant == "chess960":
        # Generate random position 0-959
        scharnagl = random.randint(0, 959)
        board = chess.Board.from_chess960_pos(scharnagl)
        board.chess960 = True
        initial_fen = board.fen()
        # Maybe store the start pos?
        game_config["start_fen"] = initial_fen
        game_config["chess960"] = True
    else:
        initial_fen = chess.Board().fen()

    game_name = req.game_name or f"Chess {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
    new_game = ChessGame(
        board_fen=initial_fen,
        current_turn="white", # python-chess uses boolean, we map to string
        status="in_progress",
        config=game_config,
        game_name=game_name,
        player_white=p_white,
        player_black=p_black,
        game_id=base_game.id,
        created_at=datetime.utcnow()
    )
    db.add(new_game)
    await db.commit()
    await db.refresh(new_game)

    # 3. Publish Redis Event
    try:
        await core_redis.redis_pool.xadd(
            f"chess:{new_game.id}",
            {"type":"create", "fen":new_game.board_fen}
        )
    except Exception as e:
        logger.error(f"Failed to publish create event: {e}")

    # Trigger AI if it's the first player
    # await process_ai_turns(new_game.id, db)
    background_tasks.add_task(process_ai_turns, new_game.id)
    
    # We don't await the AI move, so we return the initial state.
    # The frontend will receive the AI move via WebSocket.

    # 4. Return Initial State
    w_name = None
    b_name = None
    if p_white:
        p = await db.get(Player, p_white)
        w_name = p.name
    if p_black:
        p = await db.get(Player, p_black)
        b_name = p.name

    return ChessGameState(
        id=new_game.id,
        board_fen=new_game.board_fen,
        current_turn=new_game.current_turn,
        status=new_game.status,
        white_player_name=w_name,
        black_player_name=b_name,
        white_player_id=new_game.player_white,
        black_player_id=new_game.player_black,
        config=new_game.config,
        evaluation=get_board_evaluation(new_game.board_fen),
        is_check=False # Initial board is never in check
    )

async def process_ai_turns(game_id: int):
    """
    Checks if the current turn belongs to an AI and if so, plays the move.
    Repeats until it's a human's turn or game over.
    Runs in background, so manages its own DB session.
    """
    async with AsyncSessionLocal() as db:
        while True:
            # Re-fetch game to get latest state
            result = await db.execute(select(ChessGame).where(ChessGame.id == game_id))
            game = result.scalar_one_or_none()
            if not game or game.status != "in_progress":
                break
            
            # Determine current turn player ID
            current_turn_player_id = game.player_white if game.current_turn == 'white' else game.player_black
            if not current_turn_player_id:
                break

            # Check if this player is AI
            player_obj = await db.get(Player, current_turn_player_id)
            if not player_obj or player_obj.type != "ai":
                break

            # It's AI's turn
            ai = get_ai(player_obj.name) 
            if not ai:
                logger.error(f"AI strategy '{player_obj.name}' not found for player {player_obj.id}")
                break

            # Calculate Move
            ai_state = {"board_fen": game.board_fen}
            ai_move_uci = ai.select_move(ai_state)
            
            if not ai_move_uci:
                logger.warning(f"AI {player_obj.name} returned no move")
                break

            # Apply AI Move
            try:
                is_chess960 = game.config.get("chess960", False)
                board = chess.Board(game.board_fen, chess960=is_chess960)
                move = chess.Move.from_uci(ai_move_uci)
                if move not in board.legal_moves:
                    logger.error(f"AI {player_obj.name} generated illegal move: {ai_move_uci}")
                    break
                
                board.push(move)
                 
                # Update Game Status
                new_status = "in_progress"
                if board.is_game_over():
                    if board.is_checkmate():
                        new_status = "checkmate"
                    elif board.is_stalemate():
                        new_status = "stalemate"
                    elif board.is_insufficient_material():
                        new_status = "draw"
                    else:
                        new_status = "draw"
                elif board.can_claim_threefold_repetition():
                    new_status = "draw"
                elif board.can_claim_fifty_moves():
                    new_status = "draw"
                
                if not isinstance(game.config, dict):
                    game.config = {}
                moves = game.config.get("moves", [])
                moves.append(ai_move_uci)
                # Force update config since it's JSON
                game.config = {**game.config, "moves": moves}
                flag_modified(game, "config")

                game.board_fen = board.fen()
                game.current_turn = "white" if board.turn == chess.WHITE else "black"
                game.status = new_status
                
                db.add(game)
                await db.commit()
                await db.refresh(game)

                # Calc evaluation
                eval_score = get_board_evaluation(game.board_fen)

                # Publish AI Move
                try:
                    await core_redis.redis_pool.xadd(
                        f"chess:{game.id}",
                        {
                            "type": "move",
                            "fen": game.board_fen,
                            "by": "white" if game.current_turn == 'black' else "black", # logic inverted because turn already swapped
                            "move_uci": ai_move_uci,
                            "status": game.status,
                            "evaluation": str(eval_score),
                            "is_check": str(board.is_check())
                        }
                    )
                except Exception as e:
                    logger.error(f"Redis publish failed for AI move: {e}")

            except Exception as e:
                logger.error(f"Error applying AI move: {e}")
                break

@router.post("/{game_id}/undo", response_model=ChessGameState)
async def undo_move(
    game_id: int,
    db: AsyncSession = Depends(get_db),
    current_player: Player = Depends(get_current_player)
):
    result = await db.execute(select(ChessGame).where(ChessGame.id == game_id))
    game = result.scalar_one_or_none()
    if not game:
        raise HTTPException(404, "Game not found")

    if game.status not in ["in_progress", "checkmate", "stalemate", "draw"]:
         pass

    if not isinstance(game.config, dict):
        game.config = {}
        
    moves = game.config.get("moves", [])
    
    if not moves:
        raise HTTPException(400, "No moves to undo")

    opponent_type = game.config.get("opponent_type", "human")
    
    # Fallback: check player types if opponent_type says human but players might be AI
    if opponent_type == "human":
         w_player = await db.get(Player, game.player_white) if game.player_white else None
         b_player = await db.get(Player, game.player_black) if game.player_black else None
         if (w_player and w_player.type == "ai") or (b_player and b_player.type == "ai"):
             opponent_type = "ai"

    undo_count = 1
    
    if opponent_type == "ai":
        human_is_white = (game.player_white == current_player.id)
        current_turn_is_white = (game.current_turn == 'white')
        
        if human_is_white == current_turn_is_white:
            # It's my turn. Means AI moved last. Undo 2.
            undo_count = 2
        else:
            # It's opponent's turn. I just moved. Undo 1.
            undo_count = 1
            
    if len(moves) < undo_count:
        undo_count = len(moves)

    new_moves = moves[:-undo_count]
    
    new_moves = moves[:-undo_count]
    
    start_fen = game.config.get("start_fen", chess.STARTING_FEN)
    is_chess960 = game.config.get("chess960", False)
    board = chess.Board(start_fen, chess960=is_chess960)
    
    for m in new_moves:
        board.push(chess.Move.from_uci(m))
        
    game.board_fen = board.fen()
    game.current_turn = "white" if board.turn == chess.WHITE else "black"
    game.status = "in_progress"
    game.config = {**game.config, "moves": new_moves}
    flag_modified(game, "config")
    
    db.add(game)
    await db.commit()
    await db.refresh(game)
    
    eval_score = get_board_evaluation(game.board_fen)
    
    try:
        await core_redis.redis_pool.xadd(
            f"chess:{game.id}",
            {
                "type": "undo",
                "fen": game.board_fen,
                "status": game.status,
                "evaluation": str(eval_score),
                "is_check": str(chess.Board(game.board_fen).is_check())
            }
        )
    except Exception as e:
        logger.error(f"Redis publish failed: {e}")

    w_name = None
    b_name = None
    if game.player_white:
        p = await db.get(Player, game.player_white)
        w_name = p.name
    if game.player_black:
        p = await db.get(Player, game.player_black)
        b_name = p.name

    return ChessGameState(
        id=game.id,
        board_fen=game.board_fen,
        current_turn=game.current_turn,
        status=game.status,
        white_player_name=w_name,
        black_player_name=b_name,
        white_player_id=game.player_white,
        black_player_id=game.player_black,
        config=game.config,
        evaluation=eval_score,
        is_check=chess.Board(game.board_fen).is_check()
    )

@router.delete("/{game_id}")
async def delete_game(game_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ChessGame).where(ChessGame.id == game_id))
    game = result.scalar_one_or_none()
    if not game:
        raise HTTPException(404, "Game not found")
        
    await db.delete(game)
    await db.commit()
    return {"message": "Game deleted successfully", "id": game_id}

@router.get("/{game_id}", response_model=ChessGameState)
async def get_game(game_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ChessGame).where(ChessGame.id == game_id))
    game = result.scalar_one_or_none()
    if not game:
        raise HTTPException(404, "Game not found")

    w_name = None
    b_name = None
    if game.player_white:
        p = await db.get(Player, game.player_white)
        w_name = p.name
    if game.player_black:
        p = await db.get(Player, game.player_black)
        b_name = p.name
        
    return ChessGameState(
        id=game.id,
        board_fen=game.board_fen,
        current_turn=game.current_turn,
        status=game.status,
        white_player_name=w_name,
        black_player_name=b_name,
        white_player_id=game.player_white,
        black_player_id=game.player_black,
        config=game.config,
        evaluation=get_board_evaluation(game.board_fen),
        is_check=chess.Board(game.board_fen).is_check()
    )

@router.post("/{game_id}/move", response_model=ChessGameState)
async def make_move(
    game_id: int,
    req: ChessMoveRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_player: Player = Depends(get_current_player)
):
    # 1. Load Game
    result = await db.execute(select(ChessGame).where(ChessGame.id == game_id))
    game = result.scalar_one_or_none()
    if not game:
        raise HTTPException(404, "Game not found")
    
    if game.status != "in_progress":
        raise HTTPException(400, "Game is finished")

    # 2. Validate Turn ownership
    # turn is 'white' or 'black'
    is_white_turn = (game.current_turn == 'white')
    
    # Check if current user is the player for this turn
    if is_white_turn:
        if game.player_white and game.player_white != current_player.id:
            raise HTTPException(403, "Not your turn (White)")
    else:
        if game.player_black and game.player_black != current_player.id:
            raise HTTPException(403, "Not your turn (Black)")

    # 3. Apply Move using python-chess
    is_chess960 = game.config.get("chess960", False)
    board = chess.Board(game.board_fen, chess960=is_chess960)
    
    try:
        move = chess.Move.from_uci(req.move_uci)
        if move not in board.legal_moves:
             raise ValueError("Illegal move")
    except ValueError:
        raise HTTPException(400, "Invalid UCI move or Illegal move")

    board.push(move)
    
    # 4. Check Game End
    new_status = "in_progress"
    if board.is_game_over():
        if board.is_checkmate():
            new_status = "checkmate" # Winner is the one who moved
        elif board.is_stalemate():
            new_status = "stalemate"
        elif board.is_insufficient_material():
            new_status = "draw"
        else:
            new_status = "draw" # 50-move rule, repetition, etc.
    elif board.can_claim_threefold_repetition():
        new_status = "draw"
    elif board.can_claim_fifty_moves():
        new_status = "draw"

    # 5. Update DB
    if not isinstance(game.config, dict):
        game.config = {}
    moves = game.config.get("moves", [])
    moves.append(req.move_uci)
    # Force update
    game.config = {**game.config, "moves": moves}
    flag_modified(game, "config")

    game.board_fen = board.fen()
    game.current_turn = "white" if board.turn == chess.WHITE else "black"
    game.status = new_status
    
    db.add(game)
    await db.commit()
    await db.refresh(game)

    # Calc evaluation
    eval_score = get_board_evaluation(game.board_fen)

    # 6. Publish to Redis
    try:
        await core_redis.redis_pool.xadd(
            f"chess:{game.id}",
            {
                "type": "move",
                "fen": game.board_fen,
                "by": "white" if is_white_turn else "black",
                "move_uci": req.move_uci,
                "status": game.status,
                "evaluation": str(eval_score),
                "is_check": str(board.is_check())
            }
        )
    except Exception as e:
        logger.error(f"Redis publish failed: {e}")
        
    # 7. AI Turn Logic
    # await process_ai_turns(game.id, db)
    background_tasks.add_task(process_ai_turns, game.id)
    
    # Return new state
    w_name = None
    b_name = None
    if game.player_white:
        p = await db.get(Player, game.player_white)
        w_name = p.name
    if game.player_black:
        p = await db.get(Player, game.player_black)
        b_name = p.name
        
    return ChessGameState(
        id=game.id,
        board_fen=game.board_fen,
        current_turn=game.current_turn,
        status=game.status,
        white_player_name=w_name,
        black_player_name=b_name,
        white_player_id=game.player_white,
        black_player_id=game.player_black,
        config=game.config,
        evaluation=eval_score,
        is_check=board.is_check()
    )
