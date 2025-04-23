# backend/app/routes/tictactoe.py
from typing import Optional, List, Literal
import random
import json
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime
from app.db.deps import get_db
from app.models.tictactoe import TicTacToeGame
import app.core.redis as core_redis
from app.routes.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/tictactoe", tags=["tictactoe"])

# Schemas
class CreateGameRequest(BaseModel):
    playerXType: Literal["user", "ia"]
    playerXId: Optional[str] = None
    playerOType: Literal["user", "ia"]
    playerOId: Optional[str] = None
    game_name: str = "tictactoe"

class GameState(BaseModel):
    id: int
    board: List[Optional[str]]
    current_turn: str
    status: str
    config: CreateGameRequest
    player_x: Optional[str]
    player_o: Optional[str]

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
async def list_games(
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(TicTacToeGame).where(TicTacToeGame.status == "in_progress")
    )
    games = result.scalars().all()
    return [
        GameState(
            id=g.id,
            board=g.board,
            current_turn=g.current_turn,
            status=g.status,
            config=CreateGameRequest(**g.config),
            player_x=g.player_x,
            player_o=g.player_o,
            game_name=g.game_name,
            created_at=g.created_at
        ) for g in games
    ]

# Crear partida
@router.post("/", response_model=GameState)
async def create_game(
    req: CreateGameRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Validar IDs para usuarios
    if req.playerXType == 'user' and req.playerXId is None:
        raise HTTPException(status_code=400, detail="playerXId required for user type")
    if req.playerOType == 'user' and req.playerOId is None:
        raise HTTPException(status_code=400, detail="playerOId required for user type")

    game = TicTacToeGame(
        board=[None] * 9,
        current_turn="X",
        status="in_progress",
        config=req.dict(),
        player_x=(req.playerXId if req.playerXType == 'user' else None),
        player_o=(req.playerOId if req.playerOType == 'user' else None),
        game_name=req.game_name,
        created_at=datetime.utcnow()
    )
    print(str(game))
    db.add(game)
    await db.commit()
    await db.refresh(game)

    # …
    # Publicar evento de creación
    await core_redis.redis_pool.xadd(
        f"tictactoe:{game.id}",
        {"type": "create", "board": json.dumps(game.board)}
    )

    return GameState(
        id=game.id,
        board=game.board,
        current_turn=game.current_turn,
        status=game.status,
        config=req,
        player_x=game.player_x,
        player_o=game.player_o,
        game_name=game.game_name,
        created_at=game.created_at
    )

# Obtener estado de la partida
@router.get("/{game_id}", response_model=GameState)
async def get_game(
    game_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(TicTacToeGame).where(TicTacToeGame.id == game_id))
    game = result.scalar_one_or_none()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return GameState(
        id=game.id,
        board=game.board,
        current_turn=game.current_turn,
        status=game.status,
        config=CreateGameRequest(**game.config),
        player_x=game.player_x,
        player_o=game.player_o,
        game_name=game.game_name,
        created_at=game.created_at
    )

# Realizar jugada
@router.post("/{game_id}/move", response_model=GameState)
async def make_move(
    game_id: int,
    move: MoveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(TicTacToeGame).where(TicTacToeGame.id == game_id))
    game = result.scalar_one_or_none()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    if game.status != "in_progress":
        raise HTTPException(status_code=400, detail="Game already finished")

    # Validar turno de usuario real
    if game.current_turn == 'X' and game.player_x and game.player_x != current_user.username:
        raise HTTPException(status_code=403, detail="Not your turn (X)")
    if game.current_turn == 'O' and game.player_o and game.player_o != current_user.username:
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
    if game.status == 'in_progress':
        ai_type = game.config.get(f"player{game.current_turn}")
        if ai_type == 'ia':
            empties = [i for i, cell in enumerate(game.board) if cell is None]
            pos = random.choice(empties)
            board = game.board.copy()
            board[pos] = game.current_turn
            status_val = _evaluate_board(board)
            next_turn = 'O' if game.current_turn == 'X' else 'X'
            game.board = board
            game.status = status_val
            game.current_turn = next_turn if status_val == 'in_progress' else game.current_turn
            db.add(game)
            await db.commit()
            await db.refresh(game)

    # Publicar en Redis
    await core_redis.redis_pool.xadd(
        f"tictactoe:{game.id}",
        {
            "type": "move", 
            "position": str(move.position), 
            "by": game.current_turn, 
            "board": json.dumps(game.board), 
            "status": game.status}
    )

    return GameState(
        id=game.id,
        board=game.board,
        current_turn=game.current_turn,
        status=game.status,
        config=CreateGameRequest(**game.config),
        player_x=game.player_x,
        player_o=game.player_o
    )
