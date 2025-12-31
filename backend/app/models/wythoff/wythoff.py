from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Integer, String, JSON, DateTime
from app.db.base import Base

class WythoffGame(Base):
    __tablename__ = "wythoff_games"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    board: Mapped[list] = mapped_column(JSON) # e.g. [5, 3]
    current_turn: Mapped[str] = mapped_column(String) # "1" or "2"
    status: Mapped[str] = mapped_column(String, default="in_progress")
    config: Mapped[dict] = mapped_column(JSON)
    
    game_id: Mapped[int] = mapped_column(Integer) # Foreign key to Games table logic
    game_name: Mapped[str] = mapped_column(String)
    
    player_1_id: Mapped[int] = mapped_column(Integer, nullable=True)
    player_2_id: Mapped[int] = mapped_column(Integer, nullable=True)
    
    created_at: Mapped[str] = mapped_column(DateTime)
