# backend/app/models/tictactoe.py

from datetime import datetime
from sqlalchemy import Column, Integer, String, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.models.game import Game

class TicTacToeGame(Base):
    __tablename__ = "tictactoe_games"

    id           = Column(Integer, primary_key=True, index=True)
    board        = Column(JSON, nullable=False, default=[None]*9)
    current_turn = Column(String(1), nullable=False, default="X")
    status       = Column(String, nullable=False, default="in_progress")
    config       = Column(JSON, nullable=False)
    game_id      = Column(Integer, ForeignKey("games.id"), nullable=False)
    game_name    = Column(String, nullable=False, default="tictactoe")
    player_x  = Column(Integer, ForeignKey("players.id"), nullable=True)
    player_o  = Column(Integer, ForeignKey("players.id"), nullable=True)
    created_at   = Column(DateTime, nullable=False, default=datetime.utcnow)
    