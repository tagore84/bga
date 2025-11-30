import numpy as np
from app.models.azul.azul import AzulGameState, Color

def bga_state_to_azul_zero_obs(state: AzulGameState) -> dict:
    """
    Convierte el estado de BGA (AzulGameState) al formato de observación de azul_zero.
    """
    
    # 1. Factories
    num_factories = len(state.expositores)
    factories = np.zeros((num_factories, 5), dtype=int)
    for i, expositor in enumerate(state.expositores):
        for color in expositor:
            if isinstance(color, int):
                c_idx = color
            else:
                c_idx = int(color)
            factories[i, c_idx] += 1
            
    # 2. Center
    center = np.zeros(5, dtype=int)
    for color in state.centro:
        if isinstance(color, int):
            c_idx = color
        else:
            c_idx = int(color)
        center[c_idx] += 1
        
    # 3. Players
    player_ids = list(state.jugadores.keys())
    
    players_obs = []
    for pid in player_ids:
        p_bga = state.jugadores[pid]
        
        # Pattern lines
        pattern_lines = []
        for i in range(5):
            capacity = i + 1
            line = np.full(capacity, -1, dtype=int)
            bga_line = p_bga.patrones[i]
            for k, color in enumerate(bga_line):
                line[k] = int(color)
            pattern_lines.append(line)
            
        # Wall
        wall = np.full((5, 5), -1, dtype=int)
        for r in range(5):
            for c in range(5):
                val = p_bga.pared[r][c]
                if val is not None:
                    wall[r, c] = int(val)
                    
        # Floor line
        floor_line = np.full(7, -1, dtype=int)
        for k, color in enumerate(p_bga.suelo):
            if k < 7:
                if isinstance(color, int) or isinstance(color, Color):
                    floor_line[k] = int(color)
                
        players_obs.append({
            'pattern_lines': pattern_lines,
            'wall': wall,
            'floor_line': floor_line,
            'score': p_bga.puntos
        })
        
    # Current player index
    try:
        current_player_idx = player_ids.index(state.turno_actual)
    except ValueError:
        current_player_idx = 0 # Fallback
        
    # Bag and Discard
    bag = np.zeros(5, dtype=int)
    for c in state.bolsa:
        bag[int(c)] += 1
        
    discard = np.zeros(5, dtype=int)
    for c in state.caja:
        discard[int(c)] += 1
        
    obs = {
        'bag': bag,
        'discard': discard,
        'factories': factories,
        'center': center,
        'first_player_token': int(state.first_player_marker_in_center),
        'players': players_obs,
        'current_player': current_player_idx,
        'round_count': state.ronda
    }
    
    # Add 'pattern_lines_padded'
    for p in players_obs:
        padded = []
        for pl in p['pattern_lines']:
            pad_len = 5 - len(pl)
            if pad_len > 0:
                padded.append(np.pad(pl, (0, pad_len), constant_values=-1))
            else:
                padded.append(pl)
        p['pattern_lines_padded'] = padded
        
    return obs, player_ids
