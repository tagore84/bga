# backend/app/routes/tictactoe.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.deps import get_db
from app.models.tictactoe import TicTacToeGame
from pydantic import BaseModel

router = APIRouter(prefix="/tictactoe", tags=["tictactoe"])

class GameState(BaseModel):
    id: int
    board: list[str | None]
    current_turn: str
    status: str

class MoveRequest(BaseModel):
    position: int  # 0..8

@router.post("/", response_model=GameState)
async def create_game(db: AsyncSession = Depends(get_db)):
    game = TicTacToeGame()
    db.add(game)
    await db.commit()
    await db.refresh(game)
    return GameState(
        id=game.id,
        board=game.board,
        current_turn=game.current_turn,
        status=game.status
    )

@router.get("/{game_id}", response_model=GameState)
async def get_game(game_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TicTacToeGame).where(TicTacToeGame.id == game_id))
    game = result.scalar()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return GameState(
        id=game.id,
        board=game.board,
        current_turn=game.current_turn,
        status=game.status
    )

@router.post("/{game_id}/move", response_model=GameState)
async def make_move(
    game_id: int,
    move: MoveRequest,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(TicTacToeGame).where(TicTacToeGame.id == game_id))
    game = result.scalar()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    if game.status != "in_progress":
        raise HTTPException(status_code=400, detail="Game already finished")
    if not (0 <= move.position < 9) or game.board[move.position] is not None:
        raise HTTPException(status_code=400, detail="Invalid move")
    # Place the marker
    board = game.board.copy()
    board[move.position] = game.current_turn
    # Check win
    wins = [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]
    winner = None
    for a,b,c in wins:
        if board[a] == board[b] == board[c] and board[a] is not None:
            winner = board[a]
            break
    # Update status and turn
    if winner:
        status_str = f"{winner}_won"
    elif None not in board:
        status_str = "draw"
    else:
        status_str = "in_progress"
    next_turn = "O" if game.current_turn == "X" else "X"
    # Persist changes
    game.board = board
    game.status = status_str
    game.current_turn = next_turn if status_str == "in_progress" else game.current_turn
    db.add(game)
    await db.commit()
    await db.refresh(game)
    return GameState(
        id=game.id,
        board=game.board,
        current_turn=game.current_turn,
        status=game.status
    )
