try:
    from app.core.nim.ai_nim import NimAI
    ai = NimAI()
    print("NimAI instantiated successfully.")
    
    # Test simple move
    state = {
        "board": [1, 3, 5, 7],
        "current_turn": "1"
    }
    move = ai.select_move(state)
    print(f"Test Move (Start): {move}")
    
    # Test Endgame
    state_end = {
        "board": [0, 0, 1, 0],
        "current_turn": "1"
    }
    move_end = ai.select_move(state_end)
    print(f"Test Move (Endgame): {move_end}")
    
except Exception as e:
    print(f"Error: {e}")
