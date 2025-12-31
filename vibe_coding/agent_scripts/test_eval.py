import sys
import os
import chess

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.core.chess.ai_chess_minimax import MinimaxChessAI

def test_eval():
    ai = MinimaxChessAI(depth=0)
    
    # Start pos
    board = chess.Board()
    score = ai.evaluate_board(board)
    print(f"Start pos score: {score}") # Should be 0
    
    # White advantage (remove black pawn)
    board = chess.Board()
    board.remove_piece_at(chess.D7)
    score = ai.evaluate_board(board)
    print(f"White advantage score: {score}") # Should be positive (remove black piece means less negative)
    
    # Black advantage (remove white queen)
    board = chess.Board()
    board.remove_piece_at(chess.D1)
    score = ai.evaluate_board(board)
    print(f"Black advantage score: {score}") # Should be negative

    # Real game FEN
    fen = "rn1qkbnr/pbpppp2/1p4p1/7p/3PP3/2P2P2/PP4PP/RNBQKBNR w KQkq - 1 5"
    board = chess.Board(fen)
    score = ai.evaluate_board(board)
    print(f"Real game FEN score: {score}")

if __name__ == "__main__":
    test_eval()
