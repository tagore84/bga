import random
from app.core.ai_base import AIBase
from app.core.santorini.logic import SantoriniLogic

class RandomSantoriniAI(AIBase):
    def select_move(self, game_state):
        # game_state expected to have:
        # - board: 5x5 list of dicts
        # - current_turn: 'p1' or 'p2'
        
        board = game_state["board"]
        current_turn = game_state["current_turn"]
        
        # Get all valid full moves (move + build) from the logic helper
        valid_moves = SantoriniLogic.get_valid_moves(board, current_turn)
        
        if not valid_moves:
            return None # No moves available (Loss condition usually handled by game loop)
            
        # Pick a random valid move
        # Move format from logic: {'worker_start': (r,c), 'move_to': (r,c), 'build_at': (r,c)}
        selected_move = random.choice(valid_moves)
        
        return selected_move
