from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

from app.models.tictactoe.tictactoe import TicTacToeGame
from app.models.nim.nim import NimGame
from app.models.wythoff.wythoff import WythoffGame
