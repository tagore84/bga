from sqlalchemy import (Column, Integer, String)
from app.db.base import Base

class Game(Base):
    __tablename__ = "games"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, primary_key=False, index=True, nullable=False)
    description = Column(String, primary_key=False, index=True, nullable=True)

    def __str__(self):
        return self.name
