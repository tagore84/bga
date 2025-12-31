# backend/app/routes/nim/nim.py
from typing import Optional, List, Literal
import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime
from app.db.deps import get_db
from app.models.nim.nim import NimGame
from app.routes.auth import get_current_player
from app.models.player import Player
from app.models.player import PlayerType
from app.models.game import Game
import app.core.redis as core_redis
import logging

from app.core.ai_base import get_ai

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/nim", tags=["nim"])

# Listen for Redis events? Not needed for basic REST, but useful for sockets later.

# --- Pydantic Schemas ---

class NimCreateGameRequest(BaseModel):
    game_name:    str
    player1Type:  Literal["human", "ai"]
    player1Id:    int
    player2Type:  Literal["human", "ai"]
    player2Id:    int

class NimGameState(BaseModel):
    id:           int
    board:        List[int]
    current_turn: str # "1" or "2"
    status:       str
    config:       NimCreateGameRequest
    player_1_name: Optional[str] = None
    player_2_name: Optional[str] = None

class NimMoveRequest(BaseModel):
    pile_index: int
    count:      int

class NimParticipantOut(BaseModel):
    symbol: str # "1" or "2"
    player_id: int
    player_type: PlayerType
    name: Optional[str]

# --- Helpers ---

def _evaluate_board_status(board, current_turn):
    """
    Misere Nim: 
    - End condition: Sum of piles is 0.
    - If sum is 0, the player whose turn it WAS (who just moved) LOSES.
    - BUT wait, if piles are empty, the game is over.
    - The rule is: "The player who takes the last object loses."
    - So if I make a move and the board becomes empty, I TOOK the last object. I LOSE.
    - So if board sum is 0, the player who just moved (previous turn) lost.
    - The player who is currently set to move (next turn) WON.
    """
    total_items = sum(board)
    if total_items == 0:
        # Game over.
        # Who won? 
        # The player attempting to move now implies it's their turn.
        # But this function is usually called AFTER a move.
        # If I moved and left 0, I lose.
        # So "current_turn" (next player) WINS.
        
        # NOTE: logic in other games (TicTacToe) returns "X_won" or "O_won".
        # If current_turn is '2' (because we switched after move), and board is empty:
        # Player 1 moved last -> Board empty -> Player 1 loses -> Player 2 wins.
        # So '2_won'.
        return f"{current_turn}_won"
        
    return "in_progress"

# --- Endpoints ---

@router.get("/", response_model=List[NimGameState])
async def list_games(db: AsyncSession = Depends(get_db)):
    q = await db.execute(select(NimGame).where(NimGame.status=="in_progress"))
    games = q.scalars().all()
    
    out = []
    for g in games:
        # Get player names
        p1_name = None
        p2_name = None
        if g.player_1_id:
            p1 = await db.get(Player, g.player_1_id)
            p1_name = p1.name if p1 else "Unknown"
        if g.player_2_id:
            p2 = await db.get(Player, g.player_2_id)
            p2_name = p2.name if p2 else "Unknown"
            
        out.append(NimGameState(
            id=g.id,
            board=g.board,
            current_turn=g.current_turn,
            status=g.status,
            config=NimCreateGameRequest(**g.config),
            player_1_name=p1_name,
            player_2_name=p2_name
        ))
    return out

@router.post("/", response_model=NimGameState)
async def create_game(
    req: NimCreateGameRequest,
    db: AsyncSession = Depends(get_db),
    current_player = Depends(get_current_player),
):
    # 1. Get Game Definition
    result = await db.execute(select(Game).where(Game.name == "nim"))
    base_game = result.scalar_one_or_none()
    if base_game is None:
        raise HTTPException(status_code=500, detail="Game definition 'nim' not found")
        
    # 2. Create Game Instance
    nim_game = NimGame(
        board=[1, 3, 5, 7],
        current_turn="1",
        status="in_progress",
        config=req.dict(),
        game_name="nim",
        game_id=base_game.id,
        player_1_id=req.player1Id,
        player_2_id=req.player2Id,
        created_at=datetime.utcnow()
    )
    db.add(nim_game)
    await db.commit()
    await db.refresh(nim_game)
    
    # 3. Publish Event
    try:
        await core_redis.redis_pool.xadd(
            f"nim:{nim_game.id}",
            {"type": "create", "board": json.dumps(nim_game.board)}
        )
    except Exception as e:
        logger.error(f"Failed to publish create event to Redis: {e}")
        
    # 4. Resolve Names
    p1 = await db.get(Player, req.player1Id)
    p2 = await db.get(Player, req.player2Id)
    
    # 5. Trigger AI Move if Player 1 is AI
    # (Since Nim starts with Player 1)
    if req.player1Type == "ai":
        p_ai = p1
        ai = get_ai(p_ai.name)
        if ai:
            # Calculate AI Move
            ai_move = ai.select_move({
                "board": nim_game.board,
                "current_turn": nim_game.current_turn
            })
            
            # Execute Move
            board = list(nim_game.board)
            board[ai_move["pile_index"]] -= ai_move["count"]
            
            # Evaluator for after move (it becomes Player 2's turn)
            status_val = _evaluate_board_status(board, "2")
            
            # Update Game
            nim_game.board = board
            nim_game.status = status_val
            nim_game.current_turn = "2" if status_val == "in_progress" else nim_game.current_turn
            
            db.add(nim_game)
            await db.commit()
            await db.refresh(nim_game)
            
            # Publish AI Move
            try:
                await core_redis.redis_pool.xadd(
                    f"nim:{nim_game.id}",
                    {
                        "type": "move",
                        "pile_index": str(ai_move["pile_index"]),
                        "count": str(ai_move["count"]),
                        "by": "1", # Player 1 moved
                        "board": json.dumps(nim_game.board),
                        "status": nim_game.status
                    }
                )
            except Exception as e:
                logger.error(f"Failed to publish AI move on create: {e}")

    return NimGameState(
        id=nim_game.id,
        board=nim_game.board,
        current_turn=nim_game.current_turn,
        status=nim_game.status,
        config=NimCreateGameRequest(**nim_game.config),
        player_1_name=p1.name if p1 else None,
        player_2_name=p2.name if p2 else None
    )

@router.get("/{game_id}", response_model=NimGameState)
async def get_game(game_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(NimGame).where(NimGame.id == game_id))
    g = result.scalar_one_or_none()
    if not g:
        raise HTTPException(404, "Game not found")
        
    p1 = await db.get(Player, g.player_1_id)
    p2 = await db.get(Player, g.player_2_id)
    
    return NimGameState(
        id=g.id,
        board=g.board,
        current_turn=g.current_turn,
        status=g.status,
        config=NimCreateGameRequest(**g.config),
        player_1_name=p1.name if p1 else None,
        player_2_name=p2.name if p2 else None
    )

@router.post("/{game_id}/move", response_model=NimGameState)
async def make_move(
    game_id: int,
    move: NimMoveRequest,
    db: AsyncSession = Depends(get_db),
    current_player: Player = Depends(get_current_player)
):
    result = await db.execute(select(NimGame).where(NimGame.id == game_id))
    game = result.scalar_one_or_none()
    if not game:
        raise HTTPException(404, "Game not found")
    if game.status != "in_progress":
        raise HTTPException(400, "Game already finished")
        
    # Validation: Turn
    if game.current_turn == "1":
        if game.player_1_id and game.player_1_id != current_player.id:
            raise HTTPException(403, "Not your turn (Player 1)")
    elif game.current_turn == "2":
        if game.player_2_id and game.player_2_id != current_player.id:
            raise HTTPException(403, "Not your turn (Player 2)")
            
    # Validation: Move
    if not (0 <= move.pile_index < len(game.board)):
        raise HTTPException(400, "Invalid pile index")
    if move.count <= 0:
        raise HTTPException(400, "Must remove at least 1 item")
    if game.board[move.pile_index] < move.count:
        raise HTTPException(400, "Not enough items in pile")
        
    # --- Execute Human Move ---
    board = list(game.board)
    board[move.pile_index] -= move.count
    
    next_turn = "2" if game.current_turn == "1" else "1"
    
    # Check status (pass next_turn because if empty, next_turn wins)
    status_val = _evaluate_board_status(board, next_turn)
    
    game.board = board
    game.status = status_val
    game.current_turn = next_turn if status_val == "in_progress" else game.current_turn
    
    db.add(game)
    await db.commit()
    await db.refresh(game)
    
    # Publish Human Move
    try:
        await core_redis.redis_pool.xadd(
            f"nim:{game.id}",
            {
                "type": "move",
                "pile_index": str(move.pile_index),
                "count": str(move.count),
                "by": game.current_turn if status_val != "in_progress" else ("1" if next_turn == "2" else "2"), 
                # "by" should represent WHO moved. 
                # If game continues, next_turn is new player. So prev player is who moved.
                # If game ended, currents_turn is WINNER. So LOSER moved.
                # Let's simplify: Just send "move" event. Frontend can deduce.
                # But consistency helps.
                "board": json.dumps(game.board),
                "status": game.status
            }
        )
    except Exception as e:
        logger.error(f"Failed to publish move: {e}")
        
    # --- AI Move if applicable ---
    if game.status == "in_progress" and (
        (game.current_turn == "1" and game.config["player1Type"] == "ai") or
        (game.current_turn == "2" and game.config["player2Type"] == "ai")
    ):
        # AI Turn
        player_id = game.player_1_id if game.current_turn == "1" else game.player_2_id
        p_ai = await db.get(Player, player_id)
        if not p_ai: 
             # Should not happen
             logger.error("AI Player not found in DB")
             return game
             
        ai = get_ai(p_ai.name)
        if not ai:
             logger.error(f"AI Strategy not found for {p_ai.name}")
             return game
             
        ai_move = ai.select_move({
            "board": game.board,
            "current_turn": game.current_turn
        })
        # expect {"pile_index": int, "count": int}
        
        board = list(game.board)
        board[ai_move["pile_index"]] -= ai_move["count"]
        
        next_turn = "2" if game.current_turn == "1" else "1"
        status_val = _evaluate_board_status(board, next_turn)
        
        prev_turn_ai = game.current_turn
        
        game.board = board
        game.status = status_val
        game.current_turn = next_turn if status_val == "in_progress" else game.current_turn
        
        db.add(game)
        await db.commit()
        await db.refresh(game)
        
        # Publish AI Move
        try:
            await core_redis.redis_pool.xadd(
                f"nim:{game.id}",
                {
                    "type": "move",
                    "pile_index": str(ai_move["pile_index"]),
                    "count": str(ai_move["count"]),
                    "by": prev_turn_ai,
                    "board": json.dumps(game.board),
                    "status": game.status
                }
            )
        except Exception as e:
            logger.error(f"Failed to publish AI move: {e}")

    # Re-fetch names for response
    p1 = await db.get(Player, game.player_1_id)
    p2 = await db.get(Player, game.player_2_id)

    return NimGameState(
        id=game.id,
        board=game.board,
        current_turn=game.current_turn,
        status=game.status,
        config=NimCreateGameRequest(**game.config),
        player_1_name=p1.name if p1 else None,
        player_2_name=p2.name if p2 else None
    )

@router.delete("/{game_id}")
async def delete_game(game_id: int, db: AsyncSession = Depends(get_db), current_player: Player = Depends(get_current_player)):
    result = await db.execute(select(NimGame).where(NimGame.id == game_id))
    game = result.scalar_one_or_none()
    
    if not game:
        raise HTTPException(404, "Game not found")
        
    # Optional: Check permissions (only players involved or admin?)
    # For now, allow any authenticated user to delete any game to match other games' behavior/MVP.
    
    await db.delete(game)
    await db.commit()
    
    return {"detail": f"Game {game_id} deleted"}
