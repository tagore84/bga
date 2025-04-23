# backend/app/models/tictactoe.py

from datetime import datetime
from sqlalchemy import Column, Integer, String, JSON, ForeignKey, DateTime
from app.db.base import Base

class TicTacToeGame(Base):
    __tablename__ = "tictactoe_games"

    id           = Column(Integer, primary_key=True, index=True)
    board        = Column(JSON, nullable=False, default=[None]*9)
    current_turn = Column(String(1), nullable=False, default="X")
    status       = Column(String, nullable=False, default="in_progress")
    config       = Column(JSON, nullable=False)
    game_name    = Column(String, nullable=False, default="tictactoe")
    player_x     = Column(String, ForeignKey("users.username"), nullable=True)
    player_o     = Column(String, ForeignKey("users.username"), nullable=True)
    created_at   = Column(DateTime, nullable=False, default=datetime.utcnow)
