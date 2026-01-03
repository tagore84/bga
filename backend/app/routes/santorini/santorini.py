from typing import Optional, List, Literal, Tuple
import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime
from app.db.deps import get_db
from app.models.santorini.santorini import SantoriniGame
from app.core.santorini.logic import SantoriniLogic
from app.routes.auth import get_current_player
from app.models.player import Player, PlayerType
from app.models.game import Game
import app.core.redis as core_redis

import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/santorini", tags=["santorini"])

# --- Schemas ---

class SantoriniCreateGameRequest(BaseModel):
    game_name:    str
    playerP1Type:  Literal["human", "ai"]
    playerP1Id:    int
    playerP2Type:  Literal["human", "ai"]
    playerP2Id:    int

class SantoriniGameState(BaseModel):
    id:           int
    board:        List[List[dict]] # 5x5 grid of {level: int, worker: str|None}
    current_turn: str
    status:       str
    config:       SantoriniCreateGameRequest
    player_p1_name: Optional[str] = None
    player_p2_name: Optional[str] = None

class SantoriniMoveRequest(BaseModel):
    worker_start: Optional[Tuple[int, int]] = None
    move_to:      Tuple[int, int]
    build_at:     Optional[Tuple[int, int]] = None
    move_type:    Literal["move_build", "place_worker"] = "move_build"

# --- Routes ---

async def _process_ai_turn(game: SantoriniGame, db: AsyncSession):
    """
    Checks if the current turn belongs to an AI player and processes the move if so.
    """
    if game.status != 'in_progress':
        return

    # Loop to handle consecutive AI turns
    logger.info(f"Starting AI turn processing. Status: {game.status}, Turn: {game.current_turn}")
    
    while True:
        is_p1_turn = (game.current_turn == 'p1')
        p1_type = game.config.get('playerP1Type')
        p2_type = game.config.get('playerP2Type')
        
        logger.info(f"Checking turn. P1Type: {p1_type}, P2Type: {p2_type}, Current: {game.current_turn}")
        
        is_ai_turn = (is_p1_turn and p1_type == 'ai') or ((not is_p1_turn) and p2_type == 'ai')
        
        if not is_ai_turn or game.status != 'in_progress':
            logger.info("Not AI turn or game ended. Stopping loop.")
            break
        
        # 1. Get AI Player
        current_player_id = game.player_p1 if is_p1_turn else game.player_p2
        # We need to fetch player from DB
        player_res = await db.execute(select(Player).where(Player.id == current_player_id))
        ai_player = player_res.scalar_one_or_none()
        
        if ai_player:
            logger.info(f"AI Player found: {ai_player.name}")
            from app.core.ai_base import get_ai
            ai_agent = get_ai(ai_player.name)
            
            if ai_agent:
                logger.info(f"AI Agent loaded: {ai_agent}")
                # 2. Select Move
                try:
                    ai_move = ai_agent.select_move({
                        "board": game.board,
                        "current_turn": game.current_turn,
                        "config": game.config
                    })
                    logger.info(f"AI selected move: {ai_move}")
                except Exception as e:
                    logger.error(f"Error selecting AI move: {e}")
                    break
                
                if ai_move:
                    # 3. Apply Move
                    ai_mover = game.current_turn
                    # Refresh logic because validation/application is static but we use game state
                    try:
                        new_board, status = SantoriniLogic.apply_move(game.board, ai_move, ai_mover)
                        logger.info(f"Move applied. New status: {status}")
                    except Exception as e:
                        logger.error(f"Error applying AI move: {e}")
                        break

                    game.board = new_board
                    game.status = status
                    
                    previous_ai_turn = ai_mover
                    
                    if game.status == 'in_progress':
                        next_turn = 'p2' if game.current_turn == 'p1' else 'p1'
                        
                        # Check if we should switch turn (Placement Phase Logic for AI)
                        if ai_move.get('move_type') == 'place_worker':
                            # Check how many workers current player has
                            worker_count = 0
                            for r in range(5):
                                for c in range(5):
                                    if game.board[r][c]['worker'] == game.current_turn:
                                        worker_count += 1
                            
                            logger.info(f"Placement phase. Worker count for {game.current_turn}: {worker_count}")
                            
                            # If < 2 workers, they need to place another one. Turn stays.
                            if worker_count < 2:
                                next_turn = game.current_turn

                        if SantoriniLogic.check_loss(game.board, next_turn):
                            game.status = f"{game.current_turn}_won"
                        else:
                            game.current_turn = next_turn
                        
                        logger.info(f"Next turn set to: {game.current_turn}")
                            
                    db.add(game)
                    await db.commit()
                    await db.refresh(game)
                    
                    # 4. Redis Event for AI
                    try:
                        await core_redis.redis_pool.xadd(
                            f"santorini:{game.id}",
                            {
                                "type": "move",
                                "move": json.dumps(ai_move),
                                "by": previous_ai_turn,
                                "board": json.dumps(game.board),
                                "status": game.status,
                                "current_turn": game.current_turn
                            }
                        )
                    except Exception as e:
                        logger.error(f"Failed to publish AI move event: {e}")
                else:
                    # AI returned no move? Stop loop to avoid infinite spin
                    logger.warning("AI returned NO move. Breaking.")
                    break
            else:
                 logger.error(f"AI Agent not found for name: {ai_player.name}")
                 break
        else:
            logger.error("AI Player object not found in DB")
            break



@router.get("/", response_model=List[SantoriniGameState])
async def list_games(db: AsyncSession = Depends(get_db)):
    q = await db.execute(select(SantoriniGame).where(SantoriniGame.status=="in_progress"))
    games = q.scalars().all()

    out = []
    for g in games:
        # Fetch player names (could be optimized with join)
        p1_name = None
        p2_name = None
        if g.player_p1:
            p = await db.get(Player, g.player_p1)
            if p: p1_name = p.name
        if g.player_p2:
            p = await db.get(Player, g.player_p2)
            if p: p2_name = p.name
            
        out.append(SantoriniGameState(
            id            = g.id,
            board         = g.board,
            current_turn  = g.current_turn,
            status        = g.status,
            config        = SantoriniCreateGameRequest(**g.config),
            player_p1_name  = p1_name,
            player_p2_name = p2_name
        ))
    return out

@router.post("/", response_model=SantoriniGameState)
async def create_game(
    req: SantoriniCreateGameRequest,
    db: AsyncSession = Depends(get_db),
    current_player: Player = Depends(get_current_player),
):
    result = await db.execute(select(Game).where(Game.name == "santorini"))
    base_game = result.scalar_one_or_none()
    
    # If base game doesn't exist (e.g. not seeded), we should handle it. 
    # For now assume seeded or use ID 7 as default in model if logic fails.
    game_id_fk = base_game.id if base_game else 7

    board = SantoriniLogic.initialize_board()
    
    # Initial Worker Placement (Simplified: Fixed positions for MVP or Random?)
    # Rules say players place them. For this MVP, let's place them reasonably.
    # Initial Worker Placement
    # Removed automatic placement. Players must place them manually.
    # board[0][0]['worker'] = 'p1'
    # board[4][4]['worker'] = 'p1'
    # board[0][4]['worker'] = 'p2'
    # board[4][0]['worker'] = 'p2'

    new_game = SantoriniGame(
        board=board,
        current_turn="p1",
        status="in_progress",
        config=req.dict(),
        game_id=game_id_fk,
        player_p1=req.playerP1Id,
        player_p2=req.playerP2Id,
        created_at=datetime.utcnow()
    )
    db.add(new_game)
    await db.commit()
    await db.refresh(new_game)

    try:
        await core_redis.redis_pool.xadd(
            f"santorini:{new_game.id}",
            {"type":"create", "board":json.dumps(new_game.board)}
        )
    except Exception as e:
        logger.error(f"Failed to publish create event to Redis: {e}")

    # AI Turn Trigger
    await _process_ai_turn(new_game, db)

    # Fetch names
    p1 = await db.get(Player, req.playerP1Id)
    p2 = await db.get(Player, req.playerP2Id)

    return SantoriniGameState(
        id=new_game.id,
        board=new_game.board,
        current_turn=new_game.current_turn,
        status=new_game.status,
        config=SantoriniCreateGameRequest(**new_game.config),
        player_p1_name=p1.name,
        player_p2_name=p2.name
    )

@router.get("/{game_id}", response_model=SantoriniGameState)
async def get_game(game_id: int, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(SantoriniGame).where(SantoriniGame.id==game_id))
    g = res.scalar_one_or_none()
    if not g:
        raise HTTPException(404, "Game not found")
        
    p1_name = None
    p2_name = None
    if g.player_p1:
        p = await db.get(Player, g.player_p1)
        if p: p1_name = p.name
    if g.player_p2:
        p = await db.get(Player, g.player_p2)
        if p: p2_name = p.name

    return SantoriniGameState(
        id=g.id,
        board=g.board,
        current_turn=g.current_turn,
        status=g.status,
        config=SantoriniCreateGameRequest(**g.config),
        player_p1_name=p1_name,
        player_p2_name=p2_name
    )

@router.post("/{game_id}/move", response_model=SantoriniGameState)
async def make_move(
    game_id: int,
    move: SantoriniMoveRequest,
    db: AsyncSession = Depends(get_db),
    current_player: Player = Depends(get_current_player)
):
    result = await db.execute(select(SantoriniGame).where(SantoriniGame.id == game_id))
    game = result.scalar_one_or_none()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    if game.status != "in_progress":
        raise HTTPException(status_code=400, detail="Game already finished")

    # Validate turn
    if game.current_turn == 'p1' and game.player_p1 and game.player_p1 != current_player.id:
        raise HTTPException(status_code=403, detail="Not your turn (P1)")
    if game.current_turn == 'p2' and game.player_p2 and game.player_p2 != current_player.id:
        raise HTTPException(status_code=403, detail="Not your turn (P2)")

    # Validate Move via Logic
    move_dict = {
        'worker_start': move.worker_start,
        'move_to': move.move_to,
        'build_at': move.build_at,
        'move_type': move.move_type
    }
    
    # Clean up None values to match logic.py output format if needed, 
    # OR ensure logic.py returns Nones. 
    # logic.py currently does NOT return Nones for placement moves, it just omits keys.
    # So we simply filter Nones from move_dict to match valid_moves format.
    # move_dict = {k: v for k, v in move_dict.items() if v is not None}
    
    valid_moves = SantoriniLogic.get_valid_moves(game.board, game.current_turn)
    if move_dict not in valid_moves:
        # We can implement simpler comparison if dict eq fails, but it should work for POD types
        # Debugging aid
        # logger.error(f"Invalid move: {move_dict} not in {valid_moves}") 
        raise HTTPException(status_code=400, detail="Invalid move")

    # Apply Move
    new_board, status = SantoriniLogic.apply_move(game.board, move_dict, game.current_turn)
    
    game.board = new_board
    game.status = status
    
    previous_turn = game.current_turn
    if game.status == 'in_progress':
        # Turn Logic
        next_turn = 'p2' if game.current_turn == 'p1' else 'p1'
        
        # Check if we should switch turn (Placement Phase Logic)
        if move.move_type == 'place_worker':
            # Check how many workers current player has
            # We iterate board to count
            worker_count = 0
            for r in range(5):
                for c in range(5):
                    if game.board[r][c]['worker'] == game.current_turn:
                        worker_count += 1
            
            # If < 2 workers, they need to place another one. Turn stays.
            if worker_count < 2:
                next_turn = game.current_turn

        # Check if next player has moves. If not, they lose -> current player wins.
        if SantoriniLogic.check_loss(game.board, next_turn):
            game.status = f"{game.current_turn}_won"
        else:
            game.current_turn = next_turn

    db.add(game)
    await db.commit()
    await db.refresh(game)

    # Redis event
    try:
        await core_redis.redis_pool.xadd(
            f"santorini:{game.id}",
            {
                "type": "move",
                "move": json.dumps(move_dict),
                "by": previous_turn, 
                "board": json.dumps(game.board),
                "status": game.status,
                "current_turn": game.current_turn
            }
        )
    except Exception as e:
        logger.error(f"Failed to publish move event: {e}")

    # AI Turn Trigger
    await _process_ai_turn(game, db)

    # Return new state

    # Return new state
    p1_name = None
    p2_name = None
    if game.player_p1:
        p = await db.get(Player, game.player_p1)
        if p: p1_name = p.name
    if game.player_p2:
        p = await db.get(Player, game.player_p2)
        if p: p2_name = p.name

    return SantoriniGameState(
        id=game.id,
        board=game.board,
        current_turn=game.current_turn,
        status=game.status,
        config=SantoriniCreateGameRequest(**game.config),
        player_p1_name=p1_name,
        player_p2_name=p2_name
    )

@router.delete("/{game_id}")
async def delete_game(
    game_id: int,
    db: AsyncSession = Depends(get_db),
    current_player: Player = Depends(get_current_player)
):
    result = await db.execute(select(SantoriniGame).where(SantoriniGame.id == game_id))
    game = result.scalar_one_or_none()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    await db.delete(game)
    await db.commit()
    return {"detail": "Game deleted"}
