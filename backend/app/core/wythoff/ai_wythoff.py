from app.core.ai_base import AIBase
from typing import Any, Dict
import math

class WythoffAI(AIBase):
    def __init__(self):
        self.phi = (1 + math.sqrt(5)) / 2

    def select_move(self, state: Dict[str, Any]) -> dict:
        """
        Wythoff Nim AI Strategy (Golden Ratio).
        Input state: 
        {
            "board": [count_pile_1, count_pile_2]
        }
        Returns:
        {
             "type": "standard" | "diagonal",
             "pile_index": int (optional, for standard),
             "count": int
        }
        """
        board = state.get("board", [0, 0])
        x, y = sorted(board) # x <= y
        
        # Check if current position is Cold (Losing)
        # Position is cold if x = floor(k*phi) and y = floor(k*phi^2) for some k
        # k = y - x
        k = y - x
        optimal_x = math.floor(k * self.phi)
        optimal_y = math.floor(k * self.phi * self.phi)
        
        if x == optimal_x and y == optimal_y:
            # We are in a losing position.
            # Make a random valid move (e.g., take 1 from larger pile, or standard)
            # Just take 1 from the largest pile
            valid_idx = 0 if board[0] > 0 else 1
            if board[1] > board[0]: valid_idx = 1
            
            return {
                "type": "standard",
                "pile_index": valid_idx,
                "count": 1
            }
            
        else:
            # We are in a Winning Position (Hot).
            # Find a move to reach a Cold position.
            
            # Possible move types:
            # 1. Reduce x (Standard on smaller/first pile) -> Reach (x', y) which is Cold?
            # 2. Reduce y (Standard on larger/second pile) -> Reach (x, y') which is Cold?
            # 3. Reduce both (Diagonal) -> Reach (x-c, y-c) which is Cold?
            
            # Only one Cold position exists for a given k (difference).
            # And for any x, there is only one Col position containing x.
            
            # Let's search for the reachable Cold position.
            
            # Case A: Reach a cold position with same difference k? 
            # Implies x, y change same amount -> Diagonal move.
            # Target is (optimal_x, optimal_y) for current k = y-x.
            # But x <= x and y <= y.
            # Wait, if we do diagonal, difference stays same? No.
            # Diagonal: (x-c, y-c). Difference (y-c) - (x-c) = y-x = k.
            # So if we maintain difference, we try to reach the Cold position for THIS k.
            if optimal_x < x and optimal_y < y:
                # We can reach (optimal_x, optimal_y) by diagonal move?
                diff_x = x - optimal_x
                diff_y = y - optimal_y
                if diff_x == diff_y and diff_x > 0:
                    return {
                        "type": "diagonal",
                        "count": diff_x
                    }
            
            # Case B: Standard move. Changes difference.
            # We iterate through all Cold positions (k=0, 1, 2...) closer to origin.
            
            # Limit k search space. Max k roughly max(board)
            max_val = max(x, y)
            
            for k_chk in range(max_val + 2):
                nx = math.floor(k_chk * self.phi)
                ny = math.floor(k_chk * self.phi * self.phi) # ny = nx + k_chk
                
                # We have cold position (nx, ny).
                # Note: (ny, nx) is symmetric equivalent.
                
                # Can we reach (nx, ny) from (x, y) by removing from ONE pile?
                
                # Check target (nx, ny)
                # 1. y is constant (remove from x). Target must have y component same as current y? No.
                # Standard move modifies ONE value. The other value persists.
                
                # Subcase: Keep y, change x to x'
                # Is x' in {nx, ny}?
                # Meaning: is y in {nx, ny}?
                if y == ny:
                    # We need x -> nx.
                    if nx < x:
                        # Remove x - nx from pile x
                         # But board is sorted x, y. Pile indices might be swapped.
                         # We need to map back to original indices.
                         pile_to_reduce_val = x
                         target_val = nx
                         diff = pile_to_reduce_val - target_val
                         
                         # Find which index had x
                         # board is [b0, b1].
                         # if b0==x, idx=0. Else idx=1.
                         # CAREFUL if x==y.
                         idx = 0 if board[0] == x else 1
                         # Actually if x==y, pick any.
                         
                         return {"type": "standard", "pile_index": idx, "count": diff}
                
                if y == nx:
                    # We need x -> ny.
                    if ny < x:
                         idx = 0 if board[0] == x else 1
                         return {"type": "standard", "pile_index": idx, "count": x - ny}
                         
                # Subcase: Keep x, change y to y'
                # Is x in {nx, ny}?
                if x == nx:
                    # We need y -> ny
                    if ny < y:
                         idx = 0 if board[0] == y else 1 # y usually >= x. 
                         # if x==y, and we want to reduce to ny (<x), both are candidates.
                         # But ny < y.
                         # If board=[5,5], x=5, y=5. nx=2, ny=3. (k=1).
                         # x!=nx.
                         
                         # If board=[3,5], x=3, y=5. k=2, nx=3, ny=4.
                         # x==nx (3==3). Need y(5)->ny(4). Remove 1 from pile with 5.
                         if board[0] == y: idx=0
                         else: idx=1
                         
                         return {"type": "standard", "pile_index": idx, "count": y - ny}
                
                if x == ny:
                    # We need y -> nx
                    if nx < y:
                        idx = 0 if board[0] == y else 1
                        return {"type": "standard", "pile_index": idx, "count": y - nx}
                        
            # If we fall through here (shouldn't if logic is sound and position is Hot),
            # fallback to random.
            return {
                "type": "standard",
                "pile_index": 0,
                "count": 1
            }
