
import sys
import os
import json

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.models.azul.azul import AzulGameState, JugadorAzul, AzulMove, Color, aplicar_movimiento

def validate_game_log(log_path):
    print(f"--- Validating Game Log: {log_path} ---")
    
    with open(log_path, 'r') as f:
        lines = f.readlines()

    errors_found = False
    
    for i, line in enumerate(lines):
        try:
            entry = json.loads(line)
            move_data = entry['move']
            state_data = entry['state_before']
            
            # Reconstruct State
            jugadores = {}
            for pid, pdata in state_data['jugadores'].items():
                jugadores[pid] = JugadorAzul(**pdata)
                
            game_state = AzulGameState(
                jugadores=jugadores,
                bolsa=state_data['bolsa'],
                caja=state_data['caja'],
                centro=state_data['centro'],
                expositores=state_data['expositores'],
                turno_actual=state_data['turno_actual'],
                jugador_inicial=state_data['jugador_inicial'],
                fase=state_data['fase'],
                ronda=state_data['ronda'],
                first_player_marker_in_center=state_data['first_player_marker_in_center']
            )

            # Reconstruct Move
            # Handle potential string/int types for factory/color/row
            factory = move_data['factory']
            color = move_data['color']
            row = move_data['row']
            
            # Ensure types match what AzulMove expects
            # factory is str in json but might be int index
            # color is int value of enum
            
            azul_move = AzulMove(
                factory=str(factory),
                color=Color(int(color)),
                row=int(row)
            )

            player_id = entry['player_id']
            
            # Additional Custom Validations before applying
            # 1. Validate Source has tiles
            if azul_move.factory == "centro":
                source_tiles = game_state.centro
            else:
                f_idx = int(azul_move.factory)
                source_tiles = game_state.expositores[f_idx]
            
            count_color = sum(1 for t in source_tiles if t == azul_move.color.value) # json tiles are ints
            
            if count_color == 0:
                print(f"[Line {i+1}] FATAL: Player {player_id} took 0 tiles of Color {azul_move.color} from {azul_move.factory}!")
                print(f"Source tiles: {source_tiles}")
                errors_found = True

            # Apply Move (will raise ValueError if invalid logic persists, though we just fixed it in code)
            # validation here duplicates the fix but acts as a check on historic data
            try:
                aplicar_movimiento(game_state, player_id, azul_move)
            except ValueError as e:
                print(f"[Line {i+1}] LOGIC ERROR: aplicar_movimiento raised error: {e}")
                errors_found = True
            except Exception as e:
                print(f"[Line {i+1}] EXCEPTION: {e}")
                errors_found = True

        except Exception as e:
            print(f"[Line {i+1}] PARSE ERROR: {e}")
            errors_found = True
            break

    if not errors_found:
        print("SUCCESS: No illegal moves found in the game log.")
    else:
        print("FAILURE: Illegal moves detected.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        log_file = sys.argv[1]
    else:
        log_file = "backend/logs/azul_games/game_151.jsonl"
    
    validate_game_log(log_file)
