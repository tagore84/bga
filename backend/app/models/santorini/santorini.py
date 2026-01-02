from datetime import datetime
from sqlalchemy import Column, Integer, String, JSON, ForeignKey, DateTime
from app.db.base import Base

class SantoriniGame(Base):
    __tablename__ = "santorini_games"

    id           = Column(Integer, primary_key=True, index=True)
    board        = Column(JSON, nullable=False) # 5x5 grid cells: {level: 0-4, worker: null|p1|p2}
    current_turn = Column(String, nullable=False, default="p1") # p1 or p2
    status       = Column(String, nullable=False, default="in_progress") # in_progress, p1_won, p2_won
    config       = Column(JSON, nullable=False)
    game_id      = Column(Integer, ForeignKey("games.id"), nullable=False, default=7) # Assuming ID 7 for new game, or dynamic
    
    player_p1    = Column(Integer, ForeignKey("players.id"), nullable=True)
    player_p2    = Column(Integer, ForeignKey("players.id"), nullable=True)
    
    created_at   = Column(DateTime, nullable=False, default=datetime.utcnow)
