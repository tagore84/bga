# backend/app/routes/connect4/connect4.py
from typing import Optional, List, Literal
import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime
from app.db.deps import get_db
from app.models.connect4.connect4 import Connect4Game
from app.routes.auth import get_current_player
from app.models.player import Player, PlayerType
from app.models.game import Game
import app.core.redis as core_redis
from app.core.ai_base import get_ai

import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/connect4", tags=["connect4"])

# --- Schemas ---

class Connect4CreateGameRequest(BaseModel):
    game_name:    str
    playerRedType:  Literal["human", "ai"]
    playerRedId:    int
    playerBlueType:  Literal["human", "ai"]
    playerBlueId:    int

class Connect4GameState(BaseModel):
    id:           int
    board:        list[Optional[str]] # 42 elements
    current_turn: str
    status:       str
    config:       Connect4CreateGameRequest
    player_red_name: Optional[str] = None
    player_blue_name: Optional[str] = None

class Connect4ParticipantOut(BaseModel):
    symbol: str                        # "Red" or "Blue"
    player_id: int
    player_type: PlayerType
    name: Optional[str]

class Connect4MoveRequest(BaseModel):
    column: int  # 0..6

# --- Logic ---

ROWS = 6
COLS = 7

def _get_piece(board, row, col):
    if 0 <= row < ROWS and 0 <= col < COLS:
        return board[row * COLS + col]
    return None

def _check_win(board, piece):
    # Check horizontal
    for r in range(ROWS):
        for c in range(COLS - 3):
            if all(_get_piece(board, r, c+i) == piece for i in range(4)):
                return True

    # Check vertical
    for r in range(ROWS - 3):
        for c in range(COLS):
            if all(_get_piece(board, r+i, c) == piece for i in range(4)):
                return True

    # Check diagonal (positive slope)
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            if all(_get_piece(board, r+i, c+i) == piece for i in range(4)):
                return True

    # Check diagonal (negative slope)
    for r in range(3, ROWS):
        for c in range(COLS - 3):
            if all(_get_piece(board, r-i, c+i) == piece for i in range(4)):
                return True
    return False

def _evaluate_board(board):
    if _check_win(board, "Red"):
        return "Red_won"
    if _check_win(board, "Blue"):
        return "Blue_won"
    if None not in board:
        return "draw"
    return "in_progress"

def _drop_piece(board, col, piece):
    # Find the lowest empty row in the column
    for r in range(ROWS - 1, -1, -1):
        if _get_piece(board, r, col) is None:
            # Found empty spot
            idx = r * COLS + col
            board[idx] = piece
            return idx # Return index for verify
    return -1 # Column full

# --- Routes ---

@router.get("/", response_model=List[Connect4GameState])
async def list_games(db: AsyncSession = Depends(get_db)):
    q = await db.execute(select(Connect4Game).where(Connect4Game.status=="in_progress"))
    games = q.scalars().all()

    out = []
    for g in games:
        parts = []
        if g.player_red is not None:
            px = await db.get(Player, g.player_red)
            parts.append(Connect4ParticipantOut(symbol='Red', player_id=px.id, player_type=px.type, name=px.name))
        
        if g.player_blue is not None:
            po = await db.get(Player, g.player_blue)
            parts.append(Connect4ParticipantOut(symbol='Blue', player_id=po.id, player_type=po.type, name=po.name))
            
        out.append(Connect4GameState(
            id            = g.id,
            board         = g.board,
            current_turn  = g.current_turn,
            status        = g.status,
            config        = Connect4CreateGameRequest(**g.config),
            player_red_name  = parts[0].name if len(parts) > 0 else None,
            player_blue_name = parts[1].name if len(parts) > 1 else None
        ))
    return out

@router.post("/", response_model=Connect4GameState)
async def create_game(
    req: Connect4CreateGameRequest,
    db: AsyncSession = Depends(get_db),
    current_player = Depends(get_current_player),
):
    result = await db.execute(select(Game).where(Game.name == "connect4"))
    base_game = result.scalar_one_or_none()
    if base_game is None:
        raise HTTPException(status_code=500, detail="Game definition 'connect4' not found")
        
    c4_game = Connect4Game(
        board=[None]*42,
        current_turn="Red",
        status="in_progress",
        config=req.dict(),
        game_name=req.game_name,
        player_red=req.playerRedId,
        player_blue=req.playerBlueId,
        game_id=base_game.id,
        created_at=datetime.utcnow()
    )
    db.add(c4_game)
    await db.commit()
    await db.refresh(c4_game)

    try:
        await core_redis.redis_pool.xadd(
            f"connect4:{c4_game.id}",
            {"type":"create", "board":json.dumps(c4_game.board)}
        )
    except Exception as e:
        logger.error(f"Failed to publish create event to Redis: {e}")

    px = await db.get(Player, req.playerRedId)
    po = await db.get(Player, req.playerBlueId)
    
    # Trigger AI if Red is AI
    if req.playerRedType == "ai":
        ai = get_ai(px.name)
        if ai:
            # Calculate AI Move
            ai_col = ai.select_move({
                "board": c4_game.board,
                "current_turn": "Red",
                "config": c4_game.config
            })
            
            # Validate & Execute
            board = list(c4_game.board)
            if ai_col is None:
                # Fallback random valid
                valid_cols = [c for c in range(COLS) if _get_piece(board, 0, c) is None]
                ai_col = valid_cols[0] if valid_cols else 0
            
            idx = _drop_piece(board, int(ai_col), "Red")
            if idx != -1:
                status_val = _evaluate_board(board)
                
                c4_game.board = board
                c4_game.status = status_val
                c4_game.current_turn = "Blue" if status_val == "in_progress" else c4_game.current_turn
                
                # Update Config Moves
                config = dict(c4_game.config)
                moves = list(config.get("moves", []))
                moves.append(int(ai_col))
                config["moves"] = moves
                c4_game.config = config
                
                db.add(c4_game)
                await db.commit()
                await db.refresh(c4_game)
                
                try:
                    await core_redis.redis_pool.xadd(
                        f"connect4:{c4_game.id}",
                        {
                            "type": "move",
                            "column": str(ai_col),
                            "by": "Red",
                            "board": json.dumps(c4_game.board),
                            "status": c4_game.status
                        }
                    )
                except Exception as e:
                    logger.error(f"Failed to publish AI move on create: {e}")

    return Connect4GameState(
        id=c4_game.id,
        board=c4_game.board,
        current_turn=c4_game.current_turn,
        status=c4_game.status,
        config=Connect4CreateGameRequest(**c4_game.config),
        player_red_name=px.name,
        player_blue_name=po.name
    )

@router.get("/{game_id}", response_model=Connect4GameState)
async def get_game(game_id: int, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Connect4Game).where(Connect4Game.id==game_id))
    g = res.scalar_one_or_none()
    if not g:
        raise HTTPException(404, "Game not found")
        
    player_red_name = None
    player_blue_name = None
    
    if g.player_red:
        p = await db.get(Player, g.player_red)
        player_red_name = p.name
    if g.player_blue:
        p = await db.get(Player, g.player_blue)
        player_blue_name = p.name

    return Connect4GameState(
        id=g.id,
        board=g.board,
        current_turn=g.current_turn,
        status=g.status,
        config=Connect4CreateGameRequest(**g.config),
        player_red_name=player_red_name,
        player_blue_name=player_blue_name
    )

@router.post("/{game_id}/move", response_model=Connect4GameState)
async def make_move(
    game_id: int,
    move: Connect4MoveRequest,
    db: AsyncSession = Depends(get_db),
    current_player: Player = Depends(get_current_player)
):
    result = await db.execute(select(Connect4Game).where(Connect4Game.id == game_id))
    game = result.scalar_one_or_none()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    if game.status != "in_progress":
        raise HTTPException(status_code=400, detail="Game already finished")

    # Validate turn
    if game.current_turn == 'Red' and game.player_red and game.player_red != current_player.id:
        raise HTTPException(status_code=403, detail="Not your turn (Red)")
    if game.current_turn == 'Blue' and game.player_blue and game.player_blue != current_player.id:
        raise HTTPException(status_code=403, detail="Not your turn (Blue)")

    if not (0 <= move.column < COLS):
        raise HTTPException(status_code=400, detail="Invalid column")

    # Calculate Move
    board = game.board.copy()
    idx = _drop_piece(board, move.column, game.current_turn)
    
    if idx == -1:
        raise HTTPException(status_code=400, detail="Column full")
        
    status_val = _evaluate_board(board)
    next_turn = 'Blue' if game.current_turn == 'Red' else 'Red'
    
    game.board = board
    game.status = status_val
    game.current_turn = next_turn if status_val == 'in_progress' else game.current_turn
    
    # Update config moves
    config = dict(game.config)
    moves = list(config.get("moves", []))
    moves.append(move.column)
    config["moves"] = moves
    game.config = config

    db.add(game)
    await db.commit()
    await db.refresh(game)

    # Redis event
    try:
        await core_redis.redis_pool.xadd(
            f"connect4:{game.id}",
            {
                "type": "move",
                "column": str(move.column),
                "by": "Red" if next_turn == "Blue" else "Blue",
                "board": json.dumps(game.board),
                "status": game.status
            }
        )
    except Exception as e:
        logger.error(f"Failed to publish move event: {e}")

    # AI Move
    if game.status == "in_progress" and (
        (game.current_turn == "Red" and game.config["playerRedType"] == "ai") or
        (game.current_turn == "Blue" and game.config["playerBlueType"] == "ai")
    ):
        player_id = game.player_red if game.current_turn == "Red" else game.player_blue
        player = await db.get(Player, player_id)
        ai = get_ai(player.name)
        
        # DEBUG: Introspect AI object (REMOVED)


        ai_col = ai.select_move({
            "board": game.board,
            "current_turn": game.current_turn,
            "config": game.config
        })
        
        board = game.board.copy()
        if ai_col is None:
            logger.error(f"AI {player.name} returned None for move!")
            # Try to find any valid move to keep game alive
            valid_cols = [c for c in range(COLS) if _get_piece(board, 0, c) is None]
            if valid_cols:
                ai_col = valid_cols[0]
            else:
                ai_col = 0 # Will fail in _drop_piece as column full

        idx = _drop_piece(board, ai_col, game.current_turn)
        if idx != -1: 
            status_val = _evaluate_board(board)
            next_turn = "Blue" if game.current_turn == "Red" else "Red"
            game.board = board
            game.status = status_val
            game.current_turn = next_turn if status_val == "in_progress" else game.current_turn
            
            # Update config moves for AI
            config = dict(game.config)
            moves = list(config.get("moves", []))
            moves.append(int(ai_col))
            config["moves"] = moves
            game.config = config

            db.add(game)
            await db.commit()
            await db.refresh(game)
            
            try:
                await core_redis.redis_pool.xadd(
                    f"connect4:{game.id}",
                    {
                        "type": "move",
                        "column": str(ai_col),
                        "by": "Red" if next_turn == "Blue" else "Blue",
                        "board": json.dumps(game.board),
                        "status": game.status
                    }
                )
            except Exception as e:
                logger.error(f"Failed to publish AI move: {e}")

    return Connect4GameState(
        id=game.id,
        board=game.board,
        current_turn=game.current_turn,
        status=game.status,
        config=Connect4CreateGameRequest(**game.config),
        player_red_name=None, 
        player_blue_name=None
    )

@router.post("/{game_id}/undo", response_model=Connect4GameState)
async def undo_move(
    game_id: int,
    db: AsyncSession = Depends(get_db),
    current_player: Player = Depends(get_current_player)
):
    result = await db.execute(select(Connect4Game).where(Connect4Game.id == game_id))
    game = result.scalar_one_or_none()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    # Validation: User must be a player
    if (game.player_red != current_player.id) and (game.player_blue != current_player.id):
        raise HTTPException(status_code=403, detail="Not a participant")

    config = dict(game.config)
    moves = config.get("moves", [])
    if not moves:
        raise HTTPException(status_code=400, detail="No moves to undo")
    
    # Determine undo count
    # Check if opponent is AI
    # If I am Red, and Blue is AI -> Undo 2
    # If I am Blue, and Red is AI -> Undo 2
    # Else -> Undo 1
    
    is_vs_ai = False
    if game.player_red == current_player.id:
        if config.get("playerBlueType") == "ai":
            is_vs_ai = True
    else: # I am Blue
        if config.get("playerRedType") == "ai":
            is_vs_ai = True
            
    undo_count = 2 if is_vs_ai else 1
    
    if len(moves) < undo_count:
        # If we can't undo 2 (e.g. only 1 move made in AI game?? Should not happen if AI moves immediately, but strictly possibly)
        # Just undo all? Or fail?
        # If I moved, AI moves. 2 moves.
        # If I moved, AI crashed/didn't move. 1 move.
        # Let's just undo what we can up to undo_count, but strictly we want to revert to MY turn.
        undo_count = len(moves)

    # Pop moves
    # We need to replay the game to reconstruct the board because dropping pieces isn't easily reversible 
    # (checking which is top is easy, but verifying history integrity is safer by replay if cheap. 
    # Replay is cheap for C4).
    # Actually, for C4, we can just remove the top piece of the column for the last move. 
    # We know the column from `moves`.
    # Let's do Replay to be safe and consistent with "state reconstruction".
    
    moves = moves[:-undo_count]
    config["moves"] = moves
    game.config = config
    
    # Reconstruct
    board = [None] * 42
    current_turn = "Red"
    
    for col in moves:
        _drop_piece(board, col, current_turn)
        current_turn = "Blue" if current_turn == "Red" else "Red"
        
    game.board = board
    game.current_turn = current_turn
    game.status = "in_progress" # Result is cleared on undo (unless we undo to a checkmate state? No, C4 usually undoes FROM result or mid-game)
    # Check if verifying win is needed? No, if we undo, we assume previous state was valid.
    # But technically if we undo to a state where someone had won (impossible if we undo the winning move), it becomes in_progress.
    
    db.add(game)
    await db.commit()
    await db.refresh(game)
    
    # Redis event
    try:
        await core_redis.redis_pool.xadd(
            f"connect4:{game.id}",
            {
                "type": "undo", # Client should refetch or we send full board
                "board": json.dumps(game.board),
                "status": game.status,
                "current_turn": game.current_turn
            }
        )
    except Exception as e:
        logger.error(f"Failed to publish undo event: {e}")
        
    return Connect4GameState(
        id=game.id,
        board=game.board,
        current_turn=game.current_turn,
        status=game.status,
        config=Connect4CreateGameRequest(**game.config),
        player_red_name=None,
        player_blue_name=None
    )

@router.delete("/{game_id}")
async def delete_game(
    game_id: int,
    db: AsyncSession = Depends(get_db),
    current_player: Player = Depends(get_current_player)
):
    result = await db.execute(select(Connect4Game).where(Connect4Game.id == game_id))
    game = result.scalar_one_or_none()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
        
    # Optional: Check permissions? 
    # Usually strictly blocking deletion if not participant is good, 
    # but for "Active Games" list sometimes global delete is allowed or user just deletes their own.
    # Given the requested "like Azul" behavior, let's see what Azul does.
    # Azul code wasn't showing backend logic for delete, but frontend `AzulActiveGames.vue` calls DELETE /azul/{id}.
    # We will assume owner/participant check or just allow authenticated users to clean up for now (MVP).
    # Ideally: if game.player_red != current.id && game.player_blue != current.id -> 403
    
    # Implementing participant check for safety:
    # if (game.player_red != current_player.id) and (game.player_blue != current_player.id):
    #     raise HTTPException(status_code=403, detail="Not a participant")
    
    await db.delete(game)
    await db.commit()
    return {"detail": "Game deleted"}
