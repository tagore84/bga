from app.core.ai_base import AIBase, register_ai
import sys
import os

# Add the 'zero' directory to sys.path so that internal imports work
zero_dir = os.path.join(os.path.dirname(__file__), 'zero')
if zero_dir not in sys.path:
    sys.path.append(zero_dir)

from app.core.azul.zero.heuristic_min_max_mcts_player import HeuristicMinMaxMCTSPlayer, decode_action
from app.core.azul.adapter import bga_state_to_azul_zero_obs
from app.models.azul.azul import AzulMove, Color
import numpy as np

class HeuristicMinMaxMctsAdapter(AIBase):
    def __init__(self, strategy='minmax', simulations=50, depth=2):
        self.player = HeuristicMinMaxMCTSPlayer(strategy=strategy, simulations=simulations, depth=depth)

    def select_move(self, state) -> AzulMove:
        # Convert BGA state to Obs
        obs, _ = bga_state_to_azul_zero_obs(state)
        
        # Predict
        action_idx = self.player.predict(obs) # Returns int
        
        if action_idx is None:
             raise RuntimeError(f"HeuristicMinMaxMCTSPlayer returned None action")

        # Decode int -> tuple
        # decode_action is available in heuristic_min_max_mcts_player
        action_tuple = decode_action(int(action_idx))
        
        return self._action_to_move(action_tuple, state)

    def _action_to_move(self, action: tuple, state) -> AzulMove:
        # Helper to convert internal tuple (source, color, dest) to AzulMove
        source_idx, color, dest = action
        num_factories = len(state.expositores)
        
        if source_idx < num_factories:
            factory_val = str(source_idx)
        else:
            factory_val = "centro"
            
        if dest == 5:
            row_val = 0
        else:
            row_val = dest + 1
            
        return AzulMove(factory=factory_val, color=Color(color), row=row_val)

# Register configurations
# 1. MinMax (depth 2)
# 1. MinMax
register_ai("MinMax_low", HeuristicMinMaxMctsAdapter(strategy='minmax', depth=2))
register_ai("MinMax_high", HeuristicMinMaxMctsAdapter(strategy='minmax', depth=4))

# 2. MCTS Low (50 simulations)
register_ai("MCTS_low", HeuristicMinMaxMctsAdapter(strategy='mcts', simulations=50))

# 3. MCTS High (300 simulations)
# 3. MCTS High (300 simulations)
register_ai("MCTS_high", HeuristicMinMaxMctsAdapter(strategy='mcts', simulations=300))

# 4. Localized Aliases
register_ai("Medio", HeuristicMinMaxMctsAdapter(strategy='minmax', depth=2))
register_ai("Difícil", HeuristicMinMaxMctsAdapter(strategy='minmax', depth=4))
