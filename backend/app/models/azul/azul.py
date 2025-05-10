# backend/app/models/azul/azul.py
from sqlalchemy import Column, Integer, String, JSON, ForeignKey
from app.db.base import Base
from enum import Enum
from typing import List, Dict, Optional
from pydantic import BaseModel, Field


class AzulGame(Base):
    __tablename__ = "azul_games"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    state = Column(JSON, nullable=False)


class Color(str, Enum):
    BLUE = "blue"
    RED = "red"
    YELLOW = "yellow"
    BLACK = "black"
    ORANGE = "orange"


class Fase(str, Enum):
    OFERTA = "oferta"
    ALICATADO = "alicatado"
    PREPARACION = "preparacion"
    FINAL = "final"


class JugadorAzul(BaseModel):
    id: str
    name: str
    puntos: int = 0
    pared: List[List[Optional[Color]]] = Field(default_factory=lambda: [[None]*5 for _ in range(5)])
    patrones: List[List[Color]] = Field(default_factory=lambda: [[] for _ in range(5)])
    suelo: List[Color] = Field(default_factory=list)
    tiene_ficha_inicial: bool = False


class AzulGameState(BaseModel):
    jugadores: Dict[str, JugadorAzul]
    bolsa: List[Color] = Field(default_factory=list)
    caja: List[Color] = Field(default_factory=list)
    centro: List[Color] = Field(default_factory=list)
    expositores: List[List[Color]] = Field(default_factory=list)
    turno_actual: Optional[str] = None
    jugador_inicial: Optional[str] = None
    fase: Fase = Fase.OFERTA
    ronda: int = 1
    terminado: bool = False

class AzulGameOutput(BaseModel):
    id: int
    state: AzulGameState

    class Config:
        orm_mode = True