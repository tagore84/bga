# File: src/players/deep_mcts_player.py

import torch
import numpy as np

from net.azul_net import AzulNet

from azul.env import AzulEnv
from mcts.mcts import MCTS

from .base_player import BasePlayer

class DeepMCTSPlayer(BasePlayer):
    def __init__(self, model_path, device='cpu', mcts_iters=250, cpuct=1.0, single_player_mode=True):
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
                         cpuct=cpuct,
                         single_player_mode=True)

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
        # CRITICAL: We must reset the MCTS root to the new state because we are not using 'advance'
        # to track history. The BGA adapter gives us a fresh observation each time.
        # So we treat each move as a fresh search problem.
        self.mcts.root = self.mcts.Node(self.prototype_env.clone(), parent=None, prior=1.0)
        
        self.mcts.run(self.prototype_env)
        # Select and return an action tuple
        # Use temperature=0.0 for greedy selection (Validation Mode)
        action = self.mcts.select_action(temperature=0.0)
        return action

    def visualize(self, obs: dict):
        """
        Returns visualization data for the current state.
        Structure matches NeuralVision.vue expectations.
        """
        # Load state
        self._obs_to_env(obs)
        env = self.prototype_env
        
        # Encode observation
        obs_flat = env.encode_observation(env._get_obs())
        obs_batch = obs_flat[np.newaxis, :]
        
        # 1. Network Prediction (Raw)
        pi_logits_raw, values = self.net.predict(obs_batch, action_mask=None)
        raw_idx = int(np.argmax(pi_logits_raw[0]))
        value_pred = float(values[0])
        
        # 2. Network Prediction (Masked / Legal)
        valid_actions = env.get_valid_actions()
        action_mask = np.zeros(env.action_size, dtype=np.float32)
        for action in valid_actions:
            idx = env.action_to_index(action)
            action_mask[idx] = 1.0
        
        mask_batch = action_mask[np.newaxis, :]
        pi_logits_masked, _ = self.net.predict(obs_batch, action_mask=mask_batch)
        masked_idx = int(np.argmax(pi_logits_masked[0]))
        
        # Helper stringifier
        colors = ["Blue", "Yellow", "Orange", "Black", "Red"]
        def fmt_act(idx):
            src, col, dst = env.index_to_action(idx)
            src_str = f"Fac {src}" if src < env.N else "Center"
            
            # Calculate Count
            count = 0
            if src < env.N:
                count = env.factories[src, col]
            else:
                count = env.center[col]
            
            dst_str = f"Row {dst+1}" if dst < 5 else "Floor"
            return f"{src_str} ({colors[col]} x{count}) -> {dst_str}"

        # 3. Saliency
        # Spatial: Separate channels
        # Order in encode_observation: [P0_Pattern, P1_Pattern, P0_Wall, P1_Wall] (for 2 players)
        spatial_size = self.net.in_channels * 5 * 5
        spatial_flat = obs_flat[:spatial_size]
        spatial_reshaped = spatial_flat.reshape(self.net.in_channels, 5, 5)
        
        spatial_breakdown = []
        labels = ["Red (Network) Pattern", "Rival Pattern", "Red (Network) Wall", "Rival Wall"]
        
        # Ensure we don't crash if different channels
        for c in range(min(len(labels), self.net.in_channels)):
            heatmap = spatial_reshaped[c]
            # Normalize per map if max > 0
            if heatmap.max() > 0:
                heatmap = heatmap / heatmap.max()
            spatial_breakdown.append({
                "label": labels[c],
                "map": heatmap.tolist()
            })
            
        # Factories: Input counts
        fact_size = (env.N + 1) * 5
        fact_flat = obs_flat[spatial_size : spatial_size + fact_size]
        fact_viz = fact_flat.reshape(env.N + 1, 5).tolist()
        
        # Global
        glob_flat = obs_flat[spatial_size + fact_size:]
        glob_viz = glob_flat.tolist()
        
        return {
            "network_choice": {
                "value_pred": value_pred,
                "masked": { "action_idx": masked_idx, "action_desc": fmt_act(masked_idx) },
                "raw": { "action_idx": raw_idx, "action_desc": fmt_act(raw_idx) }
            },
            "saliency": {
                # Legacy keys kept for safety, but we use breakdown now
                "spatial": spatial_reshaped[0].tolist(), 
                "spatial_breakdown": spatial_breakdown,
                "factories": fact_viz,
                "global": glob_viz,
                "global_labels": ["Bag", "Discard", "FirstPlayer"] + [f"Red Floor", "Rival Floor"] + [f"Red Score", "Rival Score"]
            }
        }