
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

try:
    print("Importing HeuristicMinMaxMctsAdapter...")
    from app.core.azul.heuristic_min_max_mcts_adapter import HeuristicMinMaxMctsAdapter
    print("Import successful.")

    print("Instantiating adapter...")
    adapter = HeuristicMinMaxMctsAdapter(strategy='minmax', depth=1)
    print("Instantiation successful.")

except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()
