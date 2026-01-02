

import sys
import os

sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.core.santorini.logic import SantoriniLogic

def test_initial_board():
    board = SantoriniLogic.initialize_board()
    assert len(board) == 5
    assert len(board[0]) == 5
    assert board[0][0] == {'level': 0, 'worker': None}

def test_moves():
    board = SantoriniLogic.initialize_board()
    
    # Place worker at 1,1
    board[1][1]['worker'] = 'p1'
    
    # Valid moves should include moving to 0,0; 0,1; 0,2 etc.
    moves = SantoriniLogic.get_valid_moves(board, 'p1')
    
    # At (1,1), surrounding cells are 8.
    # From each new pos, there are roughly 8 build spots.
    # Total moves ~ 8 * 8 = 64 (minus edge cases, occupancy etc)
    
    assert len(moves) > 0
    
    # Check a specific expected move
    # Move to 0,0, Build at 0,1
    expected = {
        'worker_start': (1,1),
        'move_to': (0,0),
        'build_at': (0,1)
    }
    
    assert expected in moves

def test_cannot_move_up_two():
    board = SantoriniLogic.initialize_board()
    board[1][1]['worker'] = 'p1'
    board[0][0]['level'] = 2 # Cliff
    
    moves = SantoriniLogic.get_valid_moves(board, 'p1')
    
    # Move to 0,0 should NOT be valid
    move_to_cliff = [m for m in moves if m['move_to'] == (0,0)]
    assert len(move_to_cliff) == 0

def test_win_condition():
    board = SantoriniLogic.initialize_board()
    board[1][1]['worker'] = 'p1'
    board[0][0]['level'] = 3 # Winning spot
    
    # Execute move to 0,0
    move = {
        'worker_start': (1,1),
        'move_to': (0,0),
        'build_at': (0,1) # irrelevant for win trigger but needed for call
    }
    
    new_board, status = SantoriniLogic.apply_move(board, move, 'p1')
    assert status == 'p1_won'

if __name__ == "__main__":
    # Manually run tests if executed directly
    try:
        test_initial_board()
        test_moves()
        test_cannot_move_up_two()
        test_win_condition()
        print("All tests passed!")
    except AssertionError as e:
        print(f"Test failed: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
