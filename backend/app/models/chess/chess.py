# backend/app/models/chess/chess.py
from datetime import datetime
from sqlalchemy import Column, Integer, String, JSON, ForeignKey, DateTime
from app.db.base import Base

class ChessGame(Base):
    __tablename__ = "chess_games"

    id           = Column(Integer, primary_key=True, index=True)
    board_fen    = Column(String, nullable=False, default="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    current_turn = Column(String, nullable=False, default="white")
    status       = Column(String, nullable=False, default="in_progress")
    config       = Column(JSON, nullable=False)
    
    game_id      = Column(Integer, ForeignKey("games.id"), nullable=False)
    game_name    = Column(String, nullable=False, default="chess")
    
    player_white = Column(Integer, ForeignKey("players.id"), nullable=True)
    player_black = Column(Integer, ForeignKey("players.id"), nullable=True)
    
    created_at   = Column(DateTime, nullable=False, default=datetime.utcnow)
