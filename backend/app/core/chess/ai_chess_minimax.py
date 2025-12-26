# backend/app/core/chess/ai_chess_minimax.py
import chess
import random
from app.core.ai_base import AIBase, register_ai

from app.core.chess.pst import TABLES, PIECE_VALUES

MATE_SCORE = 30000

MATE_SCORE = 9999

class MinimaxChessAI(AIBase):
    def __init__(self, depth=2):
        self.depth = depth

    def select_move(self, state):
        fen = state.get("board_fen")
        if not fen:
            return None
        board = chess.Board(fen)
        best_move = self.alphabeta_root(board, self.depth)
        return best_move.uci() if best_move else None

    def evaluate_board(self, board):
        if board.is_checkmate():
            # side to move is checkmated
            return -MATE_SCORE if board.turn == chess.WHITE else MATE_SCORE
        if board.is_stalemate() or board.is_insufficient_material():
            return 0

        score = 0
        for sq in chess.SQUARES:
            p = board.piece_at(sq)
            if not p:
                continue
            
            # Material
            material = PIECE_VALUES.get(p.piece_type, 0)
            
            # Positional
            # Tables are defined for White relative to a1(0)..h8(63).
            # If piece is black, we need to map square to white's perspective (mirror rank)
            # or just define tables for black.
            # Usually: square ^ 56 flips the rank (a8 becomes a1)
            
            if p.color == chess.WHITE:
                pst_val = TABLES[p.piece_type][sq]
                score += (material + pst_val)
            else:
                # Flip square vertically for Black
                # 0->56, 1->57..., 56->0
                # Use chess.square_mirror(sq) if available or manual
                mirror_sq = chess.square_mirror(sq)
                pst_val = TABLES[p.piece_type][mirror_sq]
                score -= (material + pst_val)
                
        return score

    def alphabeta_root(self, board, depth):
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return None

        # Mejor ordenación simple: capturas primero (ayuda mucho a alpha-beta)
        random.shuffle(legal_moves)
        legal_moves.sort(key=lambda m: board.is_capture(m), reverse=True)

        is_maximizing = (board.turn == chess.WHITE)
        best_move = None
        best_value = -float('inf') if is_maximizing else float('inf')

        alpha = -float('inf')
        beta = float('inf')

        for move in legal_moves:
            board.push(move)
            value = self.alphabeta(board, depth - 1, alpha, beta, not is_maximizing)
            board.pop()

            if is_maximizing:
                if value > best_value:
                    best_value = value
                    best_move = move
                alpha = max(alpha, best_value)
            else:
                if value < best_value:
                    best_value = value
                    best_move = move
                beta = min(beta, best_value)

            # Poda en root también
            if beta <= alpha:
                break

        return best_move

    def alphabeta(self, board, depth, alpha, beta, is_maximizing):
        if depth == 0 or board.is_game_over():
            return self.evaluate_board(board)

        legal_moves = list(board.legal_moves)

        # Ordenación simple: capturas primero
        random.shuffle(legal_moves)
        legal_moves.sort(key=lambda m: board.is_capture(m), reverse=True)

        if is_maximizing:
            value = -float('inf')
            for move in legal_moves:
                board.push(move)
                value = max(value, self.alphabeta(board, depth - 1, alpha, beta, False))
                board.pop()
                alpha = max(alpha, value)
                if beta <= alpha:
                    break
            return value
        else:
            value = float('inf')
            for move in legal_moves:
                board.push(move)
                value = min(value, self.alphabeta(board, depth - 1, alpha, beta, True))
                board.pop()
                beta = min(beta, value)
                if beta <= alpha:
                    break
            return value