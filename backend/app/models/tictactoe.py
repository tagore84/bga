# backend/app/models/tictactoe.py

from sqlalchemy import Column, Integer, String, JSON
from app.db.base import Base

class TicTacToeGame(Base):
    __tablename__ = "tictactoe_games"

    id = Column(Integer, primary_key=True, index=True)
    board = Column(JSON, nullable=False, default=[None] * 9)
    current_turn = Column(String(1), nullable=False, default="X")  # "X" o "O"
    status = Column(String, nullable=False, default="in_progress")  # in_progress, draw, X_won, O_won