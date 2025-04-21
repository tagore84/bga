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