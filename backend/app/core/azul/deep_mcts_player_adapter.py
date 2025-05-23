# backend/app/core/azul/ai_azul_deep_mcts.py

from app.core.ai_base import AIBase
from typing import Any, Dict
import numpy as np

from backend.app.core.azul.deep_mcts_player import DeepMCTSPlayer

class AIAzulDeepMCTS(AIBase):
    def __init__(self, model_path: str, device: str = 'cpu', mcts_iters: int = 200, cpuct: float = 1.0):
        self.player = DeepMCTSPlayer(model_path, device=device, mcts_iters=mcts_iters, cpuct=cpuct)
        print(f"AIAzulDeepMCTS loaded model from {model_path}")

    def select_move(self, state: Dict[str, Any]) -> int:
        """
        Convierte el estado del juego al formato esperado por el modelo
        y devuelve un entero codificado que represente la acción.
        """
        action = self.player.predict(state)
        return self.encode_action(action)

    def encode_observation(self, obs: dict) -> np.ndarray:
        """
        Encode the observation dict into a flat numpy array.
        """
        # parts: bag, discard, factories, center
        parts = [
            obs['bag'],
            obs['discard'],
            obs['factories'].flatten(),
            obs['center'],
            np.array([int(obs['first_player_token'])], dtype=int)
        ]
        # players pattern_lines padded to 5x5
        pattern = []
        for p in obs['players']:
            plines = np.full((5, 5), -1, dtype=int)
            for i, line in enumerate(p['pattern_lines']):
                plines[i, :len(line)] = line
            pattern.append(plines)
        parts.append(np.array(pattern).flatten())
        # walls
        walls = np.stack([p['wall'] for p in obs['players']])
        parts.append(walls.flatten())
        # floor_lines
        floors = np.stack([p['floor_line'] for p in obs['players']])
        parts.append(floors.flatten())
        # scores
        scores = np.array([p['score'] for p in obs['players']], dtype=int)
        parts.append(scores)
        # current player
        parts.append(np.array([obs['current_player']], dtype=int))
        # concatenate and return
        return np.concatenate(parts)

    def encode_action(self, action: tuple) -> int:
        """
        Codifica una acción (source_idx, color, dest) como un entero único.
        """
        source_idx, color, dest = action
        return source_idx * 30 + color * 5 + dest
    
from app.core.ai_base import register_ai

register_ai("azul_deep_mcts", AIAzulDeepMCTS("modelos/checkpoint_best.pth"))