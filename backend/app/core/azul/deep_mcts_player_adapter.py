# backend/app/core/azul/ai_azul_deep_mcts.py

from app.core.ai_base import AIBase, register_ai
from typing import Any, Dict
import numpy as np

# Import from the correct location (Phase 3 architecture)
from app.core.azul.zero.deep_mcts_player import DeepMCTSPlayer

class AIAzulDeepMCTS(AIBase):
    def __init__(self, model_path: str, device: str = None, mcts_iters: int = 1, cpuct: float = 0):
        if device is None:
            import torch
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
            # MPS is not supported in Docker usually, but if running locally on Mac without docker it might be.
            # However, for safety in this environment (Docker), let's prefer CPU if not CUDA.
        
        self.player = DeepMCTSPlayer(model_path, device=device, mcts_iters=mcts_iters, cpuct=cpuct)
        print(f"AIAzulDeepMCTS loaded model from {model_path} on {device}")

    def select_move(self, state: Dict[str, Any]) -> int:
        """
        Convierte el estado del juego al formato esperado por el modelo
        y devuelve un entero codificado que represente la acción.
        """
        # DeepMCTSPlayer.predict expects a dict and returns a tuple (source, color, dest)
        action = self.player.predict(state)
        return self.encode_action(action)

    def encode_action(self, action: tuple) -> int:
        """
        Codifica una acción (source_idx, color, dest) como un entero único.
        """
        source_idx, color, dest = action
        return source_idx * 30 + color * 5 + dest
    
# Register with a default model path (can be updated)
# Note: Ensure 'modelos/checkpoint_best.pth' exists or update this path
import os
model_path = os.path.join(os.path.dirname(__file__), "zero/models/best.pt")
# Check if model exists before registering to avoid crash if missing
if os.path.exists(model_path):
    register_ai("azul_deep_mcts", AIAzulDeepMCTS(model_path))
else:
    print(f"Warning: Model not found at {model_path}. AIAzulDeepMCTS not registered.")