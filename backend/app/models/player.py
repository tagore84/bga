# backend/app/models/player.py

from enum import Enum
from sqlalchemy import (
    Column, Integer, String, ForeignKey,
    Sequence, Enum as SQLEnum
)
from app.db.base import Base

class PlayerType(str, Enum):
    human = "human"
    ai    = "ai"

# usamos una secuencia que empieza en 1 para jugadores humanos
human_seq = Sequence("player_human_seq", start=1)

class Player(Base):
    __tablename__ = "players"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, primary_key=False, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)
    type            = Column(SQLEnum(PlayerType), nullable=False)
    description     = Column(String, nullable=True)
    game_id         = Column(Integer, ForeignKey("games.id"), nullable=True)