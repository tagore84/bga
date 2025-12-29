# backend/app/models/connect4/connect4.py

from datetime import datetime
from sqlalchemy import Column, Integer, String, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.models.game import Game

class Connect4Game(Base):
    __tablename__ = "connect4_games"

    id           = Column(Integer, primary_key=True, index=True)
    board        = Column(JSON, nullable=False, default=[None] * 42) # 6 rows * 7 cols
    current_turn = Column(String, nullable=False, default="Red") # Red starts usually
    status       = Column(String, nullable=False, default="in_progress")
    config       = Column(JSON, nullable=False)
    game_id      = Column(Integer, ForeignKey("games.id"), nullable=False)
    game_name    = Column(String, nullable=False, default="connect4")
    
    # Players
    player_red   = Column(Integer, ForeignKey("players.id"), nullable=True)
    player_blue  = Column(Integer, ForeignKey("players.id"), nullable=True)
    
    created_at   = Column(DateTime, nullable=False, default=datetime.utcnow)
