
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.models.azul.azul import AzulGameState, JugadorAzul, AzulMove, Color, aplicar_movimiento

def reproduce_bug():
    print("--- Reproducing 0-Tile Bug ---")
    
    # Setup state similar to the log
    # Center has Orange(2), Black(3), Yellow(1) -> [2, 3, 1]
    # We will try to take Blue(0)
    
    state = AzulGameState(
        jugadores={
            "3": JugadorAzul(id="3", name="test", type="human"),
            "5": JugadorAzul(id="5", name="AI", type="ai")
        },
        centro=[Color.ORANGE, Color.BLACK, Color.YELLOW],
        first_player_marker_in_center=True,
        expositores=[[], [], [], [], []]
    )
    
    move = AzulMove(
        factory="centro",
        color=Color.BLUE, # 0
        row=4
    )
    
    print(f"State Center: {state.centro}")
    print(f"Attempting move: Take BLUE (0) from Center")
    
    try:
        aplicar_movimiento(state, "3", move)
        print("Move applied successfully (UNEXPECTED!)")
        print(f"Log: {state.log}")
        print("BUG REPRODUCED: Backend accepted taking 0 tiles.")
    except ValueError as e:
        print(f"Caught expected error: {e}")
        print("Fixed: Backend rejected the move.")

if __name__ == "__main__":
    reproduce_bug()
