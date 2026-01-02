import chess
import random

def test_chess960_generation():
    print("Testing Chess 960 Generation...")
    
    # 1. Generate a few random positions
    fens = set()
    for _ in range(10):
        scharnagl = random.randint(0, 959)
        board = chess.Board.from_chess960_pos(scharnagl)
        board.chess960 = True
        fen = board.fen()
        fens.add(fen)
        print(f"Generated (ID {scharnagl}): {fen}")
        
        # Verify it's a valid board
        assert board.status() == chess.Status.VALID
        
    # Check that we got different positions (statistically likely)
    if len(fens) > 1:
        print("PASS: Generated multiple distinct starting positions.")
    else:
        print("WARNING: Generated identical positions (unlikely unless randint is broken or range is 1).")

    # 2. Check Standard Position is possible (ID 518)
    board_std = chess.Board.from_chess960_pos(518)
    std_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    if board_std.fen() == std_fen:
         print("PASS: ID 518 matches Standard Chess start position.")
    else:
         print(f"FAIL: ID 518 should be standard. Got: {board_std.fen()}")

if __name__ == "__main__":
    test_chess960_generation()
