import copy
import random
import logging
from app.core.ai_base import AIBase

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Constants
ROWS = 6
COLS = 7
EMPTY = None
PLAYER_PIECE = 'Red' # This will be dynamic based on who the AI is
AI_PIECE = 'Blue'    # This will be dynamic

# Scoring
WIN_SCORE = 1000000000
LOSE_SCORE = -1000000000
DRAW_SCORE = 0

class NegamaxConnect4AI(AIBase):
    def __init__(self, depth: int = 4):
        self.depth = depth
        print(f"[{self.__class__.__name__}] Initialized Negamax (Safeguarded v2) with depth={depth}")

    def select_move(self, game_state):
        # game_state: { "board": [...], "current_turn": "Red"|"Blue", ... }
        board = game_state["board"]
        # AI is whoever's turn it is RIGHT NOW
        ai_piece = game_state["current_turn"]
        opponent_piece = "Blue" if ai_piece == "Red" else "Red"

        logger.info(f"[{self.__class__.__name__}] select_move called. Turn={ai_piece}")

        col, minimax_score = self.minimax(board, self.depth, -float('inf'), float('inf'), True, ai_piece, opponent_piece)
        
        logger.info(f"[{self.__class__.__name__}] Minimax Result: col={col}, score={minimax_score}")

        if col is None:
            # Fallback: If minimax returns None (e.g. believes terminal), but we must move:
            valid_locs = self.get_valid_locations(board)
            if valid_locs:
                fallback = random.choice(valid_locs)
                logger.warning(f"[{self.__class__.__name__}] Minimax returned None. Falling back to random: {fallback}")
                return fallback
            else:
                 # No moves possible.
                logger.info(f"[{self.__class__.__name__}] No valid moves found.")
                # Log explicitly that we are returning 0
                logger.info(f"[{self.__class__.__name__}] Returning 0 as last resort.")
                return 0 # Return a dummy column, downstream will fail to drop piece gracefully

        return col

    def _get_piece(self, board, row, col):
        if 0 <= row < ROWS and 0 <= col < COLS:
            return board[row * COLS + col]
        return None

    def _drop_piece(self, board, col, piece):
        # Helper to simulate drop. Returns NEW board copy or None if invalid.
        # However, to save memory in recursion, we might want to mutate and undo.
        # But for Python/simplicity, let's copy for now or find the index to mutate.
        
        # Find lowest empty
        for r in range(ROWS - 1, -1, -1):
            if self._get_piece(board, r, col) is None:
                board[r * COLS + col] = piece
                return True
        return False

    def is_valid_location(self, board, col):
        return self._get_piece(board, 0, col) is None

    def get_valid_locations(self, board):
        valid_locations = []
        for col in range(COLS):
            if self.is_valid_location(board, col):
                valid_locations.append(col)
        return valid_locations

    def winning_move(self, board, piece):
        # Check horizontal locations for win
        for c in range(COLS - 3):
            for r in range(ROWS):
                if (self._get_piece(board, r, c) == piece and 
                    self._get_piece(board, r, c+1) == piece and 
                    self._get_piece(board, r, c+2) == piece and 
                    self._get_piece(board, r, c+3) == piece):
                    return True

        # Check vertical locations for win
        for c in range(COLS):
            for r in range(ROWS - 3):
                if (self._get_piece(board, r, c) == piece and 
                    self._get_piece(board, r+1, c) == piece and 
                    self._get_piece(board, r+2, c) == piece and 
                    self._get_piece(board, r+3, c) == piece):
                    return True

        # Check positively sloped diaganols
        for c in range(COLS - 3):
            for r in range(ROWS - 3):
                if (self._get_piece(board, r, c) == piece and 
                    self._get_piece(board, r+1, c+1) == piece and 
                    self._get_piece(board, r+2, c+2) == piece and 
                    self._get_piece(board, r+3, c+3) == piece):
                    return True

        # Check negatively sloped diaganols
        for c in range(COLS - 3):
            for r in range(3, ROWS):
                if (self._get_piece(board, r, c) == piece and 
                    self._get_piece(board, r-1, c+1) == piece and 
                    self._get_piece(board, r-2, c+2) == piece and 
                    self._get_piece(board, r-3, c+3) == piece):
                    return True
        return False

    def evaluate_window(self, window, piece, opponent_piece):
        score = 0
        
        if window.count(piece) == 4:
            score += 100
        elif window.count(piece) == 3 and window.count(EMPTY) == 1:
            score += 5
        elif window.count(piece) == 2 and window.count(EMPTY) == 2:
            score += 2

        if window.count(opponent_piece) == 3 and window.count(EMPTY) == 1:
            score -= 4

        return score

    def score_position(self, board, piece, opponent_piece):
        score = 0

        # Score center column preferences
        center_array = [self._get_piece(board, r, COLS // 2) for r in range(ROWS)]
        center_count = center_array.count(piece)
        score += center_count * 3

        # Score Horizontal
        for r in range(ROWS):
            row_array = [self._get_piece(board, r, c) for c in range(COLS)]
            for c in range(COLS - 3):
                window = row_array[c:c+4]
                score += self.evaluate_window(window, piece, opponent_piece)

        # Score Vertical
        for c in range(COLS):
            col_array = [self._get_piece(board, r, c) for r in range(ROWS)]
            for r in range(ROWS - 3):
                window = col_array[r:r+4]
                score += self.evaluate_window(window, piece, opponent_piece)

        # Score positive sloped diagonal
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                window = [self._get_piece(board, r+i, c+i) for i in range(4)]
                score += self.evaluate_window(window, piece, opponent_piece)

        # Score negative sloped diagonal
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                window = [self._get_piece(board, r+3-i, c+i) for i in range(4)]
                score += self.evaluate_window(window, piece, opponent_piece)

        return score

    def is_terminal_node(self, board, piece, opponent_piece):
        return self.winning_move(board, piece) or self.winning_move(board, opponent_piece) or len(self.get_valid_locations(board)) == 0

    def minimax(self, board, depth, alpha, beta, maximizingPlayer, ai_piece, opponent_piece):
        # NOTE: calling this 'minimax' but it's minimax with alpha-beta.
        
        valid_locations = self.get_valid_locations(board)
        is_terminal = self.is_terminal_node(board, ai_piece, opponent_piece)
        
        if depth == 0 or is_terminal:
            if is_terminal:
                if self.winning_move(board, ai_piece):
                    return (None, WIN_SCORE)
                elif self.winning_move(board, opponent_piece):
                    return (None, LOSE_SCORE)
                else: # Game is over, no more valid moves
                    return (None, DRAW_SCORE)
            else: # Depth is zero
                return (None, self.score_position(board, ai_piece, opponent_piece))

        if maximizingPlayer:
            value = -float('inf')
            # Randomize order to add variety to equal moves and fix bias
            if not valid_locations:
                return (None, value)
            
            random.shuffle(valid_locations)
            column = valid_locations[0] # Default to first in shuffled list
            
            for col in valid_locations:
                b_copy = list(board) # Copy the list (board is flat list)
                self._drop_piece(b_copy, col, ai_piece)
                new_score = self.minimax(b_copy, depth-1, alpha, beta, False, ai_piece, opponent_piece)[1]
                
                if depth == self.depth:
                     logger.info(f"[Negamax] Top-level move consideration: Col {col}, Score {new_score}")

                if new_score > value:
                    value = new_score
                    column = col
                
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return column, value

        else: # Minimizing player
            value = float('inf')
            if not valid_locations:
                 return (None, value)

            random.shuffle(valid_locations)
            column = valid_locations[0]
            
            for col in valid_locations:
                b_copy = list(board)
                self._drop_piece(b_copy, col, opponent_piece)
                new_score = self.minimax(b_copy, depth-1, alpha, beta, True, ai_piece, opponent_piece)[1]
                
                if new_score < value:
                    value = new_score
                    column = col
                
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return column, value
