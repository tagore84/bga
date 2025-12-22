# File: src/players/deep_mcts_player.py

import torch
import numpy as np

from net.azul_net import AzulNet

from azul.env import AzulEnv
from mcts.mcts import MCTS

from .base_player import BasePlayer

class DeepMCTSPlayer(BasePlayer):
    def __init__(self, model_path, device='cpu', mcts_iters=200, cpuct=1.0, temperature=1.0):
        super().__init__()
        self.device = torch.device(device)
        self.temperature = temperature
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
        # Select and return an action tuple
        action = self.mcts.select_action(temperature=self.temperature)
        return action

    def visualize(self, obs: dict):
        """
        Returns visualization data for the neural network.
        Compatible with NeuralVision.vue.
        """
        self._obs_to_env(obs)
        env = self.prototype_env
        
        # Get flattened observation
        obs_flat = env.encode_observation(env._get_obs())
        
        # Extract components
        spatial_size = env.num_players * 2 * 5 * 5
        factories_size = (env.N + 1) * 5
        
        # 1. Spatial Breakdown
        # Shape: (num_players * 2, 5, 5) flattened
        spatial_flat = obs_flat[:spatial_size]
        spatial_map = spatial_flat.reshape(env.num_players * 2, 5, 5).tolist()
        
        spatial_breakdown = []
        labels = ["Agent", "Rival"]
        for p in range(env.num_players):
            # Use specific label if available, else generic
            p_label = labels[p] if p < len(labels) else f"Player {p}"
            spatial_breakdown.append({
                "label": f"{p_label} Pattern",
                "map": spatial_map[p * 2]
            })
            spatial_breakdown.append({
                "label": f"{p_label} Wall",
                "map": spatial_map[p * 2 + 1]
            })
            
        # 2. Factories
        factories_flat = obs_flat[spatial_size : spatial_size + factories_size]
        factories_map = factories_flat.reshape(env.N + 1, 5).tolist()
        
        # 3. Global
        global_flat = obs_flat[spatial_size + factories_size:].tolist()
        
        # 4. Network Predictions
        valid_actions = env.get_valid_actions()
        action_mask = np.zeros(env.action_size, dtype=np.float32)
        for act in valid_actions:
            idx = env.action_to_index(act)
            action_mask[idx] = 1.0
            
        # Run inference
        pi_logits, values = self.net.predict(np.array([obs_flat]), np.array([action_mask]))
        value_pred = float(values[0])
        logits = pi_logits[0]
        
        # Helper for formatting
        def format_action(action_tuple):
            if action_tuple is None:
                return "None"
            source_idx, color_idx, dest_idx = action_tuple
            
            # Colors: Blue, Yellow, Orange, Black, Red
            color_names = ["Blue", "Yellow", "Orange", "Black", "Red"]
            c_name = color_names[color_idx] if 0 <= color_idx < len(color_names) else str(color_idx)
            
            if source_idx < env.N:
                s_name = f"Factory {source_idx}"
            else:
                s_name = "Center"
                
            if dest_idx < 5:
                # 0-based dest corresponds to Row 1-5
                d_name = f"Row {dest_idx + 1}"
            else:
                d_name = "Floor"
                
            return f"{s_name}, {c_name} -> {d_name}"

        # Find best masked action
        masked_logits = logits.copy()
        masked_logits[action_mask == 0] = -1e9
        best_masked_idx = int(np.argmax(masked_logits))
        best_masked_action = env.index_to_action(best_masked_idx)
        
        # Find best raw action (pure instinct)
        best_raw_idx = int(np.argmax(logits))
        best_raw_action = env.index_to_action(best_raw_idx)
        
        
        # Generate Global Labels
        # Structure from AzulEnv.encode_observation:
        # 1. Bag (5)
        # 2. Discard (5)
        # 3. First Player Token (1) - "Is in center?"
        # 4. Floor Lines (num_players * 7)
        # 5. Scores (num_players)
        # 6. Bonuses (num_players * 3: Rows, Cols, Sets)
        # 7. Remaining Tiles (5)
        
        global_labels = []
        colors = ["Blue", "Yellow", "Orange", "Black", "Red"]
        
        # 1. Bag
        global_labels.extend([f"Bag {c}" for c in colors])
        # 2. Discard
        global_labels.extend([f"Discard {c}" for c in colors])
        # 3. First Player Token
        global_labels.append("Center Token")
        
        labels = ["Agent", "Rival"]
        
        # 4. Floor Lines
        for p in range(env.num_players):
            p_label = labels[p] if p < len(labels) else f"P{p}"
            for i in range(env.L_floor): # 7
                global_labels.append(f"{p_label} Floor {i+1}")
                
        # 5. Scores
        for p in range(env.num_players):
             p_label = labels[p] if p < len(labels) else f"P{p}"
             global_labels.append(f"{p_label} Score")
             
        # 6. Bonuses
        for p in range(env.num_players):
             p_label = labels[p] if p < len(labels) else f"P{p}"
             global_labels.extend([f"{p_label} Rows", f"{p_label} Cols", f"{p_label} Sets"])
             
        # 7. Remaining Tiles
        global_labels.extend([f"Rem. {c}" for c in colors])

        return {
            "network_choice": {
                "value_pred": value_pred,
                "masked": {
                    "action_idx": best_masked_idx,
                    "action_desc": format_action(best_masked_action)
                },
                "raw": {
                    "action_idx": best_raw_idx,
                    "action_desc": format_action(best_raw_action)
                }
            },
            "saliency": {
                "spatial_breakdown": spatial_breakdown,
                "factories": factories_map,
                "global": global_flat,
                "global_labels": global_labels
            }
        }