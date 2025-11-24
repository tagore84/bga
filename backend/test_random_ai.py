import sys
import os
import random

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.azul.azul import AzulGameState, AzulGame, JugadorAzul, Fase, Color, AzulMove, get_legal_moves
from app.core.azul.game import init_game_state
from app.models.azul.azul import aplicar_movimiento
from app.core.azul.ai_azul_random import RandomAzulAI

def test_random_ai_simulation():
    print("Starting Random AI Simulation...")
    
    # Initialize game state
    players_data = [
        {"id": "1", "name": "AI_1", "type": "ai"},
        {"id": "2", "name": "AI_2", "type": "ai"}
    ]
    state = init_game_state(players_data)
    ai_player = RandomAzulAI()
    
    # Run for a few rounds or until game end
    max_rounds = 3
    current_round = 1
    
    while current_round <= max_rounds and not state.terminado:
        print(f"\n--- Round {state.ronda} (Phase: {state.fase}) ---")
        
        # Play out the "oferta" phase
        while state.fase == Fase.OFERTA:
            current_player = state.turno_actual
            print(f"Player {current_player}'s turn.")
            
            try:
                # AI selects move
                move = ai_player.select_move(state)
                print(f"AI selected move: {move}")
                
                # Apply move
                aplicar_movimiento(state, current_player, move)
                
                # Check if phase changed (round end)
                if state.fase != Fase.OFERTA:
                    print("Round ended (Oferta phase complete).")
                    break
                    
            except Exception as e:
                print(f"CRITICAL ERROR during move execution: {e}")
                import traceback
                traceback.print_exc()
                return

        # If round ended, check state
        if state.terminado:
            print("Game Over!")
            break
            
        current_round = state.ronda

    print("\nSimulation completed successfully!")
    print(f"Final State - Round: {state.ronda}, Phase: {state.fase}")
    for pid, p in state.jugadores.items():
        print(f"Player {pid} Score: {p.puntos}")

if __name__ == "__main__":
    test_random_ai_simulation()
