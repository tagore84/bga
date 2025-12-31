from typing import Optional, List, Literal
import json
import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime

from app.db.deps import get_db
from app.models.wythoff.wythoff import WythoffGame
from app.models.player import Player, PlayerType
from app.models.game import Game
from app.routes.auth import get_current_player
import app.core.redis as core_redis
from app.core.ai_base import get_ai

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/wythoff", tags=["wythoff"])

# --- Schemas ---

class WythoffCreateGameRequest(BaseModel):
    game_name: str
    player1Type: Literal["human", "ai"]
    player1Id: int
    player2Type: Literal["human", "ai"]
    player2Id: int

class WythoffGameState(BaseModel):
    id: int
    board: List[int] # [pile1, pile2]
    current_turn: str
    status: str
    config: WythoffCreateGameRequest
    player_1_name: Optional[str] = None
    player_2_name: Optional[str] = None

class WythoffMoveRequest(BaseModel):
    type: Literal["standard", "diagonal"]
    pile_index: Optional[int] = None # Required for standard
    count: int

# --- Helper ---
def _evaluate_winner(board, current_turn):
    # If board is empty, current player TOOK the last object.
    # Normal Play: Last player to move WINS.
    # So if board is empty, the player who JUST moved (previous turn) won.
    # The 'current_turn' passed here is usually the NEXT player.
    # So if next player finds board empty, previous player won.
    if sum(board) == 0:
        # Previous player won.
        # If current_turn is '1', then '2' won.
        winner = "2" if current_turn == "1" else "1"
        return f"{winner}_won"
    return "in_progress"

# --- Endpoints ---

@router.get("/", response_model=List[WythoffGameState])
async def list_games(db: AsyncSession = Depends(get_db)):
    q = await db.execute(select(WythoffGame).where(WythoffGame.status == "in_progress"))
    games = q.scalars().all()
    
    out = []
    for g in games:
        p1 = await db.get(Player, g.player_1_id)
        p2 = await db.get(Player, g.player_2_id)
        out.append(WythoffGameState(
            id=g.id,
            board=g.board,
            current_turn=g.current_turn,
            status=g.status,
            config=WythoffCreateGameRequest(**g.config),
            player_1_name=p1.name if p1 else None,
            player_2_name=p2.name if p2 else None
        ))
    return out

@router.post("/", response_model=WythoffGameState)
async def create_game(
    req: WythoffCreateGameRequest,
    db: AsyncSession = Depends(get_db),
    current_player = Depends(get_current_player)
):
    result = await db.execute(select(Game).where(Game.name == "wythoff"))
    base_game = result.scalar_one_or_none()
    if not base_game:
        # Auto-create if missing (should be seeded though)
        pass 
        
    wythoff_game = WythoffGame(
        board=[9, 13], # Default starting piles? Or Random? Let's use something interesting.
        current_turn="1",
        status="in_progress",
        config=req.dict(),
        game_name="wythoff",
        game_id=base_game.id if base_game else 0,
        player_1_id=req.player1Id,
        player_2_id=req.player2Id,
        created_at=datetime.utcnow()
    )
    db.add(wythoff_game)
    await db.commit()
    await db.refresh(wythoff_game)
    
    # AI First Move Trigger
    if req.player1Type == "ai":
        p1 = await db.get(Player, req.player1Id)
        ai = get_ai(p1.name)
        if ai:
            move = ai.select_move({"board": wythoff_game.board})
            
            # Application of move
            board = list(wythoff_game.board)
            if move["type"] == "standard":
                board[move["pile_index"]] -= move["count"]
            else:
                board[0] -= move["count"]
                board[1] -= move["count"]
            
            status = _evaluate_winner(board, "2")
            wythoff_game.board = board
            wythoff_game.status = status
            wythoff_game.current_turn = "2" if status == "in_progress" else wythoff_game.current_turn
            
            db.add(wythoff_game)
            await db.commit()
            await db.refresh(wythoff_game)
            
            # Redis pub
            try:
                await core_redis.redis_pool.xadd(f"wythoff:{wythoff_game.id}", {
                    "type": "move",
                    "move_type": move["type"],
                    "count": str(move["count"]),
                    "pile_index": str(move.get("pile_index", -1)),
                    "by": "1",
                    "board": json.dumps(wythoff_game.board),
                    "status": wythoff_game.status
                })
            except Exception as e:
                logger.error(f"Redis error: {e}")

    p1 = await db.get(Player, req.player1Id)
    p2 = await db.get(Player, req.player2Id)
    
    return WythoffGameState(
        id=wythoff_game.id,
        board=wythoff_game.board,
        current_turn=wythoff_game.current_turn,
        status=wythoff_game.status,
        config=WythoffCreateGameRequest(**wythoff_game.config),
        player_1_name=p1.name if p1 else None,
        player_2_name=p2.name if p2 else None
    )

@router.get("/{game_id}", response_model=WythoffGameState)
async def get_game(game_id: int, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(WythoffGame).where(WythoffGame.id == game_id))
    g = res.scalar_one_or_none()
    if not g: raise HTTPException(404, "Game not found")
    
    p1 = await db.get(Player, g.player_1_id)
    p2 = await db.get(Player, g.player_2_id)
    
    return WythoffGameState(
        id=g.id,
        board=g.board,
        current_turn=g.current_turn,
        status=g.status,
        config=WythoffCreateGameRequest(**g.config),
        player_1_name=p1.name if p1 else None,
        player_2_name=p2.name if p2 else None
    )

@router.delete("/{game_id}")
async def delete_game(game_id: int, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(WythoffGame).where(WythoffGame.id == game_id))
    g = res.scalar_one_or_none()
    if not g: raise HTTPException(404, "Game not found")
    await db.delete(g)
    await db.commit()
    return {"detail": "Deleted"}

@router.post("/{game_id}/move", response_model=WythoffGameState)
async def make_move(
    game_id: int,
    move: WythoffMoveRequest,
    db: AsyncSession = Depends(get_db),
    current_player: Player = Depends(get_current_player)
):
    res = await db.execute(select(WythoffGame).where(WythoffGame.id == game_id))
    game = res.scalar_one_or_none()
    if not game: raise HTTPException(404, "Game not found")
    if game.status != "in_progress": raise HTTPException(400, "Game over")
    
    # Validate Turn
    if game.current_turn == "1" and game.player_1_id != current_player.id:
        raise HTTPException(403, "Not your turn")
    if game.current_turn == "2" and game.player_2_id != current_player.id:
        raise HTTPException(403, "Not your turn")
        
    # Apply Move
    board = list(game.board)
    if move.type == "standard":
        if move.pile_index is None or move.pile_index < 0 or move.pile_index > 1:
            raise HTTPException(400, "Invalid pile index")
        if move.count > board[move.pile_index] or move.count < 1:
            raise HTTPException(400, "Invalid count")
        board[move.pile_index] -= move.count
    elif move.type == "diagonal":
        if move.count < 1: raise HTTPException(400, "Invalid count")
        if board[0] < move.count or board[1] < move.count:
            raise HTTPException(400, "Not enough items for diagonal move")
        board[0] -= move.count
        board[1] -= move.count
        
    # Update State
    next_turn = "2" if game.current_turn == "1" else "1"
    status = _evaluate_winner(board, next_turn)
    
    game.board = board
    game.status = status
    game.current_turn = next_turn if status == "in_progress" else game.current_turn
    
    db.add(game)
    await db.commit()
    await db.refresh(game)
    
    # Redis
    try:
        await core_redis.redis_pool.xadd(f"wythoff:{game.id}", {
            "type": "move",
            "move_type": move.type,
            "count": str(move.count),
            "pile_index": str(move.pile_index if move.pile_index is not None else -1),
            "by": "1" if next_turn == "2" else "2",
            "board": json.dumps(game.board),
            "status": game.status
        })
    except Exception as e:
        logger.error(f"Redis err: {e}")
        
    # AI Move
    if (game.status == "in_progress" and 
       ((game.current_turn == "1" and game.config["player1Type"] == "ai") or
        (game.current_turn == "2" and game.config["player2Type"] == "ai"))
    ):
        p_id = game.player_1_id if game.current_turn == "1" else game.player_2_id
        p = await db.get(Player, p_id)
        ai = get_ai(p.name)
        if ai:
            ai_move = ai.select_move({"board": game.board})
            
            board = list(game.board)
            if ai_move["type"] == "standard":
                board[ai_move["pile_index"]] -= ai_move["count"]
            else:
                board[0] -= ai_move["count"]
                board[1] -= ai_move["count"]
            
            next_turn = "2" if game.current_turn == "1" else "1"
            status = _evaluate_winner(board, next_turn)
            
            prev_turn = game.current_turn
            game.board = board
            game.status = status
            game.current_turn = next_turn if status == "in_progress" else game.current_turn
            
            db.add(game)
            await db.commit()
            await db.refresh(game)
            
            try:
                await core_redis.redis_pool.xadd(f"wythoff:{game.id}", {
                    "type": "move",
                    "move_type": ai_move["type"],
                    "count": str(ai_move["count"]),
                    "pile_index": str(ai_move.get("pile_index", -1)),
                    "by": prev_turn,
                    "board": json.dumps(game.board),
                    "status": game.status
                })
            except Exception as e:
                logger.error(f"Redis err: {e}")

    p1 = await db.get(Player, game.player_1_id)
    p2 = await db.get(Player, game.player_2_id)

    return WythoffGameState(
        id=game.id,
        board=game.board,
        current_turn=game.current_turn,
        status=game.status,
        config=WythoffCreateGameRequest(**game.config),
        player_1_name=p1.name if p1 else None,
        player_2_name=p2.name if p2 else None
    )
