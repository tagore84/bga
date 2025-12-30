
import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

try:
    print("Attempting to import app.core.seed...")
    from app.core.seed import AI_PLAYER_CONFIG
    print("Import successful.")
except Exception as e:
    print(f"FAILED to import app.core.seed: {e}")
    sys.exit(1)

def check_azul_config():
    print("Checking Azul Config...")
    if "azul" not in AI_PLAYER_CONFIG:
        print("ERROR: 'azul' key missing from AI_PLAYER_CONFIG")
        return

    azul_ais = AI_PLAYER_CONFIG["azul"]
    print(f"Found {len(azul_ais)} Azul AI configurations.")
    
    for i, ai in enumerate(azul_ais):
        print(f"[{i}] Name: {ai['name']}")
        print(f"    Strategy Object: {ai.get('strategy')}")
        if ai.get('strategy') is None:
            print("    ERROR: Strategy is None!")
        else:
            print("    Strategy instantiated successfully.")

if __name__ == "__main__":
    check_azul_config()
