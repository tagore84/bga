# backend/app/core/azul/zero/players/heuristic_player.py
import random
import torch
import numpy as np

class HeuristicPlayer:
    def __init__(self, name="Heuristic"):
        self.device = torch.device("cpu")
        self.name = name

    def predict(self, obs):
        current_player = obs["current_player"]
        # Ensure we handle the padded lines correctly
        if "pattern_lines_padded" in obs["players"][current_player]:
             pattern_lines = np.array(obs["players"][current_player]["pattern_lines_padded"])
        else:
             # Fallback if padding not present (though adapter provides it)
             # This might fail if shapes are irregular without padding
             pattern_lines = obs["players"][current_player]["pattern_lines"]

        wall = np.array(obs["players"][current_player]["wall"])
        valid_actions = get_valid_actions_from_obs(obs)

        best_score = float("-inf")
        best_action = None
        
        # If valid_actions is empty, handle it
        if len(valid_actions) == 0:
             return None

        for action in valid_actions:
            flat_action = action.item()
            factory, color, row = decode_action(flat_action)

            score = 0

            if row < 5:
                pline = pattern_lines[row]
                if color in wall[row]:
                    continue  # ilegal, pero por si acaso
                filled = (pline != -1).sum()
                total = len(pline)
                if color in pline or np.all(pline == -1):
                    score += 10  # colocar color compatible o en vacío
                    score += 5 * filled  # más llena la línea = mejor
                    if filled == total - 1:
                        score += 20  # ¡completa!
            else:
                score -= 15  # penaliza ir al suelo

            # pequeñas bonificaciones por usar fábricas y no centro
            if factory < 5:
                score += 1

            if score > best_score:
                best_score = score
                best_action = flat_action

        if best_action is not None:
            # Return tuple (source, color, dest) as expected by ai_zero adapter
            return decode_action(best_action)
        else:
            # Fallback random
            if len(valid_actions) > 0:
                 return decode_action(valid_actions[0].item())
            return None

def decode_action(index):
    """
    Decode an action index into (factory/source index, color, destination row).
    Actions are encoded as: index = source_idx * (C * 6) + color * 6 + dest.
    C is number of colors (5), dest count is 6 (pattern lines 0–4 and floor as 5).
    """
    C = 5  # number of colors
    D = 6  # number of possible destinations (5 pattern rows + floor)
    factory = index // (C * D)
    remainder = index % (C * D)
    color = remainder // D
    row = remainder % D
    return factory, color, row

def get_valid_actions_from_obs(obs):
    C = 5  # number of colors
    N = len(obs["factories"])  # number of factories
    valid_actions = []
    current_player = obs["current_player"]
    wall = obs["players"][current_player]["wall"]
    
    # Need to check pattern lines for validity too (color match, fullness)
    # The original code didn't fully check pattern line validity in the loop, 
    # relying on the environment or assuming 'valid_actions' was passed in?
    # Wait, the original code had `get_valid_actions_from_obs` which implements logic.
    # Let's verify that logic.
    
    pattern_lines = obs["players"][current_player]["pattern_lines"] # List of arrays/lists

    for source_idx in range(N + 1):
        source = obs["factories"][source_idx] if source_idx < N else obs["center"]
        for color in range(C):
            if source[color] == 0:
                continue
            for dest in range(6):
                if dest < 5:
                    # Check wall
                    wall_row = wall[dest]
                    if color in wall_row:
                        continue
                    # Check pattern line
                    pline = pattern_lines[dest]
                    # pline is array or list. -1 is empty.
                    # Check if full
                    if np.sum(pline != -1) >= len(pline):
                        continue
                    # Check color match if not empty
                    first_val = -1
                    for v in pline:
                        if v != -1:
                            first_val = v
                            break
                    if first_val != -1 and first_val != color:
                        continue
                        
                index = source_idx * (C * 6) + color * 6 + dest
                valid_actions.append(index)
    return torch.tensor(valid_actions)
