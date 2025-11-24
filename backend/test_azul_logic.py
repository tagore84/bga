import sys
import os
sys.path.append(os.getcwd())

from app.models.azul.azul import AzulGameState, JugadorAzul, Color, move_tiles_to_wall, calculate_scoring, prepare_next_round, wall_tiling_phase
from app.core.azul.game import init_game_state

def test_scoring():
    print("Testing Scoring...")
    # Create a dummy wall
    wall = [[None]*5 for _ in range(5)]
    
    # Place a tile at 0,0
    wall[0][0] = Color.BLUE
    score = calculate_scoring(wall, 0, 0)
    assert score == 1, f"Expected 1, got {score}"
    
    # Place at 0,1 (Horizontal adjacency)
    wall[0][1] = Color.YELLOW
    score = calculate_scoring(wall, 0, 1)
    assert score == 2, f"Expected 2, got {score}"
    
    # Place at 1,1 (Vertical adjacency)
    wall[1][1] = Color.BLUE
    score = calculate_scoring(wall, 1, 1)
    assert score == 2, f"Expected 2, got {score}"
    
    print("Scoring OK")

def test_wall_tiling():
    print("Testing Wall Tiling...")
    # Setup player with a full line
    p = JugadorAzul(id="1", name="Test", type="human")
    p.patrones[0] = [Color.BLUE] # Row 0 needs 1 tile
    p.patrones[1] = [Color.YELLOW] # Row 1 needs 2 tiles, incomplete
    
    state = AzulGameState(jugadores={"1": p})
    state.caja = []
    
    move_tiles_to_wall(state, p)
    
    # Row 0 should be empty (moved to wall)
    assert len(p.patrones[0]) == 0, "Row 0 not cleared"
    # Wall 0,0 (Blue) should be filled. Blue is col 0 in row 0.
    assert p.pared[0][0] == Color.BLUE, "Tile not on wall"
    # Score should be 1
    assert p.puntos == 1, f"Expected 1 point, got {p.puntos}"
    
    # Row 1 should be unchanged
    assert len(p.patrones[1]) == 1, "Row 1 changed"
    
    print("Wall Tiling OK")

def test_round_transition():
    print("Testing Round Transition...")
    p1 = JugadorAzul(id="1", name="P1", type="human")
    p2 = JugadorAzul(id="2", name="P2", type="human")
    p2.tiene_ficha_inicial = True
    
    state = AzulGameState(jugadores={"1": p1, "2": p2})
    state.expositores = [[], []] # Empty
    state.centro = [] # Empty
    state.bolsa = [Color.RED] * 20 # Enough for refill
    state.ronda = 1
    
    wall_tiling_phase(state)
    
    assert state.ronda == 2, "Round not incremented"
    assert state.fase == "oferta", "Phase not reset"
    assert len(state.expositores[0]) == 4, "Factories not refilled"
    assert state.turno_actual == "2", "Wrong start player"
    assert p2.tiene_ficha_inicial == False, "First player token not reset"
    
    print("Round Transition OK")

if __name__ == "__main__":
    test_scoring()
    test_wall_tiling()
    test_round_transition()
    print("ALL TESTS PASSED")
