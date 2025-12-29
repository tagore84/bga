# tests/test_connect4_logic.py
import sys
import os

# Ensure backend directory is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app.routes.connect4.connect4 import _check_win, _drop_piece, ROWS, COLS

def test_drop_piece():
    board = [None] * 42
    # Drop in col 0
    idx = _drop_piece(board, 0, 'Red')
    # Should be at bottom row (row 5). Index = 5*7 + 0 = 35
    assert idx == 35, f"Expected 35, got {idx}"
    assert board[35] == 'Red'
    
    # Drop again in col 0
    idx = _drop_piece(board, 0, 'Blue')
    # Should be row 4. Index = 4*7 + 0 = 28
    assert idx == 28, f"Expected 28, got {idx}"
    assert board[28] == 'Blue'
    
    print("test_drop_piece PASSED")

def test_win_horizontal():
    board = [None] * 42
    # Row 5: R R R R
    board[35] = 'Red'
    board[36] = 'Red'
    board[37] = 'Red'
    board[38] = 'Red'
    
    assert _check_win(board, 'Red') == True
    assert _check_win(board, 'Blue') == False
    print("test_win_horizontal PASSED")

def test_win_vertical():
    board = [None] * 42
    # Col 0: R R R R (Rows 5,4,3,2)
    board[35] = 'Red'
    board[28] = 'Red'
    board[21] = 'Red'
    board[14] = 'Red'
    
    assert _check_win(board, 'Red') == True
    print("test_win_vertical PASSED")

def test_win_diagonal():
    board = [None] * 42
    # Diagonal /
    # Row 5, Col 0 (35)
    # Row 4, Col 1 (29)
    # Row 3, Col 2 (23)
    # Row 2, Col 3 (17)
    board[35] = 'Red'
    board[29] = 'Red'
    board[23] = 'Red'
    board[17] = 'Red'
    
    assert _check_win(board, 'Red') == True
    print("test_win_diagonal / PASSED")

def test_win_diagonal_inverse():
    board = [None] * 42
    # Diagonal \
    # Row 2, Col 0 (14)
    # Row 3, Col 1 (22)
    # Row 4, Col 2 (30)
    # Row 5, Col 3 (38)
    
    board[14] = 'Blue'
    board[22] = 'Blue'
    board[30] = 'Blue'
    board[38] = 'Blue'
    
    assert _check_win(board, 'Blue') == True
    print("test_win_diagonal \\ PASSED")

if __name__ == "__main__":
    test_drop_piece()
    test_win_horizontal()
    test_win_vertical()
    test_win_diagonal()
    test_win_diagonal_inverse()
