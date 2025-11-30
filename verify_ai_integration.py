import sys
import os
import asyncio
import json

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.models.azul.azul import AzulGameState, JugadorAzul, Color
from app.core.azul.ai_zero import AzulZeroMCTS, AzulZeroRandomPlus

def create_dummy_state():
    p1 = JugadorAzul(id="p1", name="Player 1", type="human")
    p2 = JugadorAzul(id="p2", name="Player 2", type="ai")
    
    state = AzulGameState(
        jugadores={"p1": p1, "p2": p2},
        turno_actual="p1",
        jugador_inicial="p1"
    )
    
    # Initialize factories
    state.expositores = [
        [Color.BLUE, Color.RED, Color.YELLOW, Color.BLACK],
        [Color.BLUE, Color.BLUE, Color.RED, Color.RED],
        [Color.YELLOW, Color.YELLOW, Color.BLACK, Color.BLACK],
        [Color.ORANGE, Color.ORANGE, Color.ORANGE, Color.ORANGE],
        [Color.BLUE, Color.YELLOW, Color.RED, Color.BLACK]
    ]
    state.centro = [Color.BLUE]
    
    return state

def test_random_plus():
    print("Testing AzulZeroRandomPlus...")
    ai = AzulZeroRandomPlus()
    state = create_dummy_state()
    state.turno_actual = "p2" # AI turn
    
    move = ai.select_move(state)
    print(f"RandomPlus selected move: {move}")
    assert move is not None
    print("RandomPlus test passed!")

def test_mcts():
    print("\nTesting AzulZeroMCTS...")
    model_path = "backend/modelos/best.pt"
    if not os.path.exists(model_path):
        print(f"Model not found at {model_path}, skipping MCTS test")
        return

    ai = AzulZeroMCTS(model_path, mcts_iters=10) # Low iters for speed
    state = create_dummy_state()
    state.turno_actual = "p2" # AI turn
    
    move = ai.select_move(state)
    print(f"MCTS selected move: {move}")
    assert move is not None
    print("MCTS test passed!")

if __name__ == "__main__":
    test_random_plus()
    test_mcts()
