#!/usr/bin/env bash
# sync_azul_zero_specific.sh
# Copies selected files from azul_zero repo to the BGA backend
# and fixes imports to use absolute package paths.

set -e

# Define source base directory
SRC_BASE="/Users/alberto/src/azul_zero"

# Define destination base directory
DEST_BASE="/Users/alberto/src/bga/backend/app/core/azul/zero"

# Helper to copy a file and ensure destination directory exists
copy_file() {
  local src="$1"
  local dest="$2"
  local dest_dir=$(dirname "$dest")
  mkdir -p "$dest_dir"
  cp -f "$src" "$dest"
  echo "Copied $src -> $dest"
}

# Mapping list (source relative to SRC_BASE, destination relative to DEST_BASE)
declare -a mappings=(
  "src/azul/env.py|azul/env.py"
  "src/azul/rules.py|azul/rules.py"
  "src/azul/utils.py|azul/utils.py"
  "src/mcts/mcts.py|mcts/mcts.py"
  "data/checkpoints_v5/best.pt|models/best.pt"
  "src/net/azul_net.py|net/azul_net.py"
  "src/players/deep_mcts_player.py|players/deep_mcts_player.py"
  "src/players/heuristic_player.py|players/heuristic_player.py"
  "src/players/random_plus_player.py|players/random_plus_player.py"
)

for entry in "${mappings[@]}"; do
  IFS='|' read -r rel_src rel_dest <<< "$entry"
  src_path="$SRC_BASE/$rel_src"
  dest_path="$DEST_BASE/$rel_dest"
  if [[ -f "$src_path" ]]; then
    copy_file "$src_path" "$dest_path"
  else
    echo "Warning: source file $src_path does not exist"
  fi
done

echo "Files copied. Fixing imports..."

# Fix imports in copied Python files to use absolute package paths
# deep_mcts_player.py
sed -i '' \
  -e 's/^from net\.azul_net import/from app.core.azul.zero.net.azul_net import/' \
  -e 's/^from azul\.env import/from app.core.azul.zero.azul.env import/' \
  -e 's/^from mcts\.mcts import/from app.core.azul.zero.mcts.mcts import/' \
  "$DEST_BASE/players/deep_mcts_player.py"

# mcts/mcts.py
sed -i '' \
  -e 's/^from azul\.env import/from app.core.azul.zero.azul.env import/' \
  "$DEST_BASE/mcts/mcts.py"

# net/azul_net.py
sed -i '' \
  -e 's/^from azul\.env import/from app.core.azul.zero.azul.env import/' \
  -e 's/^from mcts\.mcts import/from app.core.azul.zero.mcts.mcts import/' \
  "$DEST_BASE/net/azul_net.py"

# azul/env.py
sed -i '' \
  -e 's/^from azul\.utils import/from app.core.azul.zero.azul.utils import/' \
  "$DEST_BASE/azul/env.py"

# random_plus_player.py
sed -i '' \
  -e 's/^from azul\.env import/from app.core.azul.zero.azul.env import/' \
  -e 's/^from azul\.rules import/from app.core.azul.zero.azul.rules import/' \
  "$DEST_BASE/players/random_plus_player.py"

echo "Sync completed successfully."
