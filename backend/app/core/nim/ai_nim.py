from app.core.ai_base import AIBase
from typing import Any, Dict
import random

class NimAIExpert(AIBase):
    def select_move(self, state: Dict[str, Any]) -> dict:
        """
        Nim Misere AI Strategy (Optimal).
        """
        board = state.get("board", [])
        
        # Calculate Nim-sum
        nim_sum = 0
        for count in board:
            nim_sum ^= count
            
        # Check if we are in the endgame case (all piles size 0 or 1)
        piles_gt_1 = [i for i, c in enumerate(board) if c > 1]
        is_endgame = (len(piles_gt_1) == 0)
        
        move = None
        
        if is_endgame:
            # End game strategy for Misere:
            # We want to leave an ODD number of piles with size 1.
            piles_1 = [i for i, c in enumerate(board) if c == 1]
            count_1 = len(piles_1)
            
            if count_1 % 2 == 1:
                # Odd number of piles of size 1. Losing position.
                move = {"pile_index": piles_1[0], "count": 1}
            else:
                # Even number of piles of size 1. Winning position.
                move = {"pile_index": piles_1[0], "count": 1}
        
        else:
            # Normal play
            if nim_sum != 0:
                for i, count in enumerate(board):
                    target = count ^ nim_sum
                    if target < count:
                        amount_to_remove = count - target
                        
                        # Misere transition check
                        remaining_piles_gt_1 = 0
                        for j, c in enumerate(board):
                            if j == i:
                                if target > 1:
                                    remaining_piles_gt_1 += 1
                            else:
                                if c > 1:
                                    remaining_piles_gt_1 += 1
                                    
                        if remaining_piles_gt_1 == 0:
                            # This move forces endgame. Ensure ODD 1s.
                            count_1s = 0
                            for j, c in enumerate(board):
                                val = target if j == i else c
                                if val == 1:
                                    count_1s += 1
                                    
                            if count_1s % 2 == 0:
                                # Adjust to leave ODD 1s
                                p_board = list(board)
                                p_board[i] -= amount_to_remove
                                
                                # We either remove 1 more or 1 less to toggle parity of 1s
                                # If target was 0 ( removed 'amount'), make it 1 (remove amount-1)
                                # If target was 1 ( removed 'amount'), make it 0 (remove amount+1)
                                if (count - amount_to_remove) == 0:
                                     amount_to_remove -= 1
                                else:
                                     amount_to_remove += 1
                                     
                        move = {"pile_index": i, "count": amount_to_remove}
                        return move
                        
            if move is None:
                 # Losing position, take 1 from first available
                 for i, count in enumerate(board):
                     if count > 0:
                         return {"pile_index": i, "count": 1}
                         
        return move

class NimAIIntermediate(AIBase):
    def __init__(self):
        self.expert = NimAIExpert()

    def select_move(self, state: Dict[str, Any]) -> dict:
        """
        Intermediate Strategy:
        30% chance to make a random mistake.
        70% chance to play optimally.
        """
        # Valid moves
        board = state.get("board", [])
        valid_moves = []
        for i, count in enumerate(board):
            for c in range(1, count + 1):
                valid_moves.append({"pile_index": i, "count": c})
        
        if not valid_moves:
             return {} # Should not happen

        if random.random() < 0.3:
            # Make a mistake: Pick random move
            return random.choice(valid_moves)
        else:
            # Play optimal
            return self.expert.select_move(state)

# For backward compatibility if needed, though we actally update seed.
NimAI = NimAIExpert
