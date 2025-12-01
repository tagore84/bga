import sys
import os
# Add current dir to path
sys.path.append(os.getcwd())

from azul.env import AzulEnv
from net.azul_net import AzulNet

print("Verifying AzulEnv...")
env = AzulEnv()
obs = env.reset()
obs_flat = env.encode_observation(obs)
print(f"Global size: {obs_flat.shape[0]}")
if obs_flat.shape[0] == 164:
    print("✅ AzulEnv is updated (Size 164)")
else:
    print(f"❌ AzulEnv mismatch. Expected 164, got {obs_flat.shape[0]}")
    exit(1)

print("\nVerifying AzulNet...")
import inspect
sig = inspect.signature(AzulNet.forward)
if 'action_mask' in sig.parameters:
    print("✅ AzulNet accepts action_mask")
else:
    print(f"❌ AzulNet.forward does NOT accept action_mask")
    exit(1)

print("\n✅ BGA Core Files Verified!")
