#!/usr/bin/env bash
# sync_azul_zero.sh
# This script copies the player implementation files from the azul_zero repository
# into the BGA backend core directory. It should be run whenever the source
# code in azul_zero/src/players is updated.

# Paths (adjust if your workspace layout changes)
SRC_DIR="/Users/alberto/src/azul_zero/src/players"
DEST_DIR="/Users/alberto/src/bga/backend/app/core/azul/zero"

# Ensure source exists
if [ ! -d "$SRC_DIR" ]; then
  echo "Source directory $SRC_DIR does not exist. Exiting."
  exit 1
fi

# Create destination if it does not exist
mkdir -p "$DEST_DIR"

# Use rsync to copy files, preserving permissions and overwriting changed files
rsync -av --delete "$SRC_DIR/" "$DEST_DIR/"

echo "Sync completed successfully."
