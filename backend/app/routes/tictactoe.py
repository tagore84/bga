# backend/app/routes/tictactoe.py
from typing import Optional, List, Literal
import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime
from app.db.deps import get_db
from app.models.tictactoe import TicTacToeGame
from app.routes.auth import get_current_player
from app.models.player import Player

from app.models.player import PlayerType
from app.models.tictactoe import TicTacToeGame
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import json

from app.db.deps import get_db
from app.models.tictactoe import TicTacToeGame
from app.models.player import Player
import app.core.redis as core_redis
from app.models.game import Game

import logging
logger = logging.getLogger(__name__)


router = APIRouter(prefix="/tictactoe", tags=["tictactoe"])

# Schemas
class CreateGameRequest(BaseModel):
    game_name:    str
    playerXType:  Literal["human", "ai"]
    playerXId:    int
    playerOType:  Literal["human", "ai"]
    playerOId:    int

class GameState(BaseModel):
    id:           int
    board:        list[Optional[str]]
    current_turn: str
    status:       str
    config:       CreateGameRequest
    player_x_name: Optional[str] = None
    player_o_name: Optional[str] = None


class ParticipantOut(BaseModel):
    symbol: str                        # "X" u "O"
    player_id: int
    player_type: PlayerType
    name: Optional[str]

class MoveRequest(BaseModel):
    position: int  # 0..8

# Helper para computar resultado
def _evaluate_board(board):
    wins = [
        (0, 1, 2), (3, 4, 5), (6, 7, 8),
        (0, 3, 6), (1, 4, 7), (2, 5, 8),
        (0, 4, 8), (2, 4, 6)
    ]
    for a, b, c in wins:
        if board[a] == board[b] == board[c] and board[a] is not None:
            return f"{board[a]}_won"
    if None not in board:
        return "draw"
    return "in_progress"

# Listar partidas activas
@router.get("/", response_model=List[GameState])
async def list_games(db: AsyncSession = Depends(get_db)):
    q = await db.execute(select(TicTacToeGame).where(TicTacToeGame.status=="in_progress"))
    games = q.scalars().all()

    out = []
    for g in games:
        # serializar participantes
        parts = []
        if g.player_x is not None:
            px = await db.get(Player, g.player_x)
            parts.append(ParticipantOut(
                symbol='X',
                player_id=px.id,
                player_type=px.type,
                name=px.name
            ))
        if g.player_o is not None:
            po = await db.get(Player, g.player_o)
            parts.append(ParticipantOut(
                symbol='O',
                player_id=po.id,
                player_type=po.type,
                name=po.name
            ))
        out.append(GameState(
            id            = g.id,
            board         = g.board,
            current_turn  = g.current_turn,
            status        = g.status,
            config        = CreateGameRequest(**g.config),
            player_x_name  = parts[0].name if len(parts) > 0 else None,
            player_o_name  = parts[1].name if len(parts) > 1 else None
        ))
    return out

@router.post("/", response_model=GameState)
async def create_game(
    req: CreateGameRequest,
    db: AsyncSession = Depends(get_db),
    current_player = Depends(get_current_player),
):
    # 1) Obtener definición de juego
    result = await db.execute(select(Game).where(Game.name == "tictactoe"))
    base_game = result.scalar_one_or_none()
    if base_game is None:
        raise HTTPException(status_code=500, detail="Game definition 'tictactoe' not found")
    player_x_id = req.playerXId
    player_o_id = req.playerOId
    tictactoe_game = TicTacToeGame(
        board=[None]*9,
        current_turn="X",
        status="in_progress",
        config=req.dict(),
        game_name=req.game_name,
        player_x=req.playerXId,
        player_o=req.playerOId,
        game_id=base_game.id,
        created_at=datetime.utcnow()
    )
    db.add(tictactoe_game)
    await db.commit()
    await db.refresh(tictactoe_game)


    # 3) Publicar evento en Redis
    try:
        await core_redis.redis_pool.xadd(
            f"tictactoe:{tictactoe_game.id}",
            {"type":"create", "board":json.dumps(tictactoe_game.board)}
        )
    except Exception as e:
        logger.error(f"Failed to publish create event to Redis: {e}")

    # 4) Devolver estado inicial
    x_name = None
    o_name = None
    
    px = await db.get(Player, player_x_id)
    x_name = px.name
    po = await db.get(Player, player_o_id)
    o_name = po.name
    return GameState(
        id           = tictactoe_game.id,
        board        = tictactoe_game.board,
        current_turn = tictactoe_game.current_turn,
        status       = tictactoe_game.status,
        config       = CreateGameRequest(**tictactoe_game.config),
        player_x_name   = x_name,
        player_o_name   = o_name
        # ahora podrías también devolver lista de participants si lo quisieras
    )

# Obtener estado de la partida
@router.get("/{game_id}", response_model=GameState)
async def get_game(game_id: int, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(TicTacToeGame).where(TicTacToeGame.id==game_id))
    g = res.scalar_one_or_none()
    if not g:
        raise HTTPException(404, "Game not found")
    # serializar igual que arriba...
    player_x = None
    player_o = None
    if g.player_x is not None:
        px = await db.get(Player, g.player_x)
        player_x = ParticipantOut(
            symbol='X',
            player_id=px.id,
            player_type=px.type,
            name=px.name
        )
    if g.player_o is not None:
        po = await db.get(Player, g.player_o)
        player_o = ParticipantOut(
            symbol='O',
            player_id=po.id,
            player_type=po.type,
            name=po.name
        )
    outputGameState = GameState(
        id           = g.id,
        board        = g.board,
        current_turn = g.current_turn,
        status       = g.status,
        config       = CreateGameRequest(**g.config),
        player_x_name     = player_x.name,
        player_o_name     = player_o.name
    )
    print("outputGameState", outputGameState)
    return outputGameState

# Realizar jugada
@router.post("/{game_id}/move", response_model=GameState)
async def make_move(
    game_id: int,
    move: MoveRequest,
    db: AsyncSession = Depends(get_db),
    current_player: Player = Depends(get_current_player)
):
    result = await db.execute(select(TicTacToeGame).where(TicTacToeGame.id == game_id))
    game = result.scalar_one_or_none()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    if game.status != "in_progress":
        raise HTTPException(status_code=400, detail="Game already finished")

    # Validar turno de usuario real
    if game.current_turn == 'X' and game.player_x and game.player_x != current_player.id:
        raise HTTPException(status_code=403, detail="Not your turn (X)")
    if game.current_turn == 'O' and game.player_o and game.player_o != current_player.id:
        raise HTTPException(status_code=403, detail="Not your turn (O)")

    if not (0 <= move.position < 9) or game.board[move.position] is not None:
        raise HTTPException(status_code=400, detail="Invalid move")

    # Jugada humana\    
    board = game.board.copy()
    board[move.position] = game.current_turn
    status_val = _evaluate_board(board)
    next_turn = 'O' if game.current_turn == 'X' else 'X'
    game.board = board
    game.status = status_val
    game.current_turn = next_turn if status_val == 'in_progress' else game.current_turn
    db.add(game)
    await db.commit()
    await db.refresh(game)

    # Jugada IA si aplica
    # Jugada IA si aplica
    # ToDo

    # Publicar en Redis
    try:
        await core_redis.redis_pool.xadd(
            f"tictactoe:{game.id}",
            {
                "type": "move",
                "position": str(move.position),
                "by": game.current_turn,
                "board": json.dumps(game.board),
                "status": game.status
            }
        )
    except Exception as e:
        logger.error(f"Failed to publish move event to Redis: {e}")

    return GameState(
        id=game.id,
        board=game.board,
        current_turn=game.current_turn,
        status=game.status,
        config=CreateGameRequest(**game.config),
        player_x=game.player_x,
        player_o=game.player_o
    )
