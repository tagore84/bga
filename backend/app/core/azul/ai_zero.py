import sys
import os

# Add the 'zero' directory to sys.path so that internal imports in synced files (like 'from net import...') work
zero_dir = os.path.join(os.path.dirname(__file__), 'zero')
if zero_dir not in sys.path:
    sys.path.append(zero_dir)

from app.core.ai_base import AIBase, register_ai
from app.core.azul.zero.deep_mcts_player import DeepMCTSPlayer
from app.core.azul.zero.random_plus_player import RandomPlusPlayer
from app.models.azul.azul import AzulMove, Color
from app.core.azul.adapter import bga_state_to_azul_zero_obs


class AzulZeroMCTS(AIBase):
    def __init__(self, model_path: str, device: str = 'cpu', mcts_iters: int = 1, cpuct: float = 0.0, temperature: float = 0.0):
        # Resolve absolute path if needed
        if not os.path.isabs(model_path):
            # Asumimos que es relativo a backend/
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
            # Actually, let's just use the path provided, assuming CWD is backend root or handled correctly.
            # But DeepMCTSPlayer loads it directly.
            pass
            
        self.player = DeepMCTSPlayer(model_path, device=device, mcts_iters=mcts_iters, cpuct=cpuct, temperature=temperature)
        print(f"AzulZeroMCTS loaded model from {model_path}")

    def select_move(self, state) -> AzulMove:
        obs, player_ids = bga_state_to_azul_zero_obs(state)
        
        # DeepMCTSPlayer.predict returns (source_idx, color, dest) tuple
        action = self.player.predict(obs)
        
        if action is None:
            raise RuntimeError(f"AzulZeroMCTS ({self.player}) returned None action. Obs: {obs}")

        return self._action_to_move(action, state)

    def _action_to_move(self, action: tuple, state) -> AzulMove:
        source_idx, color, dest = action
        
        # Map source_idx to factory ID or "centro"
        num_factories = len(state.expositores)
        
        if source_idx < num_factories:
            factory_val = str(source_idx)
        else:
            factory_val = "centro"
            
        # Map dest to row (1-5) or 0 (floor)
        if dest == 5:
            row_val = 0
        else:
            row_val = dest + 1
            
        return AzulMove(factory=factory_val, color=Color(color), row=row_val)

class AzulZeroRandomPlus(AIBase):
    def __init__(self):
        self.player = RandomPlusPlayer()

    def select_move(self, state) -> AzulMove:
        obs, player_ids = bga_state_to_azul_zero_obs(state)
        action = self.player.predict(obs)
        
        if action is None:
             # Fallback or raise error
             raise RuntimeError(f"AzulZeroRandomPlus returned None action. Obs factories: {obs['factories']}, center: {obs['center']}")
             
        return self._action_to_move(action, state)

    def _action_to_move(self, action: tuple, state) -> AzulMove:
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

from app.core.azul.zero.heuristic_player import HeuristicPlayer

class AzulZeroHeuristic(AIBase):
    def __init__(self):
        self.player = HeuristicPlayer()

    def select_move(self, state) -> AzulMove:
        obs, player_ids = bga_state_to_azul_zero_obs(state)
        action = self.player.predict(obs)
        
        if action is None:
             raise RuntimeError(f"AzulZeroHeuristic returned None action. Obs: {obs}")
             
        return self._action_to_move(action, state)

    def _action_to_move(self, action: tuple, state) -> AzulMove:
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

# Register players
# Use path relative to this file
model_path = os.path.join(os.path.dirname(__file__), "zero/models/best.pt")
if os.path.exists(model_path):
    register_ai("AzulZero_MCTS", AzulZeroMCTS(model_path))
else:
    print(f"Warning: Model not found at {model_path}, skipping AzulZero_MCTS registration")

register_ai("AzulZero_RandomPlus", AzulZeroRandomPlus())
register_ai("AzulZero_Heuristic", AzulZeroHeuristic())
