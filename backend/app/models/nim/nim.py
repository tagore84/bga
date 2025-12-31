from datetime import datetime
from sqlalchemy import Column, Integer, String, JSON, ForeignKey, DateTime
from app.db.base import Base

class NimGame(Base):
    __tablename__ = "nim_games"

    id           = Column(Integer, primary_key=True, index=True)
    board        = Column(JSON, nullable=False, default=[1, 3, 5, 7]) # Default pyramid 1-3-5-7
    current_turn = Column(String(1), nullable=False, default="1") # "1" or "2" (Player 1 or Player 2) - OR maybe keep consistent with others using Player IDs or Indices? 
    # TicTacToe uses "X"/"O". Chess "white"/"black".
    # Let's use indices "0" and "1" or just ID references. 
    # Actually, let's stick to a simple string identifier for turn like "1" and "2" or "p1"/"p2".
    # Docs say "Two players". Let's use "1" and "2" as simplified turn indicators relative to the player columns.
    
    status       = Column(String, nullable=False, default="in_progress")
    config       = Column(JSON, nullable=False)
    game_id      = Column(Integer, ForeignKey("games.id"), nullable=False)
    game_name    = Column(String, nullable=False, default="nim")
    
    player_1_id  = Column(Integer, ForeignKey("players.id"), nullable=True)
    player_2_id  = Column(Integer, ForeignKey("players.id"), nullable=True)
    
    created_at   = Column(DateTime, nullable=False, default=datetime.utcnow)
