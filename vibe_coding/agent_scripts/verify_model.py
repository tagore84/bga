
from typing import Optional
from pydantic import BaseModel

# Copy of the class from backend/app/routes/chess/chess.py
class ChessGameState(BaseModel):
    id: int
    board_fen: str
    current_turn: str
    status: str
    white_player_name: Optional[str]
    black_player_name: Optional[str]
    white_player_id: Optional[int]
    black_player_id: Optional[int]
    config: dict

def test_model():
    data = {
        "id": 1,
        "board_fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        "current_turn": "white",
        "status": "in_progress",
        "white_player_name": "Alice",
        "black_player_name": "Bob",
        "white_player_id": 10,
        "black_player_id": 20,
        "config": {"time": 10}
    }
    
    try:
        game = ChessGameState(**data)
        print("Model instantiation SUCCESS")
        print(game.json())
        
        # Verify fields
        assert game.white_player_id == 10
        assert game.black_player_id == 20
        print("Fields verified successfully")
        
    except Exception as e:
        print(f"Model instantiation FAILED: {e}")

if __name__ == "__main__":
    test_model()
