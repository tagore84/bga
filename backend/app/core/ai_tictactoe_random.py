# backend/app/core/ai_tictactoe_random.py
import random
from app.core.ai_base import AIBase, register_ai

class RandomTicTacToeAI(AIBase):
    def select_move(self, state):
        board = state["board"]
        empties = [i for i, c in enumerate(board) if c is None]
        return random.choice(empties)

# al importar este módulo, se registra
register_ai("RandomTicTacToe", RandomTicTacToeAI())