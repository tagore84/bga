# backend/app/core/azul/ai_azul_deep_mcts.py

from app.core.ai_base import AIBase, register_ai
from typing import Any, Dict
import numpy as np

# Import from the correct location (Phase 3 architecture)
from app.core.azul.zero.deep_mcts_player import DeepMCTSPlayer
from app.core.azul.adapter import bga_state_to_azul_zero_obs
from app.models.azul.azul import AzulMove, Color

class AIAzulDeepMCTS(AIBase):
    def __init__(self, model_path: str, device: str = None, mcts_iters: int = 1, cpuct: float = 0, single_player_mode=True):
        if device is None:
            import torch
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
            # MPS is not supported in Docker usually, but if running locally on Mac without docker it might be.
            # However, for safety in this environment (Docker), let's prefer CPU if not CUDA.
        
        self.player = DeepMCTSPlayer(model_path, device=device, mcts_iters=mcts_iters, cpuct=cpuct, single_player_mode=single_player_mode)
        print(f"AIAzulDeepMCTS loaded model from {model_path} on {device}")

    def select_move(self, state: Any) -> AzulMove:
        """
        Convierte el estado del juego al formato esperado por el modelo
        y devuelve una AzulMove.
        """
        # Convert BGA state to AzulZero observation
        obs, _ = bga_state_to_azul_zero_obs(state)
        
        # DeepMCTSPlayer.predict expects a dict and returns a tuple (source, color, dest)
        action = self.player.predict(obs)
        
        return self._action_to_move(action, state)

    def _action_to_move(self, action: tuple, state) -> AzulMove:
        source_idx, color, dest = action
        
        # Map source_idx to factory ID or "centro"
        # Note: state might be a dict or valid object depending on context, 
        # but usually it's AzulGameState here.
        # AzulGameState has 'expositores' (list of lists).
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

# Register with a default model path (can be updated)
# Note: Ensure 'modelos/checkpoint_best.pth' exists or update this path
import os
model_path = os.path.join(os.path.dirname(__file__), "zero/models/best.pt")
# Check if model exists before registering to avoid crash if missing
if os.path.exists(model_path):
    register_ai("azul_deep_mcts", AIAzulDeepMCTS(model_path))
    register_ai("Experimental", AIAzulDeepMCTS(model_path))
else:
    print(f"Warning: Model not found at {model_path}. AIAzulDeepMCTS not registered.")