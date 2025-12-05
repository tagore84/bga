# File: src/players/deep_mcts_player.py

import torch
import numpy as np

from ..net.azul_net import AzulNet

from ..azul.env import AzulEnv
from ..mcts.mcts import MCTS

from .base_player import BasePlayer

class DeepMCTSPlayer(BasePlayer):
    def __init__(self, model_path, device='cpu', mcts_iters=200, cpuct=1.0):
        super().__init__()
        self.device = torch.device(device)
        # Load checkpoint and extract model state
        checkpoint = torch.load(model_path, map_location=self.device)
        state_dict = checkpoint.get('model_state', checkpoint)
        
        # Infer network dimensions from checkpoint
        in_channels = state_dict['conv_in.weight'].shape[1]
        
        # For Phase 2 architecture:
        # policy_fc1.weight has shape [256, spatial_flat + factories_flat + global_size]
        # value_fc1.weight has shape [256, spatial_flat + factories_flat + global_size]
        # spatial_flat = 2 * 5 * 5 = 50 (policy conv outputs 2 channels)
        # spatial_flat = 1 * 5 * 5 = 25 (value conv outputs 1 channel)
        # factories_flat = (N + 1) * embed_dim, where N=5, we need to infer embed_dim
        
        # For now, use a simpler approach: initialize env to get correct sizes
        env = AzulEnv()
        obs_flat = env.encode_observation(env.reset(initial=True))
        total_obs_size = obs_flat.shape[0]
        spatial_size = env.num_players * 2 * 5 * 5
        factories_size = (env.N + 1) * 5
        global_size = total_obs_size - spatial_size - factories_size
        action_size = env.action_size
        
        # Build and load network
        self.net = AzulNet(
            in_channels=in_channels,
            global_size=global_size,
            action_size=action_size,
            factories_count=env.N
        )
        self.net.load_state_dict(state_dict)
        self.net.to(self.device)
        self.net.eval()
        
        # Prepare prototype environment for MCTS
        self.prototype_env = env
        # Initialize MCTS searcher
        self.mcts = MCTS(self.prototype_env,
                         self.net,
                         simulations=mcts_iters,
                         cpuct=cpuct)

    def _obs_to_env(self, obs: dict):
        """
        Copy the observation dict into the prototype_env state.
        """
        env = self.prototype_env
        env.bag = obs['bag'].copy()
        env.discard = obs['discard'].copy()
        env.factories = obs['factories'].copy()
        env.center = obs['center'].copy()
        env.first_player_token = bool(obs['first_player_token'])
        env.current_player = int(obs['current_player'])
        env.round_count = int(obs.get('round_count', env.round_count))
        for i, p_obs in enumerate(obs['players']):
            env.players[i]['pattern_lines'] = [line.copy() for line in p_obs['pattern_lines']]
            env.players[i]['wall'] = p_obs['wall'].copy()
            env.players[i]['floor_line'] = p_obs['floor_line'].copy()
            env.players[i]['score'] = int(p_obs['score'])

    def predict(self, obs: dict):
        """
        Ejecuta MCTS en el estado dado y devuelve la acción seleccionada.
        """
        # Load current observation into the prototype environment
        self._obs_to_env(obs)
        # Run MCTS from this state
        self.mcts.run(self.prototype_env)
        
        # --- LOGGING STATISTICS ---
        # Get statistics from the root node
        root = self.mcts.root
        children = root.children
        
        # Sort actions by visit count (descending)
        sorted_items = sorted(children.items(), key=lambda item: item[1].visits, reverse=True)
        
        print(f"\n[DeepMCTSPlayer] Decision Analysis (Sims: {self.mcts.simulations})")
        print(f"{'Action':<30} | {'Visits':<8} | {'Q-Val':<8} | {'Prior':<8} | {'Score':<8}")
        print("-" * 75)
        
        for i, (action, node) in enumerate(sorted_items[:5]): # Show top 5
            # Action is (source_idx, color, dest)
            # Create a more readable string
            source, color, dest = action
            src_str = f"Fact_{source}" if source < 5 else "Center"
            dest_str = f"Line_{dest+1}" if dest < 5 else "Floor"
            action_str = f"{src_str}, Color_{color}, to {dest_str}"
            
            # UCB Score (approximate since we don't pass cpuct here exactly as in select, but close enough for display)
            # Usually we want the value used for selection. 
            # Note: MCTS.select uses ucb_score method.
            ucb = node.ucb_score(self.mcts.cpuct)
            
            print(f"{action_str:<30} | {node.visits:<8} | {node.value:.4f}   | {node.prior:.4f}   | {ucb:.4f}")
            
        print("-" * 75)
        # --------------------------

        # Select and return an action tuple
        action = self.mcts.select_action()
        return action