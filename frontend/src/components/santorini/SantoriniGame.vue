<template>
  <div class="santorini-game min-h-screen flex flex-col items-center bg-gray-900">
    
    <!-- Game Area (Board) - Now at the Top -->
    <div class="game-area relative">
      <!-- Board Background -->
      <img src="../../assets/santorini/board.png" class="board-bg" alt="Board" />
      
      <!-- Grid Overlay -->
      <div class="grid-container">
        <div 
          v-for="(cell, index) in flatBoard" 
          :key="index"
          class="grid-cell"
          :style="cell.style"
          :class="{
            'cursor-pointer': isInteractive(cell.r, cell.c),
            'highlight-move': canMoveTo(cell.r, cell.c),
            'highlight-build': canBuildAt(cell.r, cell.c),
            'selected-source': isSelectedSource(cell.r, cell.c)
          }"
          @click="handleCellClick(cell.r, cell.c)"
        >
          <!-- Cell Content Stack -->
           <div class="cell-content">
             <!-- Building Block Level 1 -->
             <img v-if="cell.data.level >= 1" src="../../assets/santorini/block_1.png" class="asset base-block" />
             <!-- Building Block Level 2 -->
             <img v-if="cell.data.level >= 2" src="../../assets/santorini/block_2.png" class="asset mid-block" />
             <!-- Building Block Level 3 -->
             <img v-if="cell.data.level >= 3" src="../../assets/santorini/block_3.png" class="asset top-block" />
             <!-- Dome -->
             <img v-if="cell.data.level >= 4" src="../../assets/santorini/dome.png" class="asset dome" />
             
             <!-- Worker -->
             <!-- Dynamic lift: 25px per level approx? -->
             <img v-if="cell.data.worker === 'p1'" src="../../assets/santorini/worker_p1.png" class="asset worker" 
                  :style="{ transform: `translateY(-${(cell.data.level || 0) * 25}px)` }" />
             <img v-if="cell.data.worker === 'p2'" src="../../assets/santorini/worker_p2.png" class="asset worker" 
                  :style="{ transform: `translateY(-${(cell.data.level || 0) * 25}px)` }" />
             
             <!-- Ghost Worker (Movement Preview) -->
             <div v-if="step === 'build' && selectedMovePos.r === cell.r && selectedMovePos.c === cell.c" 
                  class="ghost-worker">
                  <img :src="getCurrentWorkerImage()" class="asset worker opacity-70" 
                       :style="{ transform: `translateY(-${(cell.data.level || 0) * 25}px)` }" />
             </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Game Info & Controls (Moved Below) -->
    <!-- ... -->

    <div class="game-footer w-full max-w-3xl mt-4 px-4 flex flex-col gap-4">
        
        <!-- Header Info Row -->
        <div class="header flex justify-between items-center w-full glass-panel p-4">
          <div>
            <h2 class="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-yellow-400 to-orange-300">
               Santorini
            </h2>
            <div class="text-sm text-gray-400">
               ID: {{ $route.params.id }} | Turno: 
               <span :class="currentTurn === 'p1' ? 'text-yellow-400 font-bold' : 'text-red-400 font-bold'">
                 {{ currentTurnPlayerName }}
               </span>
            </div>
          </div>
          
          <div class="status text-xl font-mono">
            {{ statusMessage }}
          </div>
    
          <router-link to="/santoriniActive" class="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded text-sm transition">
            Salir
          </router-link>
        </div>

        <!-- Controls Message Row -->
        <div class="controls glass-panel p-4 w-full text-center">
           <div v-if="myPlayerId && !isMyTurn" class="text-yellow-500 animate-pulse">
              Esperando al oponente...
           </div>
           <div v-if="step === 'select'" class="text-blue-300">
              Selecciona uno de tus trabajadores.
           </div>
           <div v-if="step === 'move'" class="text-green-300">
              Selecciona una casilla adyacente para MOVER.
              <button @click="resetSelection" class="ml-4 text-xs bg-gray-600 px-2 py-1 rounded">Cancelar</button>
           </div>
           <div v-if="step === 'build'" class="text-purple-300">
              Selecciona una casilla adyacente para CONSTRUIR.
              <button @click="resetSelection" class="ml-4 text-xs bg-gray-600 px-2 py-1 rounded">Cancelar</button>
           </div>
        </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { API_BASE, WS_BASE } from '../../config'
import p1WorkerImg from '../../assets/santorini/worker_p1.png'
import p2WorkerImg from '../../assets/santorini/worker_p2.png'

const route = useRoute()
const gameId = route.params.id

const CELL_COORDS = {
    '0,0': {x: 300, y: 160}, '0,1': {x: 525, y: 195}, '0,2': {x: 750, y: 230}, '0,3': {x: 975, y: 265}, '0,4': {x: 1200, y: 300},
    '1,0': {x: 332, y: 295}, '1,1': {x: 558, y: 311}, '1,2': {x: 783, y: 328}, '1,3': {x: 1008, y: 344}, '1,4': {x: 1233, y: 360},
    '2,0': {x: 365, y: 430}, '2,1': {x: 590, y: 428}, '2,2': {x: 815, y: 425}, '2,3': {x: 1040, y: 423}, '2,4': {x: 1265, y: 420},
    '3,0': {x: 398, y: 565}, '3,1': {x: 623, y: 544}, '3,2': {x: 848, y: 523}, '3,3': {x: 1073, y: 501}, '3,4': {x: 1298, y: 480},
    '4,0': {x: 430, y: 700}, '4,1': {x: 655, y: 660}, '4,2': {x: 880, y: 620}, '4,3': {x: 1105, y: 580}, '4,4': {x: 1330, y: 540},
}
const BOARD_WIDTH = 1536
const BOARD_HEIGHT = 838

// State
const game = ref(null)
const socket = ref(null)
// Auth State
const token = localStorage.getItem('token')
// Decode token to get username (sub)
const meUsername = token ? JSON.parse(atob(token.split('.')[1])).sub : null

// Interaction State
const step = ref('select') 
const selectedWorkerPos = ref(null) // {r, c}
const selectedMovePos = ref(null) // {r, c}
const validMovesCache = ref([])

// --- Computed ---

const currentTurn = computed(() => game.value?.current_turn)
const isMyTurn = computed(() => {
    if (!game.value) return false;
    
    // Check if I am P1
    if (game.value.player_p1_name === meUsername && game.value.current_turn === 'p1') return true;
    // Check if I am P2
    if (game.value.player_p2_name === meUsername && game.value.current_turn === 'p2') return true;
    
    return false;
})

const myPlayerId = computed(() => {
    // Return something truthy if logged in, but we rely on username matching above
    return meUsername; 
})

const currentTurnPlayerName = computed(() => {
    if (!game.value) return ''
    return game.value.current_turn === 'p1' ? (game.value.player_p1_name || 'P1') : (game.value.player_p2_name || 'P2')
})

const statusMessage = computed(() => {
    if (!game.value) return 'Cargando...'
    if (game.value.status === 'in_progress') return 'En Juego'
    if (game.value.status === 'p1_won') return '¡Victoria Amarilla!'
    if (game.value.status === 'p2_won') return '¡Victoria Roja!'
    return game.value.status
})

const flatBoard = computed(() => {
    if (!game.value || !game.value.board) return []
    const arr = []
    for (let r = 0; r < 5; r++) {
        for (let c = 0; c < 5; c++) {
            const coord = CELL_COORDS[`${r},${c}`] || {x:0, y:0}
            const leftPct = (coord.x / BOARD_WIDTH) * 100
            const topPct = (coord.y / BOARD_HEIGHT) * 100
            const zIndex = r + c + 10 // Base Z-index

            arr.push({ 
                r, 
                c, 
                data: game.value.board[r][c],
                style: {
                    left: `${leftPct}%`,
                    top: `${topPct}%`,
                    zIndex: zIndex
                }
            })
        }
    }
    return arr
})

// ... (rest of logic)


// --- Logic ---

function getCurrentWorkerImage() {
    return game.value.current_turn === 'p1' ? p1WorkerImg : p2WorkerImg
}

function isInteractive(r, c) {
    if (!isMyTurn.value || game.value.status !== 'in_progress') return false
    
    // If selecting worker, only my workers are interactive
    if (step.value === 'select') {
        const cell = game.value.board[r][c]
        return cell.worker === game.value.current_turn
    }
    // If moving, potential move spots are interactive (filtered by UI)
    if (step.value === 'move') return canMoveTo(r, c)
    // If building, potential build spots
    if (step.value === 'build') return canBuildAt(r, c)
    
    return false
}

function isSelectedSource(r, c) {
    return selectedWorkerPos.value && selectedWorkerPos.value.r === r && selectedWorkerPos.value.c === c
}

function canMoveTo(r, c) {
    if (step.value !== 'move') return false
    // Basic rules check: adjacent, not occupied, max 1 level up, not dome
    const fromR = selectedWorkerPos.value.r
    const fromC = selectedWorkerPos.value.c
    const dr = Math.abs(r - fromR)
    const dc = Math.abs(c - fromC)
    if (dr > 1 || dc > 1 || (dr === 0 && dc === 0)) return false
    
    const target = game.value.board[r][c]
    const source = game.value.board[fromR][fromC]
    
    if (target.worker !== null) return false
    if (target.level === 4) return false
    if (target.level > source.level + 1) return false
    
    return true
}

function canBuildAt(r, c) {
    if (step.value !== 'build') return false
    // Rule: Adjacent to moved position (selectedMovePos)
    // AND not occupied by OTHER worker (but could be the old spot of THIS worker, which is now empty)
    // Note: The UI still shows the worker at 'selectedWorkerPos' because we haven't committed the move.
    
    const fromR = selectedMovePos.value.r
    const fromC = selectedMovePos.value.c
    const dr = Math.abs(r - fromR)
    const dc = Math.abs(c - fromC)
    if (dr > 1 || dc > 1 || (dr === 0 && dc === 0)) return false
    
    const target = game.value.board[r][c]
    
    // Check occupancy. 
    // The target cannot have a worker, UNLESS it is the 'selectedWorkerPos' (since that worker is conceptually 'moving' away)
    const isOldWorkerSpot = (r === selectedWorkerPos.value.r && c === selectedWorkerPos.value.c)
    if (target.worker !== null && !isOldWorkerSpot) return false
    
    if (target.level === 4) return false
    
    return true
}

function handleCellClick(r, c) {
    console.log(`Clicked cell [${r}, ${c}]`);
    console.log(`My Turn? ${isMyTurn.value}, Status: ${game.value?.status}, Step: ${step.value}`);
    
    if (!isMyTurn.value) {
        console.warn("Not my turn!");
        return;
    }
    
    if (step.value === 'select') {
        const cell = game.value.board[r][c]
        console.log("Checking worker at cell:", cell);
        console.log("Current turn player:", game.value.current_turn);
        
        if (cell.worker === game.value.current_turn) {
            console.log("Worker selected!");
            selectedWorkerPos.value = { r, c }
            step.value = 'move'
        } else {
             console.log("No valid worker at this cell.");
        }
    } else if (step.value === 'move') {
        if (canMoveTo(r, c)) {
            selectedMovePos.value = { r, c }
            step.value = 'build'
        } else if (game.value.board[r][c].worker === game.value.current_turn) {
            // Change selection
            selectedWorkerPos.value = { r, c }
            step.value = 'move'
        }
    } else if (step.value === 'build') {
        if (canBuildAt(r, c)) {
            submitMove(r, c)
        }
    }
}

function resetSelection() {
    step.value = 'select'
    selectedWorkerPos.value = null
    selectedMovePos.value = null
}

async function submitMove(buildR, buildC) {
    try {
        const payload = {
            worker_start: [selectedWorkerPos.value.r, selectedWorkerPos.value.c],
            move_to: [selectedMovePos.value.r, selectedMovePos.value.c],
            build_at: [buildR, buildC]
        }
        
        await fetch(`${API_BASE}/santorini/${gameId}/move`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            body: JSON.stringify(payload)
        })
        
        // Reset local state, wait for WS update
        resetSelection()
    } catch (e) {
        console.error("Move failed", e)
        alert("Movimiento inválido o error del servidor")
        resetSelection()
    }
}

// --- API & WS ---

async function fetchGame() {
    const res = await fetch(`${API_BASE}/santorini/${gameId}`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
    })
    game.value = await res.json()
}

function connectWs() {
    socket.value = new WebSocket(`${WS_BASE}/ws/santorini/${gameId}`)
    socket.value.onmessage = (event) => {
        const data = JSON.parse(event.data)
        if (data.type === 'move' || data.type === 'create') {
            // Update board and status
            game.value.board = JSON.parse(data.board)
            game.value.status = data.status
            game.value.current_turn = (data.by === 'p1' ? 'p2' : 'p1') // 'by' is who MOVED, so turn is next
            
            // If game ended, turn might not switch conventionally, but status handles UI
             if (data.status.includes('won')) {
                 // Keep turn as winner or null? Doesn't matter much if filtered by status
             }
        }
    }
}

onMounted(async () => {
    await fetchGame()
    connectWs()
})

onUnmounted(() => {
    if (socket.value) socket.value.close()
})
</script>

<style scoped>
.glass-panel {
  background: rgba(30, 41, 59, 0.8);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
}

.santorini-game {
  height: 100vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background-color: #111827; /* gray-900 */
}

.game-area {
  width: min(98vw, calc((100vh - 250px) * (2816 / 1536)));
  max-width: none;
  aspect-ratio: 2816 / 1536;
  height: auto;
  position: relative;
  user-select: none;
}

.board-bg {
  width: 100%;
  height: 100%;
  object-fit: contain; /* Ensure image is not distorted */
  border-radius: 8px;
  box-shadow: 0 20px 50px rgba(0,0,0,0.5);
}

/* ... */

.grid-container {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none; /* Let clicks pass through if needed, but cells have pointer-events auto */
}

.grid-cell {
  position: absolute;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 0; /* Position refers to center point */
  height: 0;
  transform: translate(-50%, -50%); /* Centering magic */
  pointer-events: auto; /* Re-enable clicks */
  
  /* Debugging dot */
  /* background: red; width: 4px; height: 4px; border-radius: 50%; */
}

.cell-content {
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 120px; /* Reduced touch target width approx */
  height: 120px;
  display: flex;
  justify-content: center;
  align-items: flex-end; /* Stack from bottom up */
}

.asset {
  position: absolute;
  width: 100%; /* Relative to cell-content width */
  pointer-events: none;
  transition: transform 0.3s ease;
  bottom: 0; /* Base assets at bottom of content box */
}

.asset.base-block { z-index: 1; }
.asset.mid-block { z-index: 2; bottom: 25px; } /* Adjust per visual overlap */
.asset.top-block { z-index: 3; bottom: 50px; }
.asset.dome { z-index: 4; bottom: 75px; }

.asset.worker {
  bottom: 22px; /* Lift worker slightly higher than blocks to center on tile top */
  z-index: 10;
  width: 70%; 
  left: 15%; 
}

/* Animations / Highlights */
.highlight-move {
  background: rgba(0, 255, 0, 0.4);
  box-shadow: inset 0 0 20px rgba(0, 255, 0, 0.6);
  border-radius: 50%;
  transform: scale(0.8) scaleY(0.6);
}

.highlight-build {
  background: rgba(160, 32, 240, 0.4);
  box-shadow: inset 0 0 20px rgba(160, 32, 240, 0.6);
  border-radius: 50%;
  transform: scale(0.8) scaleY(0.6);
}

.selected-source {
  background: rgba(255, 255, 0, 0.4);
  box-shadow: 0 0 15px rgba(255, 255, 0, 0.8);
  border-radius: 50%;
  transform: scale(0.9) scaleY(0.6);
}

.ghost-worker {
  position: absolute;
  width: 100%;
  height: 100%;
  pointer-events: none;
  opacity: 0.6;
  filter: grayscale(100%);
  z-index: 20; /* Ensure on top of blocks */
}
</style>
