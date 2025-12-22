#!/usr/bin/env bash
# sync_azul_zero.sh
# This script copies the player implementation files from the azul_zero repository
# into the BGA backend core directory. It should be run whenever the source
# code in azul_zero/src/players is updated.

# Paths (adjust if your workspace layout changes)
SRC_DIR="/Users/alberto/src/azul_zero"
DEST_DIR="/Users/alberto/src/bga/backend/app/core/azul/zero"

# Ensure source exists
if [ ! -d "$SRC_DIR" ]; then
  echo "Source directory $SRC_DIR does not exist. Exiting."
  exit 1
fi

# Create destination if it does not exist
mkdir -p "$DEST_DIR"

# Use rsync to copy files, preserving permissions and overwriting changed files
rsync -av --delete --exclude "deep_mcts_player.py" "$SRC_DIR/src/players/" "$DEST_DIR/"
rsync -av --delete "$SRC_DIR/src/net/" "$DEST_DIR/net/"
rsync -av --delete "$SRC_DIR/src/mcts/" "$DEST_DIR/mcts/"
rsync -av --delete "$SRC_DIR/src/azul/" "$DEST_DIR/azul/"
# Sync models so the backend doesn't crash
mkdir -p "$DEST_DIR/models"
rsync -av "$SRC_DIR/data/checkpoints_v5/best.pt" "$DEST_DIR/models/best.pt"

echo "Sync completed successfully."
