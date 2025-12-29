# backend/app/core/connect4/ai_connect4_random.py
import random
from app.core.ai_base import AIBase

class RandomConnect4AI(AIBase):
    def select_move(self, game_state):
        # game_state has "board" (list of 42), "current_turn", "config"
        board = game_state["board"]
        
        # Identify valid columns
        # Board is 6 rows x 7 cols. 
        # Row 0 is top. If board[0 * 7 + c] is None, then column c is not full.
        valid_cols = []
        for c in range(7):
            if board[c] is None:
                valid_cols.append(c)
                
        if not valid_cols:
            return -1 # Should not happen in progress game
            
        return random.choice(valid_cols)
