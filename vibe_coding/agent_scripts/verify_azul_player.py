
import sys
import os
import torch
import numpy as np

# Add project root to path
sys.path.append(os.path.abspath("."))
# Add deep_mcts_player location for its local imports (net, mcts, azul)
sys.path.append(os.path.abspath("backend/app/core/azul/zero"))

from backend.app.core.azul.zero.deep_mcts_player import DeepMCTSPlayer
from backend.app.core.azul.zero.azul.env import AzulEnv

def test_deep_mcts_player():
    print("Testing DeepMCTSPlayer...")
    
    # Path to the synced model
    model_path = "backend/app/core/azul/zero/models/best.pt"
    if not os.path.exists(model_path):
        print(f"Error: Model not found at {model_path}")
        return

    try:
        player = DeepMCTSPlayer(model_path, mcts_iters=10)
        print("Model loaded successfully.")
    except Exception as e:
        print(f"Failed to load DeepMCTSPlayer: {e}")
        return

    # Create dummy observation
    env = AzulEnv()
    obs = env.reset(initial=True)
    obs_dict = env._get_obs() # Helper to get dict directly if needed, but reset returns dict in gym usually? 
    # Wait, AzulEnv.reset returns dict.
    
    print("Running predict()...")
    try:
        action = player.predict(obs)
        print(f"Prediction successful. Action: {action}")
    except Exception as e:
        print(f"Predict failed: {e}")
        import traceback
        traceback.print_exc()
        return

    print("Running visualize()...")
    try:
        viz = player.visualize(obs)
        print("Keys in viz:", viz.keys())
        
        # Check Saliency Structure
        saliency = viz['saliency']
        print("Saliency keys:", saliency.keys())
        
        # Check breakdown
        breakdown = saliency.get('spatial_breakdown', [])
        print(f"Spatial breakdown has {len(breakdown)} maps.")
        if len(breakdown) != 4:
            print("ERROR: Expected 4 spatial maps in breakdown.")
        
        # Check global labels
        global_labels = saliency.get('global_labels', [])
        print(f"Global labels count: {len(global_labels)}")
        
        # Check global values matches labels
        global_vals = saliency.get('global', [])
        print(f"Global values count: {len(global_vals)}")
        
        if len(global_labels) != len(global_vals):
             print(f"ERROR: Mismatch between global labels ({len(global_labels)}) and values ({len(global_vals)}).")

        print("Visualization check passed.")

    except Exception as e:
        print(f"Visualize failed: {e}")
        import traceback
        traceback.print_exc()
        return

    print("All tests passed.")

if __name__ == "__main__":
    test_deep_mcts_player()
