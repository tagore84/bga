
import sys
import os
sys.path.append(os.getcwd())

from app.models.azul.azul import AzulGameState, JugadorAzul, Color, move_tiles_to_wall, aplicar_movimiento, AzulMove

def test_disappearing_tiles():
    print("\n--- Test Disappearing Tiles (Bug 1) ---")
    # Setup state matching Game 149 Line 4
    # Player 5 has [4, 4, 4] in Row 4 (Index 3). Capacity 4.
    # Player took 3 Oranges (4) from Center.
    
    p5 = JugadorAzul(id="5", name="AzulZero_MCTS", type="ai")
    # Index 3 is Row 4. Capacity 4. 
    # It has 3 Oranges.
    p5.patrones[3] = [Color.RED, Color.RED, Color.RED] # Assuming 4 is Red for a moment, or Orange. 
    # In code Color enum: 0=Blue, 1=Yellow, 2=Orange, 3=Black, 4=Red.
    # Wait. In Log, "Naranja" was 4. But in Code Color enum, 2 is Orange, 4 is Red.
    # Let's verify enum.
    # file `app/models/azul/azul.py` lines 18-23:
    # 0=Blue, 1=Yellow, 2=Orange, 3=Black, 4=Red.
    
    # In Log:
    # Line 2: "Rojo" move color 2. 
    # Wait. If Enum has 2=Orange. Why Log says "Rojo" (Red) for 2?
    # This implies Log/Enum Mismatach.
    # Log 2: "AzulZero_MCTS tomó 1 Rojo... color: 2".
    # Code Enum: 2 is Orange. 4 is Red.
    # Is it possible the Enum in `app/models/azul/azul.py` I read is outdated or different version?
    # Or Log text generation uses a different array?
    # Line 304: `color_names = ["Azul", "Amarillo", "Rojo", "Negro", "Naranja"]`
    # Index 0: Azul. Index 1: Amarillo. Index 2: Rojo. Index 3: Negro. Index 4: Naranja.
    # BUT Enum: 0=Blue, 1=Yellow, 2=Orange, 3=Black, 4=Red.
    # Mismatch!
    # Enum 2 = Orange. name_list[2] = Rojo.
    # Enum 4 = Red. name_list[4] = Naranja.
    # This mismatch doesn't affect logic (numbers match numbers), but explains the confusion.
    # In Log Line 4: "Naranja" (Orange). Move color 4.
    # In Code: color 4 is Red (Enum). name_list[4] is Naranja.
    # So Log text "Naranja" corresponds to ID 4.
    # ID 4 is "Red" in Enum Name (but "Naranja" in text).
    # Okay. P5 Pattern 3 has `[4, 4, 4]`.
    
    p5.patrones[3] = [Color.RED, Color.RED, Color.RED] # ID 4
    
    state = AzulGameState(jugadores={"5": p5})
    # Center has 3 tiles of ID 4. 
    # (Log Line 4: tomó 3 Naranja).
    state.centro = [Color.RED, Color.RED, Color.RED, Color.BLUE] # Add extra to ensure correct filtering
    
    move = AzulMove(factory="centro", color=Color.RED, row=4) # Row 4 (1-based) -> Index 3
    
    print(f"Before: Pattern 3: {p5.patrones[3]}, Suelo: {p5.suelo}")
    aplicar_movimiento(state, "5", move)
    print(f"After:  Pattern 3: {p5.patrones[3]}, Suelo: {p5.suelo}")
    
    # Expected: Pattern 3 full (4 tiles). Suelo has 2 tiles. (Took 3, 1 fits, 2 overflow).
    # Actual in Log: Pattern 3 same (3 tiles). Suelo empty.
    
    if len(p5.patrones[3]) == 3 and len(p5.suelo) == 0:
        print("BUG 1 REPRODUCED: Tiles disappeared!")
    elif len(p5.patrones[3]) == 4 and len(p5.suelo) == 2:
        print("Logic correct locally. Bug not reproduced with this script.")
    else:
        print("Something else happened.")

def test_pattern_clearing():
    print("\n--- Test Pattern Clearing (Bug 2) ---")
    # Setup state matching End of Round 1
    # P5 has Pattern 0 (Cap 1) full with [0]. Wall 0 empty.
    # P5 has Pattern 1 (Cap 2) full with [3, 3]. Wall 1 empty.
    
    p5 = JugadorAzul(id="5", name="AzulZero_MCTS", type="ai")
    p5.patrones[0] = [Color.BLUE] # ID 0
    p5.patrones[1] = [Color.BLACK, Color.BLACK] # ID 3
    
    # Wall is empty initially
    
    state = AzulGameState(jugadores={"5": p5})
    state.caja = []
    
    print(f"Before: Pattern 0: {p5.patrones[0]}, Wall 0,0: {p5.pared[0][0]}")
    move_tiles_to_wall(state, p5)
    print(f"After:  Pattern 0: {p5.patrones[0]}, Wall 0,0: {p5.pared[0][0]}")
    
    # Expected: Pattern 0 empty. Wall 0,0 has Blue (0).
    
    if len(p5.patrones[0]) > 0 and p5.pared[0][0] == Color.BLUE:
        print("BUG 2 REPRODUCED: Pattern not cleared!")
    elif len(p5.patrones[0]) == 0 and p5.pared[0][0] == Color.BLUE:
         print("Logic correct locally for cleanup.")

if __name__ == "__main__":
    test_disappearing_tiles()
    test_pattern_clearing()
