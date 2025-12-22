from sqlalchemy import Column, Integer, String, JSON, ForeignKey
from app.db.base import Base
from enum import Enum, IntEnum
from typing import List, Dict, Optional
from pydantic import BaseModel, Field


class AzulGame(Base):
    __tablename__ = "azul_games"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    state = Column(JSON, nullable=False)


from enum import IntEnum

class Color(IntEnum):
    BLUE = 0
    YELLOW = 1
    ORANGE = 2
    BLACK = 3
    RED = 4


class Fase(str, Enum):
    OFERTA = "oferta"
    ALICATADO = "alicatado"
    PREPARACION = "preparacion"
    FINAL = "final"


class JugadorAzul(BaseModel):
    id: str
    name: str
    type: str
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
    log: List[str] = Field(default_factory=list)
    first_player_marker_in_center: bool = True
    last_move: Optional[dict] = None


class AzulGameOutput(BaseModel):
    id: int
    state: AzulGameState

    class Config:
        from_attributes = True

class AzulMove(BaseModel):
    factory: int | str  # puede ser un índice numérico o el string 'centro'
    color: Color
    row: int

    row: int

def get_wall_column(row: int, color: Color) -> int:
    # Azul wall pattern:
    # Row 0: B Y R K O (0 1 2 3 4)
    # Row 1: O B Y R K (4 0 1 2 3)
    # Row 2: K O B Y R (3 4 0 1 2)
    # Row 3: R K O B Y (2 3 4 0 1)
    # Row 4: Y R K O B (1 2 3 4 0)
    # Formula: (color + row) % 5
    return (color + row) % 5

def calculate_scoring(wall: List[List[Optional[Color]]], row: int, col: int) -> int:
    score = 0
    
    # Horizontal
    h_score = 0
    # Check left
    for c in range(col - 1, -1, -1):
        if wall[row][c] is not None:
            h_score += 1
        else:
            break
    # Check right
    for c in range(col + 1, 5):
        if wall[row][c] is not None:
            h_score += 1
        else:
            break
    if h_score > 0:
        h_score += 1 # Count the placed tile itself
    
    # Vertical
    v_score = 0
    # Check up
    for r in range(row - 1, -1, -1):
        if wall[r][col] is not None:
            v_score += 1
        else:
            break
    # Check down
    for r in range(row + 1, 5):
        if wall[r][col] is not None:
            v_score += 1
        else:
            break
    if v_score > 0:
        v_score += 1 # Count the placed tile itself

    # If both horizontal and vertical formed lines, sum both. 
    # If only one, it's just that score.
    # If neither (isolated tile), score is 1.
    if h_score == 0 and v_score == 0:
        score = 1
    else:
        score = h_score + v_score
        if h_score > 0 and v_score > 0:
            # The tile is counted twice in the logic above (once for H, once for V), which is correct in Azul rules?
            # Rules: "If there are tiles in both directions, count points for both lines (the placed tile is counted twice)."
            # So yes, h_score + v_score is correct because both include the tile itself.
            pass
        elif h_score > 0:
            score = h_score
        else:
            score = v_score
            
    return score

def move_tiles_to_wall(state: AzulGameState, jugador: JugadorAzul):
    # Floor penalty
    floor_penalties = [1, 1, 2, 2, 2, 3, 3] # Cumulative: -1, -2, -4, -6, -8, -11, -14
    penalty = 0
    for i, tile in enumerate(jugador.suelo):
        if i < len(floor_penalties):
            penalty += floor_penalties[i]
        else:
            penalty += 3 # Max penalty per extra tile? Rules say usually max 14 total but let's assume 3 per extra.
    
    jugador.puntos = max(0, jugador.puntos - penalty)
    
    # Return floor tiles to box (caja), except the first player marker (if it was implemented as a tile)
    # In this model, first player marker is a boolean flag, but we might have put a placeholder in 'suelo'.
    # In aplicar_movimiento: jugador.suelo.append(Color.BLUE) # placeholder
    # We should filter that out or handle it.
    # Let's assume standard colors go to caja.
    for tile in jugador.suelo:
        if isinstance(tile, int) or isinstance(tile, Color): # It's a color
             state.caja.append(tile)
    jugador.suelo = []

    # Process pattern lines
    for r in range(5):
        line = jugador.patrones[r]
        if len(line) == r + 1: # Line is full
            color = line[0]
            # Move one to wall
            col = get_wall_column(r, color)
            jugador.pared[r][col] = color
            
            # Score
            points = calculate_scoring(jugador.pared, r, col)
            jugador.puntos += points
            
            # Rest to box
            # One tile is on wall, rest (len(line)-1) go to caja
            state.caja.extend([color] * (len(line) - 1))
            
            # Clear line
            jugador.patrones[r] = []
        else:
            # Line not full, stays as is
            pass

def check_game_end(state: AzulGameState) -> bool:
    for jugador in state.jugadores.values():
        for row in jugador.pared:
            if all(c is not None for c in row):
                return True
    return False

def final_scoring(state: AzulGameState):
    for jugador in state.jugadores.values():
        # Horizontal lines: +2
        for r in range(5):
            if all(c is not None for c in jugador.pared[r]):
                jugador.puntos += 2
        
        # Vertical lines: +7
        for c in range(5):
            if all(jugador.pared[r][c] is not None for r in range(5)):
                jugador.puntos += 7
                
        # 5 of a color: +10
        for color in Color:
            count = 0
            for r in range(5):
                for c in range(5):
                    if jugador.pared[r][c] == color:
                        count += 1
            if count == 5:
                jugador.puntos += 10

def prepare_next_round(state: AzulGameState):
    state.ronda += 1
    state.fase = Fase.OFERTA
    
    # Refill factories
    # Need 4 tiles per factory.
    num_factories = len(state.expositores)
    total_needed = num_factories * 4
    
    if len(state.bolsa) < total_needed:
        # Refill bag from caja
        state.bolsa.extend(state.caja)
        state.caja = []
        import random
        random.shuffle(state.bolsa)
    
    # If still not enough, fill as much as possible (rare edge case)
    for i in range(num_factories):
        tiles = []
        for _ in range(4):
            if state.bolsa:
                tiles.append(state.bolsa.pop())
        state.expositores[i] = tiles
        
    # Determine next starting player
    next_start = None
    for pid, jug in state.jugadores.items():
        if jug.tiene_ficha_inicial:
            next_start = pid
            jug.tiene_ficha_inicial = False # Reset for next round
            break
            
    if next_start:
        state.turno_actual = next_start
        state.jugador_inicial = next_start
    else:
        # Fallback if logic failed (shouldn't happen if someone took from center)
        pass
    
    # Reset first player marker for new round
    state.first_player_marker_in_center = True

def wall_tiling_phase(state: AzulGameState):
    state.fase = Fase.ALICATADO
    
    for pid, jugador in state.jugadores.items():
        move_tiles_to_wall(state, jugador)
        
    if check_game_end(state):
        state.fase = Fase.FINAL
        state.terminado = True
        final_scoring(state)
    else:
        prepare_next_round(state)

def aplicar_movimiento(state: AzulGameState, jugador_id: str, move: AzulMove):
    jugador = state.jugadores[jugador_id]
    color = move.color
    row = move.row - 1  # convertir a índice 0-based

    # Paso 1: recoger fichas
    if move.factory == "centro":
        fichas_tomadas = [f for f in state.centro if f == color]
        state.centro = [f for f in state.centro if f != color]
        if state.first_player_marker_in_center:
            state.first_player_marker_in_center = False
            jugador.tiene_ficha_inicial = True
    else:
        factory_index = int(move.factory)
        expositor = state.expositores[factory_index]
        fichas_tomadas = [f for f in expositor if f == color]
        restantes = [f for f in expositor if f != color]
        state.centro.extend(restantes)
        state.expositores[factory_index] = []

    # Validation: Ensure at least one tile was taken
    if not fichas_tomadas:
        source_name = "Centro" if move.factory == "centro" else f"Fábrica {move.factory}"
        # color name
        color_names = ["Azul", "Amarillo", "Rojo", "Negro", "Naranja"]
        c_name = color_names[int(color)] if isinstance(color, int) else str(color)
        raise ValueError(f"Movimiento inválido: No hay fichas de color {c_name} en {source_name}")

    # Track tracking info
    added_to_pattern = 0
    added_to_floor = 0

    # Paso 2: intentar colocar fichas en la fila de patrón
    if row == -1: # move.row was 0, meaning Floor
        sobrantes = len(fichas_tomadas)
    else:
        fila = jugador.patrones[row]
        if all(c == color for c in fila) or not fila:
            espacio_disponible = (row + 1) - len(fila)
            colocar = min(len(fichas_tomadas), espacio_disponible)
            jugador.patrones[row].extend([color] * colocar)
            sobrantes = len(fichas_tomadas) - colocar
            added_to_pattern = colocar
        else:
            sobrantes = len(fichas_tomadas)
            added_to_pattern = 0

    # Paso 3: poner fichas sobrantes en el suelo
    jugador.suelo.extend([color] * sobrantes)
    added_to_floor = sobrantes
    
    # populate last_move
    state.last_move = {
        "player_id": jugador_id,
        "color": color,
        "target_row_index":row, # -1 for floor, 0-4 for pattern
        "added_to_pattern": added_to_pattern,
        "added_to_floor": added_to_floor,
        "round_at_move": state.ronda
    }
    
    # Log move
    color_names = ["Azul", "Amarillo", "Naranja", "Negro", "Rojo"] # Map Color enum to Spanish names if desired, or English
    color_name = color_names[int(color)] if isinstance(color, int) else str(color)
    
    source_name = "Centro" if move.factory == "centro" else f"Fábrica {move.factory}"
    dest_name = "Suelo" if row == -1 else f"Fila {row + 1}"
    
    count = len(fichas_tomadas)
    msg = f"{jugador.name} tomó {count} {color_name} de {source_name} a {dest_name}"
    state.log.append(msg)

    # Check if round is over (all factories empty and center empty)
    factories_empty = all(len(exp) == 0 for exp in state.expositores)
    center_empty = len(state.centro) == 0
    
    if factories_empty and center_empty:
        wall_tiling_phase(state)

def get_legal_moves(state: AzulGameState) -> List[AzulMove]:
    moves = []
    jugador = state.jugadores[state.turno_actual]
    
    # Fuentes: índices 0..N-1 son fábricas, "centro" es el centro
    sources = list(range(len(state.expositores))) + ["centro"]
    
    for source in sources:
        # Determinar qué colores hay disponibles en esta fuente
        if source == "centro":
            available_colors = set(state.centro)
        else:
            available_colors = set(state.expositores[source])
            
        for color in available_colors:
            # Para cada color disponible, probar destinos (filas 1-5)
            for row_idx in range(5):
                patron = jugador.patrones[row_idx]
                
                # Reglas para poder colocar en una fila:
                # 1. La fila no debe estar llena.
                if len(patron) >= row_idx + 1:
                    continue
                    
                # 2. Si tiene fichas, deben ser del mismo color.
                # Nota: patron puede tener None/null si es una implementación array fija, 
                # pero aquí parece ser lista dinámica o lista con None.
                # En init_game_state: patrones = [[] for _ in range(5)]
                # En aplicar_movimiento: jugador.patrones[row].extend(...)
                # Así que es lista dinámica de colores.
                if patron and patron[0] != color:
                    continue
                    
                # 3. La pared correspondiente a esa fila no debe tener ya ese color.
                col_wall = get_wall_column(row_idx, color)
                if jugador.pared[row_idx][col_wall] is not None:
                    continue
                
                # Si pasa todas las reglas, es un movimiento válido
                # factory debe ser string para "centro" o int para expositor
                factory_val = str(source)
                moves.append(AzulMove(factory=factory_val, color=color, row=row_idx + 1))
            
            # Opción de ir directo al suelo (row=0)
            # Siempre es legal coger fichas y tirarlas al suelo (aunque sea mala jugada)
            moves.append(AzulMove(factory=str(source), color=color, row=0))
                
    return moves