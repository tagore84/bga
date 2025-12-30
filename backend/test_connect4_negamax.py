import sys
import os

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.connect4.ai_connect4_negamax import NegamaxConnect4AI

def test_negamax_ai():
    print("Testing NegamaxConnect4AI...")
    ai = NegamaxConnect4AI(depth=2)

    # 1. Test Block Win
    # Board state where Red is about to win horizontally
    # 0 0 0 0 0 0 0
    # ...
    # R R R . . . .
    # Blue (AI) must play col 3 to block
    board = [None] * 42
    # Set up R R R in bottom row cols 0, 1, 2
    board[0*7 + 0] = 'Red'
    board[0*7 + 1] = 'Red'
    board[0*7 + 2] = 'Red'
    
    game_state = {
        "board": board,
        "current_turn": "Blue", # AI is Blue, needs to block Red
        "config": {}
    }

    print("Test 1: Check if AI blocks immediate win.")
    col = ai.select_move(game_state)
    print(f"AI Selected: {col}")
    if col == 3:
        print("PASS: AI blocked winning move.")
    else:
        print(f"FAIL: AI selected {col}, expected 3.")

    # 2. Test Take Win
    # Same board, but now it's Red's turn (AI is Red). AI should play 3 to win.
    game_state["current_turn"] = "Red"
    print("\nTest 2: Check if AI takes immediate win.")
    col = ai.select_move(game_state)
    print(f"AI Selected: {col}")
    if col == 3:
        print("PASS: AI took winning move.")
    else:
        print(f"FAIL: AI selected {col}, expected 3.")
        
    # 3. Test Invalid Move Avoidance (Full Col)
    # Fill column 0
    for r in range(6):
        board[r*7 + 0] = 'Red'
    
    # AI should not pick 0
    game_state["current_turn"] = "Blue"
    print("\nTest 3: Check if AI avoids full column.")
    col = ai.select_move(game_state)
    print(f"AI Selected: {col}")
    if col != 0:
        print("PASS: AI did not pick full column.")
    else:
        print("FAIL: AI picked full column 0.")

if __name__ == "__main__":
    test_negamax_ai()
