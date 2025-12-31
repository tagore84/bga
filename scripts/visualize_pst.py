
import sys
import os
import matplotlib.pyplot as plt
import numpy as np
import chess

# Add backend to path to allow imports
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_path = os.path.join(current_dir, '..', 'backend')
sys.path.append(backend_path)

from app.core.chess.pst import TABLES

def visualize_pst():
    pieces = [
        (chess.PAWN, "Pawn"),
        (chess.KNIGHT, "Knight"),
        (chess.BISHOP, "Bishop"),
        (chess.ROOK, "Rook"),
        (chess.QUEEN, "Queen"),
        (chess.KING, "King")
    ]

    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    axes = axes.flatten()

    for idx, (piece_type, name) in enumerate(pieces):
        ax = axes[idx]
        pst_values = TABLES[piece_type]
        
        # PST is a flat list of 64 integers: a1..h1, a2..h2, ..., a8..h8
        # We reshape it to 8x8.
        # numpy reshape fills row by row.
        # So row 0 becomes a1..h1, which is Rank 1.
        grid = np.array(pst_values).reshape((8, 8))
        
        # We want to display Rank 8 at the top, Rank 1 at the bottom.
        # using origin='lower' puts index 0 at the bottom.
        im = ax.imshow(grid, cmap='RdYlGn', origin='lower')
        
        ax.set_title(f"White {name} PST")
        ax.set_xticks(range(8))
        ax.set_yticks(range(8))
        ax.set_xticklabels(['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'])
        ax.set_yticklabels(['1', '2', '3', '4', '5', '6', '7', '8'])
        
        # Loop over data dimensions and create text annotations.
        for i in range(8): # Rank (y)
            for j in range(8): # File (x)
                text = ax.text(j, i, grid[i, j],
                               ha="center", va="center", color="black", fontsize=8)

        fig.colorbar(im, ax=ax)

    plt.tight_layout()
    output_path = os.path.join(current_dir, '..', 'pst_heatmaps.png')
    plt.savefig(output_path)
    print(f"Visualization saved to {output_path}")

if __name__ == "__main__":
    visualize_pst()
