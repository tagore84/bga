
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

try:
    print("Importing AIAzulDeepMCTS...")
    from app.core.azul.deep_mcts_player_adapter import AIAzulDeepMCTS
    print("Import successful.")
    
    # We won't instantiate it because we might not have the model and don't want to load it if slow.
    # But let's check if the module import is safe.
    
except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()
