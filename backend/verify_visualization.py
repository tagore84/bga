
import sys
import os
import torch
import numpy as np

# Adjust path to find app
sys.path.append("/Users/alberto/src/bga/backend")

from app.core.azul.zero.players.deep_mcts_player import DeepMCTSPlayer
from app.core.azul.zero.azul.env import AzulEnv

def test_visualize():
    # We need a model file.
    model_path = "/Users/alberto/src/bga/backend/app/core/azul/zero/models/best.pt"
    if not os.path.exists(model_path):
        print("Model not found, skipping DeepMCTSPlayer test")
        return

    try:
        player = DeepMCTSPlayer(model_path, device='cpu')
    except Exception as e:
        print(f"Failed to load player: {e}")
        return

    env = AzulEnv()
    obs = env.reset()
    
    print("Testing visualization...")
    try:
        data = player.visualize(obs)
        
        print("Visualization keys:", data.keys())
        print("Saliency keys:", data['saliency'].keys())
        print("Spatial saliency shape:", np.array(data['saliency']['spatial']).shape)
        print("Factories saliency shape:", np.array(data['saliency']['factories']).shape)
        
        assert 'saliency' in data
        assert 'network_choice' in data
        assert 'inputs' in data
        print("Verification SUCCESS")
        
    except Exception as e:
        print(f"Verification FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_visualize()
