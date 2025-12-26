# backend/app/core/chess/ai_chess_random.py
import random
import chess
from app.core.ai_base import AIBase, register_ai

class RandomChessAI(AIBase):
    def select_move(self, state):
        """
        state dict expected to have:
          - "board_fen": str
        """
        fen = state.get("board_fen")
        if not fen:
            # Fallback or error
            return None
        
        board = chess.Board(fen)
        legal_moves = list(board.legal_moves)
        
        if not legal_moves:
            return None
            
        move = random.choice(legal_moves)
        return move.uci()

# RandomChessAI registration is now handled in init_chess_ais.py