# backend/app/routes/games.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from app.models.game import Game
from app.db.deps import get_db

router = APIRouter()

class GameOut(BaseModel):
    name: str
    id: int

@router.get("/", response_model=list[GameOut])
async def list_games(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Game))
    games = result.scalars().all()
    return games

@router.delete("/{game_id}")
async def delete_game(game_id: int, db: AsyncSession = Depends(get_db)):
    from fastapi import HTTPException
    from app.models.azul.azul import AzulGame
    
    result = await db.execute(select(Game).where(Game.id == game_id))
    game = result.scalar_one_or_none()
    if game is None:
        raise HTTPException(status_code=404, detail="Juego no encontrado")
    
    # Delete related azul_games first to avoid foreign key constraint violation
    azul_result = await db.execute(select(AzulGame).where(AzulGame.game_id == game_id))
    azul_games = azul_result.scalars().all()
    for azul_game in azul_games:
        await db.delete(azul_game)
    
    # Now delete the game
    await db.delete(game)
    await db.commit()
    
    return {"message": "Juego eliminado correctamente", "id": game_id}

