#backend/app/core/azul/game.py
import random
from typing import List
from app.models.azul.azul import AzulGameState, JugadorAzul, Color

def init_game_state(jugadores_data: List[dict]) -> AzulGameState:
    # Crear bolsa con 20 losetas por color
    bolsa = [color for color in Color for _ in range(20)]
    random.shuffle(bolsa)

    # Inicializar jugadores
    jugadores = {}
    for jugador in jugadores_data:
        jugadores[str(jugador["id"])] = JugadorAzul(id=str(jugador["id"]), name=jugador["name"])
    # Elegir jugador inicial
    jugador_inicial = str(jugadores_data[0]["id"])
    jugadores[jugador_inicial].tiene_ficha_inicial = True

    # Determinar número de expositores
    num_jugadores = len(jugadores_data)
    if num_jugadores == 2:
        num_expositores = 5
    elif num_jugadores == 3:
        num_expositores = 7
    else:
        num_expositores = 9
            # Rellenar expositores con 4 losetas cada uno
    expositores = []
    for _ in range(num_expositores):
        expositor = [bolsa.pop() for _ in range(4)]
        expositores.append(expositor)

        # Construir estado inicial
    estado = AzulGameState (
        jugadores=jugadores,
        bolsa=bolsa,
        caja=[],
        centro=[],
        expositores=expositores,
        turno_actual=jugador_inicial,
        jugador_inicial=jugador_inicial,
        fase="oferta",
        ronda=1,
        terminado=False
    )
    return estado