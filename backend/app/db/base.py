from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

from app.models.tictactoe.tictactoe import TicTacToeGame
