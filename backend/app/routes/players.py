from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional, Literal
from pydantic import BaseModel
from app.models.player import Player
from app.db.deps import get_db

router = APIRouter(prefix="/players", tags=["players"])

class PlayerOut(BaseModel):
    name: str
    game_id: Optional[int]
    id: int
    type: Literal["human", "ai"]

    class Config:
        from_attributes = True

@router.get("/", response_model=list[PlayerOut])
async def list_players(db: AsyncSession = Depends(get_db)):
    print("Fetching players from the database:\n")
    result = await db.execute(select(Player))
    players = result.scalars().all()
    print(f"Fetched {len(players)} players:\n")
    for player in players:
        print(f"Player ID: {player.id}, Name: {player.name}, Game ID: {player.game_id}")
    print("\n")
    print("Finished fetching players from the database.\n")
    return players