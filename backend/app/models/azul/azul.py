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

class AzulMove(BaseModel):
    factory: int | str  # puede ser un índice numérico o el string 'centro'
    color: Color
    row: int

def aplicar_movimiento(state: AzulGameState, jugador_id: str, move: AzulMove):
    jugador = state.jugadores[jugador_id]
    color = move.color
    row = move.row - 1  # convertir a índice 0-based

    # Paso 1: recoger fichas
    if move.factory == "centro":
        fichas_tomadas = [f for f in state.centro if f == color]
        state.centro = [f for f in state.centro if f != color]
        if not jugador.tiene_ficha_inicial:
            jugador.tiene_ficha_inicial = True
            jugador.suelo.append(Color.BLUE)  # puedes usar un color especial si tienes uno para "jugador inicial"
    else:
        factory_index = int(move.factory)
        expositor = state.expositores[factory_index]
        fichas_tomadas = [f for f in expositor if f == color]
        restantes = [f for f in expositor if f != color]
        state.centro.extend(restantes)
        state.expositores[factory_index] = []

    # Paso 2: intentar colocar fichas en la fila de patrón
    fila = jugador.patrones[row]
    if all(c == color for c in fila) or not fila:
        espacio_disponible = 5 - len(fila)
        colocar = min(len(fichas_tomadas), espacio_disponible)
        jugador.patrones[row].extend([color] * colocar)
        sobrantes = len(fichas_tomadas) - colocar
    else:
        sobrantes = len(fichas_tomadas)

    # Paso 3: poner fichas sobrantes en el suelo
    jugador.suelo.extend([color] * sobrantes)