<template>
  <div class="santorini-game min-h-screen flex flex-col items-center bg-gray-900">
    
    <!-- Header (Top) -->
    <div class="header w-full max-w-3xl glass-panel p-4 mb-4 flex justify-between items-center">
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
        
        <div class="status text-xl font-mono text-gray-200">
            {{ statusMessage }}
        </div>
    </div>

    <!-- Game Area (Board - Middle) -->
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
            'cursor-pointer': isInteractive(cell.r, cell.c)
          }"
          @click="handleCellClick(cell.r, cell.c)"
        >
          <!-- Highlights / Markers (Background Layer) -->
          <div class="cell-marker"
               :class="{
                 'highlight-move': canMoveTo(cell.r, cell.c),
                 'highlight-build': canBuildAt(cell.r, cell.c) || (step === 'place' && canPlaceAt(cell.r, cell.c)),
                 'selected-source': isSelectedSource(cell.r, cell.c)
               }"
          ></div>

          <!-- Cell Content Stack -->
           <div class="cell-content">
             <!-- Building Block Level 1 -->
             <!-- Building Block Level 1 -->
             <img v-if="cell.data.level === 1" src="../../assets/santorini/block_1.png" class="asset base-block" />
             <!-- Building Block Level 2 -->
             <img v-if="cell.data.level === 2" src="../../assets/santorini/block_2.png" class="asset mid-block" />
             <!-- Building Block Level 3 -->
             <img v-if="cell.data.level === 3" src="../../assets/santorini/block_3.png" class="asset top-block" />
             <!-- Dome -->
             <img v-if="cell.data.level === 4" src="../../assets/santorini/dome.png" class="asset dome" />
             
             <!-- Worker -->
             <!-- Dynamic lift: 30px per level to match visual scale better and avoid clipping -->
             <!-- Transform logic includes translateX(-50%) to keep it centered horizontally 
                  and translateY for the vertical             <!-- Worker -->
             <img v-if="cell.data.worker === 'p1'" src="../../assets/santorini/worker_p1.png" class="asset worker" 
                  :style="{ transform: `translate(-50%, -${getWorkerTy(cell.data.level)}px)` }" />
             <img v-if="cell.data.worker === 'p2'" src="../../assets/santorini/worker_p2.png" class="asset worker" 
                  :style="{ transform: `translate(-50%, -${getWorkerTy(cell.data.level)}px)` }" />
             
             <!-- Ghost Worker (Movement Preview) -->
             <div v-if="step === 'build' && selectedMovePos.r === cell.r && selectedMovePos.c === cell.c" 
                  class="ghost-worker">
                  <img :src="getCurrentWorkerImage()" class="asset worker opacity-70" 
                       :style="{ transform: `translate(-50%, -${getWorkerTy(cell.data.level)}px)` }" />
             </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Game Info & Controls (Moved Below) -->
    <!-- Controls (Bottom) -->
    <div class="controls w-full max-w-3xl mt-4 flex flex-col items-center gap-4">
        
        <!-- Action Prompts -->
        <div class="glass-panel p-4 w-full text-center min-h-[80px] flex flex-col justify-center items-center">
            <div v-if="myPlayerId && !isMyTurn" class="text-yellow-500 animate-pulse text-lg">
               Esperando al oponente...
            </div>
            <div v-else-if="step === 'select'" class="text-blue-300 text-lg">
               Selecciona uno de tus trabajadores.
            </div>
            <div v-else-if="step === 'move'" class="text-green-300 text-lg flex items-center gap-4">
               <span>Selecciona una casilla adyacente para <b>MOVER</b>.</span>
               <button @click="resetSelection" class="btn-secondary text-sm">Cancelar</button>
            </div>
            <div v-else-if="step === 'build'" class="text-purple-300 text-lg flex items-center gap-4">
               <span>Selecciona una casilla adyacente para <b>CONSTRUIR</b>.</span>
               <button @click="resetSelection" class="btn-secondary text-sm">Cancelar</button>
            </div>
            <div v-else-if="step === 'place'" class="text-blue-300 text-lg">
               <span>Selecciona una casilla vacía para <b>COLOCAR</b> tu trabajador.</span>
            </div>
        </div>

        <!-- Meta Controls -->
        <div class="w-full flex justify-center">
             <router-link to="/games" class="btn-danger">
                Salir del Juego
             </router-link>
        </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { API_BASE, WS_BASE } from '../../config'
import p1WorkerImg from '../../assets/santorini/worker_p1.png'
import p2WorkerImg from '../../assets/santorini/worker_p2.png'

const route = useRoute()
const gameId = route.params.id

const CELL_COORDS = {
    '0,0': {x: 360, y: 410}, '0,1': {x: 465, y: 355}, '0,2': {x: 570, y: 300}, '0,3': {x: 670, y: 235}, '0,4': {x: 770, y: 180},
    '1,0': {x: 465, y: 465}, '1,1': {x: 570, y: 410}, '1,2': {x: 670, y: 350}, '1,3': {x: 770, y: 290}, '1,4': {x: 870, y: 235},
    '2,0': {x: 570, y: 520}, '2,1': {x: 670, y: 465}, '2,2': {x: 770, y: 410}, '2,3': {x: 870, y: 350}, '2,4': {x: 973, y: 290},
    '3,0': {x: 670, y: 580}, '3,1': {x: 770, y: 520}, '3,2': {x: 870, y: 465}, '3,3': {x: 973, y: 410}, '3,4': {x: 1070, y: 350},
    '4,0': {x: 770, y: 650}, '4,1': {x: 870, y: 580}, '4,2': {x: 973, y: 520}, '4,3': {x: 1070, y: 465}, '4,4': {x: 1180, y: 410},
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
            const coordKey = `${r},${c}`;
            const coord = CELL_COORDS[coordKey] || {x:0, y:0}
            
            const leftPct = (coord.x / BOARD_WIDTH) * 100
            const topPct = (coord.y / BOARD_HEIGHT) * 100
            // Sort by depth: (4,0) is front, (0,4) is back.
            // increasing r moves down (front), increasing c moves up (back).
            const zIndex = (r - c) + 20 

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


// --- Logic ---

// ... (previous code)

function getCurrentWorkerImage() {
    return game.value.current_turn === 'p1' ? p1WorkerImg : p2WorkerImg
}

function getWorkerTy(level) {
    if (!level) return 0;
    // Tuned based on user feedback:
    // L1: Lower slightly (was 30 -> 26)
    // L2: Lower a bit more (was 60 -> 52)
    // L3: Perfect (was 90 -> 90)
    const map = {
        0: 0,
        1: 33, 
        2: 60,
        3: 98
    }
    return map[level] || (level * 30)
}

function isInteractive(r, c) {
// ...
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
    // If placing, empty spots
    if (step.value === 'place') return canPlaceAt(r, c)
    
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

function canPlaceAt(r, c) {
    if (step.value !== 'place') return false
    const cell = game.value.board[r][c]
    return cell.worker === null && cell.level !== 4
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
            // Check if this move wins the game (Level 3)
            const target = game.value.board[r][c]
            if (target.level === 3) {
                // Instant win move, no build needed
                selectedMovePos.value = { r, c }
                submitMove(null, null) 
            } else {
                selectedMovePos.value = { r, c }
                step.value = 'build'
            }
        } else if (game.value.board[r][c].worker === game.value.current_turn) {
            // Change selection
            selectedWorkerPos.value = { r, c }
            step.value = 'move'
        }
    } else if (step.value === 'build') {
        if (canBuildAt(r, c)) {
            submitMove(r, c)
        }
    } else if (step.value === 'place') {
        if (canPlaceAt(r, c)) {
            submitPlacement(r, c)
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
            move_type: 'move_build',
            worker_start: [selectedWorkerPos.value.r, selectedWorkerPos.value.c],
            move_to: [selectedMovePos.value.r, selectedMovePos.value.c],
            build_at: (buildR != null && buildC != null) ? [buildR, buildC] : null
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

async function submitPlacement(r, c) {
    try {
        const payload = {
            move_type: 'place_worker',
            move_to: [r, c]
        }
        
        await fetch(`${API_BASE}/santorini/${gameId}/move`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            body: JSON.stringify(payload)
        })
        
        // Wait for WS
    } catch (e) {
        console.error("Placement failed", e)
        alert("Colocación inválida")
    }
}

// Watch for turn changes to set step
watch(game, (newGame) => {
    if (!newGame) return
    
    if (isMyTurn.value) {
        // Count my workers
        let myWorkers = 0
        newGame.board.forEach(row => {
            row.forEach(cell => {
                if (cell.worker === newGame.current_turn) myWorkers++
            })
        })
        
        if (myWorkers < 2) {
            step.value = 'place'
        } else {
            // Only reset to select if we were in a non-active state or wrong state?
            // Or just force select if it's my turn and I have workers.
            // But if I am in middle of 'move' (from UI interaction), don't reset?
            // Actually, if game state updates (e.g. from server), I should probably reset to Select unless I'm ignoring updates.
            // But here, update comes from WS after MY move? Or opponent's move.
            // If it's my turn now, it means opponent just moved. So I should start at 'select'.
            if (step.value !== 'move' && step.value !== 'build') {
                 step.value = 'select'
            }
        }
    } else {
        // Not my turn
        step.value = 'select' // Reset logic
    }
}, { deep: true })

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
            
            // Use authoritative turn from server if available (Placement Phase support)
            if (data.current_turn) {
                game.value.current_turn = data.current_turn
            } else {
                // Fallback for legacy events (should not happen after update)
                game.value.current_turn = (data.by === 'p1' ? 'p2' : 'p1') 
            }
            
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
/* UI Panels */
.glass-panel {
  background: rgba(30, 41, 59, 0.85); /* Slightly darker/opaque */
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0,0,0,0.3);
}

.santorini-game {
  min-height: 100vh;
  /* Removed fixed height 100vh to allow scrolling on small screens if needed */
  overflow-y: auto; 
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start; /* Top alignment */
  background-color: #111827;
  padding: 1rem;
}

/* Board Area */
.game-area {
  /* Dynamic sizing based on viewport */
  width: min(95vw, 1200px); 
  /* Maintain Aspect Ratio */
  aspect-ratio: 2816 / 1536;
  position: relative;
  user-select: none;
  /* Add margin to separate from top/bottom */
  margin: 10px 0; 
}

.board-bg {
  width: 100%;
  height: 100%;
  object-fit: contain; 
  border-radius: 8px;
  box-shadow: 0 20px 50px rgba(0,0,0,0.5);
}

.grid-container {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.grid-cell {
  position: absolute;
  display: flex;
  align-items: center; 
  justify-content: center;
  /* Relative width/height to support scaling */
  width: 7.8%; 
  height: 8.6%; 
  transform: translate(-50%, -50%); 
  pointer-events: auto; 
  cursor: pointer; 
  z-index: 100; 
}

.cell-marker {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 120%; /* Relative to cell */
  height: 120%; 
  pointer-events: none;
  border-radius: 50%;
  opacity: 0; 
  transition: all 0.2s ease;
  z-index: 0; 
}

.cell-content {
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 120%; 
  height: 200%; /* Allow height for vertical stack */
  pointer-events: none;
  display: flex;
  justify-content: center;
  align-items: flex-end; 
}

.asset {
  position: absolute;
  width: 100%; 
  pointer-events: none;
  transition: transform 0.3s ease;
  bottom: 0; 
}

.asset.base-block { z-index: 1; }
.asset.mid-block { z-index: 2; } 
.asset.top-block { z-index: 3; }
.asset.dome { z-index: 4; }

.asset.worker {
  bottom: 8%; /* Relative offset */
  z-index: 10;
  width: 40%; 
  left: 50%; 
  transform-origin: bottom center;
  filter: drop-shadow(4px 4px 3px rgba(0,0,0,0.5));
}

/* Marker States */
.highlight-move {
  opacity: 1;
  background: rgba(0, 255, 0, 0.4);
  box-shadow: inset 0 0 20px rgba(0, 255, 0, 0.6);
  transform: translate(-50%, -50%) scale(1.0);
}

.highlight-build {
  opacity: 1;
  background: rgba(160, 32, 240, 0.4);
  box-shadow: inset 0 0 20px rgba(160, 32, 240, 0.6);
  transform: translate(-50%, -50%) scale(1.0);
}

.selected-source {
  opacity: 1;
  background: rgba(255, 255, 0, 0.4);
  box-shadow: 0 0 15px rgba(255, 255, 0, 0.8);
  transform: translate(-50%, -50%) scale(1.1);
}

.ghost-worker {
  position: absolute;
  width: 100%;
  height: 100%;
  pointer-events: none;
  opacity: 0.6;
  filter: grayscale(100%);
  z-index: 20; 
}

/* Buttons */
.btn-danger {
    background: rgba(220, 38, 38, 0.2);
    color: #fca5a5;
    border: 1px solid rgba(220, 38, 38, 0.4);
    padding: 0.6rem 1.2rem;
    border-radius: 8px;
    font-weight: 600;
    transition: all 0.2s;
    text-decoration: none;
    display: inline-block;
}
.btn-danger:hover {
    background: rgba(220, 38, 38, 0.4);
    color: #fff;
    box-shadow: 0 0 10px rgba(220, 38, 38, 0.2);
}

.btn-secondary {
    background: rgba(255, 255, 255, 0.05); /* Subtle background */
    border: 1px solid rgba(255, 255, 255, 0.2);
    color: rgba(255, 255, 255, 0.8);
    border-radius: 20px; /* Rounded pill shape */
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease-in-out;
    padding: 0.4rem 1rem; /* Adjust padding in CSS instead of utility if possible, but utility overrides. 
                             Wait, utility is inline <button class="... py-1 px-3">. 
                             We can remove utility classes in next step or just override here with !important if needed, 
                             or rely on these being specific enough? Utility usually wins.
                             I will update the HTML to remove utility classes or trust this looks good with them.
                             Let's stick to the color/border change primarily here. */
}
.btn-secondary:hover {
    background: rgba(255, 255, 255, 0.15);
    color: #fff;
    border-color: rgba(255, 255, 255, 0.5);
    transform: translateY(-1px);
}
</style>
