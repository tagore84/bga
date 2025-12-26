from app.core.ai_base import AIBase
from app.core.azul.zero.random_plus_player import RandomPlusPlayer
from app.core.azul.adapter import bga_state_to_azul_zero_obs
from app.models.azul.azul import AzulMove, Color

class RandomPlusAdapter(AIBase):
    def __init__(self):
        self.player = RandomPlusPlayer()

    def select_move(self, state) -> AzulMove:
        # Convert BGA state to Obs
        obs, _ = bga_state_to_azul_zero_obs(state)
        
        # Predict: returns (source, color, dest)
        action = self.player.predict(obs) 
        
        if action is None:
             raise RuntimeError(f"RandomPlusPlayer returned None action")

        return self._action_to_move(action, state)

    def _action_to_move(self, action: tuple, state) -> AzulMove:
        source_idx, color, dest = action
        # Check factory count from state (assuming it has expositores)
        # state might be AzulGameState object
        num_factories = len(state.expositores)
        
        if source_idx < num_factories:
            factory_val = str(source_idx)
        else:
            factory_val = "centro"
            
        if dest == 5:
            row_val = 0
        else:
            row_val = dest + 1
            
        return AzulMove(factory=factory_val, color=Color(color), row=row_val)
