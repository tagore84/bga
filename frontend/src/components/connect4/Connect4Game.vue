<template>
  <div class="connect4-container">
    <div v-if="error" class="error">{{ error }}</div>
    <div v-else-if="!loaded" class="loading">Cargando partida...</div>
    <div v-else>
      <div class="status-bar">
        <div v-if="status !== 'in_progress'" class="result">
            <p v-if="status === 'draw'">¡Empate!</p>
            <p v-else>¡{{ status === 'Red_won' ? 'Rojo' : 'Azul' }} ha ganado!</p>
            <button @click="goBack" class="back-button">Volver</button>
        </div>
        <div v-else>
            Turno: <span :class="currentTurn.toLowerCase()">{{ currentTurn === 'Red' ? 'Rojo' : 'Azul' }}</span>
        </div>
      </div>

      <div class="board-wrapper">
        <!-- Render Pieces -->
        <!-- Render Pieces in a constrained container to account for board margins -->
        <div class="pieces-container">
            <template v-for="(cell, idx) in board" :key="idx">
                <div 
                    v-if="cell"
                    class="piece"
                    :class="{ 'last-move': idx === lastMoveIndex }"
                    :style="{
                        left: ((idx % 7) * (100/7)) + '%',
                        top: (Math.floor(idx / 7) * (100/6)) + '%'
                    }"
                >
                    <img :src="cell === 'Red' ? redPiece : bluePiece" alt="piece" />
                </div>
            </template>
        </div>

        <!-- Board Image (Overlay) -->
        <img :src="boardImg" class="board-overlay" alt="board" />

        <!-- Winning Line Overlay -->
        <svg v-if="winningLineCoords" class="winning-line-container">
            <line 
                :x1="winningLineCoords.x1" 
                :y1="winningLineCoords.y1" 
                :x2="winningLineCoords.x2" 
                :y2="winningLineCoords.y2" 
                stroke="yellow" 
                stroke-width="3" 
                stroke-linecap="round" 
                class="winning-line-anim"
            />
        </svg>

        <!-- Click Columns (Transparent Overlays) -->
        <div class="click-layer">
            <div 
                v-for="col in 7" 
                :key="col" 
                class="column-click-area"
                @click="onClick(col - 1)"
            ></div>
        </div>
      </div>

      <div class="controls">
        <button v-if="canUndo" class="btn-undo" @click="undoMove">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon-undo"><path d="M3 7v6h6"></path><path d="M21 17a9 9 0 0 0-9-9 9 9 0 0 0-6 2.3L3 13"></path></svg>
            Undo Move
        </button>
        <button class="btn-exit" @click="goBack">Salir</button>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { API_BASE, WS_BASE } from '../../config'
import boardImg from '@/assets/conecta_cuatro/board.png'
import redPiece from '@/assets/conecta_cuatro/red_piece.png'
import bluePiece from '@/assets/conecta_cuatro/blue_piece.png'

const route = useRoute()
const router = useRouter()
const gameId = parseInt(route.params.id)

const board = ref(Array(42).fill(null))
const currentTurn = ref('Red')
const status = ref('in_progress')
const loaded = ref(false)
const error = ref(null)
const player_red = ref(null)
const player_blue = ref(null)
const moves = ref([]) 

const isPlayerRed = ref(false)
const isPlayerBlue = ref(false)

const token = localStorage.getItem('token')
const meUsername = token ? JSON.parse(atob(token.split('.')[1])).sub : null

const canUndo = computed(() => {
    if (status.value !== 'in_progress') return false;
    // Check if player
    if (!isPlayerRed.value && !isPlayerBlue.value) return false;
    // Check if moves exist
    return moves.value && moves.value.length > 0;
});

const lastMoveIndex = computed(() => {
    if (!moves.value || moves.value.length === 0) return -1;
    const lastCol = moves.value[moves.value.length - 1];
    
    // Find the highest piece in this column
    for (let r = 0; r < 6; r++) {
        const idx = r * 7 + lastCol;
        if (board.value[idx]) return idx;
    }
    return -1;
});

const winningLine = ref(null); // { start: index, end: index }



function findWinningLine(board, player) {
    const piece = player; // "Red" or "Blue"
    const ROWS = 6;
    const COLS = 7;
    
    function getPiece(r, c) {
        if (r < 0 || r >= ROWS || c < 0 || c >= COLS) return null;
        return board[r * COLS + c];
    }
    
    // Check horizontal
    for (let r = 0; r < ROWS; r++) {
        for (let c = 0; c < COLS - 3; c++) {
            if ([0,1,2,3].every(i => getPiece(r, c+i) === piece)) {
                return { start: r * COLS + c, end: r * COLS + c + 3 };
            }
        }
    }
    // Check vertical
    for (let r = 0; r < ROWS - 3; r++) {
        for (let c = 0; c < COLS; c++) {
            if ([0,1,2,3].every(i => getPiece(r+i, c) === piece)) {
                return { start: r * COLS + c, end: (r+3) * COLS + c };
            }
        }
    }
    // Check diagonal positive (slope down-right in visual? No, coords: r0=top. increasing r = down. increasing c = right.)
    // Slope positive in array terms (r+, c+)
    for (let r = 0; r < ROWS - 3; r++) {
        for (let c = 0; c < COLS - 3; c++) {
            if ([0,1,2,3].every(i => getPiece(r+i, c+i) === piece)) {
                return { start: r * COLS + c, end: (r+3) * COLS + c + 3 };
            }
        }
    }
    // Check diagonal negative (r+, c-)
    for (let r = 0; r < ROWS - 3; r++) {
        for (let c = 3; c < COLS; c++) {
             if ([0,1,2,3].every(i => getPiece(r+i, c-i) === piece)) {
                return { start: r * COLS + c, end: (r+3) * COLS + c - 3 };
            }
        }
    }
    return null;
}

const winningLineCoords = computed(() => {
    if (!winningLine.value) return null;
    
    const getCenter = (idx) => {
        const r = Math.floor(idx / 7);
        const c = idx % 7;
        // Center x % = col * (100/7) + (100/14)
        // Center y % = row * (100/6) + (100/12)
        const x = (c * (100/7)) + (50/7);
        const y = (r * (100/6)) + (50/6);
        return { x, y };
    }
    
    const start = getCenter(winningLine.value.start);
    const end = getCenter(winningLine.value.end);
    return { x1: start.x + '%', y1: start.y + '%', x2: end.x + '%', y2: end.y + '%' };
});

async function fetchState() {
// ...
  const res = await fetch(`${API_BASE}/connect4/${gameId}`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const data = await res.json();
  
  board.value = data.board;
  currentTurn.value = data.current_turn;
  status.value = data.status;
  player_red.value = data.player_red_name;
  player_blue.value = data.player_blue_name;
  
  if (status.value === 'Red_won') {
      winningLine.value = findWinningLine(board.value, 'Red');
  } else if (status.value === 'Blue_won') {
      winningLine.value = findWinningLine(board.value, 'Blue');
  } else {
      winningLine.value = null;
  }
  
  if (data.config && data.config.moves) {
      moves.value = data.config.moves;
  } else {
      moves.value = [];
  }
  
  return data;
}

async function onClick(col) {
    if (status.value !== 'in_progress') return;
    
    // Check turn
    if (currentTurn.value === 'Red' && !isPlayerRed.value) return;
    if (currentTurn.value === 'Blue' && !isPlayerBlue.value) return;

    try {
        const res = await fetch(`${API_BASE}/connect4/${gameId}/move`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ column: col })
        });
        if (!res.ok) {
            const txt = await res.text();
            throw new Error(txt);
        }
    } catch (e) {
        // console.error(e);
    }
}

async function undoMove() {
    if (!confirm("Are you sure you want to undo the last move?")) return;
    try {
        const res = await fetch(`${API_BASE}/connect4/${gameId}/undo`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!res.ok) {
            const txt = await res.text();
            try {
                const err = JSON.parse(txt);
                alert(err.detail || txt);
            } catch(e) {
                alert(txt);
            }
        }
    } catch (e) {
        console.error("Undo failed", e);
    }
}

function goBack() {
    router.push('/games')
}

let socket;

onMounted(async () => {
    socket = new WebSocket(`${WS_BASE}/ws/connect4/${gameId}`);
    
    socket.onmessage = ({ data }) => {
        try {
            const msg = JSON.parse(data);
            
            if (msg.type === 'undo') {
                fetchState();
                return;
            }
            
            if (msg.board) board.value = JSON.parse(msg.board);
            if (msg.status) {
                status.value = msg.status;
                if (status.value === 'Red_won') {
                    winningLine.value = findWinningLine(board.value, 'Red');
                } else if (status.value === 'Blue_won') {
                    winningLine.value = findWinningLine(board.value, 'Blue');
                }
            }
            
            if (msg.by) {
                currentTurn.value = msg.by === 'Red' ? 'Blue' : 'Red';
            }
            
            if (msg.type === 'move' && msg.column) {
                moves.value.push(parseInt(msg.column));
            }
            
        } catch (e) {
            console.error("WS Error", e);
        }
    };

    try {
        await fetchState();
        isPlayerRed.value = (player_red.value === meUsername);
        isPlayerBlue.value = (player_blue.value === meUsername);
        loaded.value = true;
    } catch (e) {
        error.value = e.message;
    }
});

onBeforeUnmount(() => {
    socket && socket.close();
});
</script>

<style scoped>
.connect4-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    margin-top: 2rem;
    font-family: 'Arial', sans-serif;
    padding-bottom: 2rem;
}
.board-wrapper {
    position: relative;
    width: 100%;
    max-width: 780px;
    aspect-ratio: 780 / 490;
    margin-top: 20px;
    background-color: transparent; 
}
.board-overlay {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: 10;
    pointer-events: none;
}
.pieces-container {
    position: absolute;
    top: 2.45%;
    bottom: 3.06%; 
    left: 2.44%;
    right: 2.44%;
    z-index: 5;
}
.piece {
    position: absolute;
    width: 14.2857%; /* 100/7 */
    height: 16.6667%; /* 100/6 */
    display: flex;
    justify-content: center;
    align-items: center;
}
.piece img {
    height: 82%; 
    width: auto;
    aspect-ratio: 1/1;
    border-radius: 50%;
    box-shadow: inset 0 0 10px rgba(0,0,0,0.3);
}
.click-layer {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: 20;
    display: flex;
}
.column-click-area {
    width: 14.2857%; /* 100/7 */
    height: 100%;
    cursor: pointer;
}
.column-click-area:hover {
    background-color: rgba(255, 255, 255, 0.1);
}
.status-bar {
    font-size: 1.5rem;
    margin-bottom: 1rem;
    text-align: center;
}
.red { color: red; font-weight: bold; }
.blue { color: blue; font-weight: bold; }
.result { text-align: center; }

.back-button {
    margin-top: 10px;
    padding: 10px 20px;
    font-size: 1rem;
    cursor: pointer;
    background-color: #333;
    color: white;
    border: none;
    border-radius: 5px;
}

.controls {
    display: flex;
    gap: 1rem;
    margin-top: 2rem;
}

.btn-undo, .btn-exit {
    padding: 10px 20px;
    font-size: 1rem;
    cursor: pointer;
    border: none;
    border-radius: 5px;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    transition: background-color 0.2s;
    font-weight: bold;
}

.btn-undo {
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(8px);
    border: 1px solid rgba(255, 255, 255, 0.15);
    color: var(--text-primary);
    padding: 0.6rem 1.2rem;
    border-radius: var(--radius-sm);
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-weight: 600;
    font-size: 1rem;
    transition: all 0.2s ease;
}

.btn-undo:hover {
    background: rgba(255, 255, 255, 0.15);
    box-shadow: 0 0 15px rgba(255, 255, 255, 0.1);
    border-color: var(--text-primary);
    transform: translateY(-2px);
}

.btn-undo svg {
    width: 20px;
    height: 20px;
}

.btn-exit {
    background-color: #d9534f;
    color: white;
}
.btn-exit:hover {
    background-color: #c9302c;
}
/* Highlight for the last move */
.piece.last-move img {
    box-shadow: 0 0 15px 5px rgba(255, 255, 255, 0.8);
    transform: scale(1.1);
    transition: all 0.3s ease;
    z-index: 10;
}

.winning-line-container {
    position: absolute;
    top: 2.45%;
    left: 2.44%;
    width: 95.12%; /* 100% - 2.44% - 2.44% */
    height: 94.49%; /* 100% - 2.45% - 3.06% */
    z-index: 30;
    pointer-events: none;
    display: block;
}
.winning-line-anim {
    stroke-dasharray: 100;
    stroke-dashoffset: 100;
    animation: dash 1s linear forwards;
    filter: drop-shadow(0 0 5px orange);
}
@keyframes dash {
  to {
    stroke-dashoffset: 0;
  }
}
</style>
