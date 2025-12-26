<template>
  <div class="chess-piece" :style="{ width: size, height: size }">
    <img :src="pieceImage" :alt="piece" class="piece-img" draggable="false" />
  </div>
</template>

<script>
// Load all SVG files from the assets directory
const svgImages = import.meta.glob('../../assets/chess/pieces-svg/*.svg', { eager: true, query: '?url', import: 'default' })

export default {
  name: "ChessPiece",
  props: {
    piece: {
      type: String, // 'P', 'R', ... for White; 'p', 'r', ... for Black
      required: true
    },
    size: {
      type: String,
      default: "100%"
    }
  },
  computed: {
    pieceImage() {
      if (!this.piece) return '';
      
      const isWhite = this.piece === this.piece.toUpperCase();
      const colorSuffix = isWhite ? 'w' : 'b';
      const p = this.piece.toLowerCase();
      
      const typeMap = {
        'p': 'pawn',
        'r': 'rook',
        'n': 'knight',
        'b': 'bishop',
        'q': 'queen',
        'k': 'king'
      };
      
      const type = typeMap[p] || 'pawn';
      const fileName = `${type}-${colorSuffix}.svg`;
      
      // key matches the glob pattern
      const key = `../../assets/chess/pieces-svg/${fileName}`;
      return svgImages[key] || '';
    }
  }
};
</script>

<style scoped>
.chess-piece {
  display: flex;
  justify-content: center;
  align-items: center;
  /* Disable pointer events on the container so clicks pass through to the square,
     UNLESS we want to support native drag-and-drop where the image is the drag handle.
     ChessGame.vue handles drag on the .piece-container wrapper, so we can keep this none or strict.
     However, standard html5 drag usually wants the img to be draggable=false to avoid ghost issues 
     if the parent is the draggable one. */
  pointer-events: none; 
}

.piece-img {
    width: 100%;
    height: 100%;
    /* Ensure the image doesn't capture drag events itself if the parent controls it */
    user-select: none;
    -webkit-user-drag: none;
    filter: drop-shadow(1px 2px 3px rgba(0,0,0,0.4));
}
</style>
