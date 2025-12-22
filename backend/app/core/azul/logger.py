import os
import json
from datetime import datetime

class AzulGameLogger:
    def __init__(self, base_dir="logs/azul_games"):
        # Ensure absolute path based on backend root if needed, but assuming CWD is backend root
        # If running in docker, /app is root.
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def log_move(self, game_id: int, move: dict, player_id: int, state_before: dict, state_after: dict):
        """
        Logs a move event to the game's log file.
        """
        filename = os.path.join(self.base_dir, f"game_{game_id}.jsonl")
        
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "game_id": game_id,
            "player_id": player_id,
            "move": move,
            "state_before": state_before,
            "state_after": state_after
        }
        
        try:
            with open(filename, 'a') as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            print(f"Error writing to game log {filename}: {e}")

# Global instance or create per use? Global is fine.
game_logger = AzulGameLogger()
