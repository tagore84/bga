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
            Deshacer
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

async function fetchState() {
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
    if (!confirm("¿Seguro que quieres deshacer el último movimiento?")) return;
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
            if (msg.status) status.value = msg.status;
            
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
    width: 780px;
    height: 490px;
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
    top: 12px;
    bottom: 15px; 
    left: 19px;
    right: 19px;
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
    background-color: #f0ad4e;
    color: white;
}
.btn-undo:hover {
    background-color: #ec971f;
}

.btn-exit {
    background-color: #d9534f;
    color: white;
}
.btn-exit:hover {
    background-color: #c9302c;
}

.icon-undo {
    width: 18px;
    height: 18px;
}
</style>
