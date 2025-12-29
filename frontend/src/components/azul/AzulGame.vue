<template>
  <div class="azul-game-container">
      <div class="glass-panel header-section mb-2">
        <div class="header-row">
          <h2>Azul Match #{{ gameId }}</h2>
          <button @click="goHome" class="btn-danger small-btn">Exit Game</button>
        </div>
        
        <div class="user-status mt-1">
          <p><span class="label">Player:</span> {{ me }}</p>
          <p><span class="label">Current Turn:</span> <span class="highlight">{{ gameState?.turno_actual }}</span></p>
        </div>
      </div>

      <div v-if="!loaded" class="text-center">Loading game state...</div>
      <div v-else-if="error" class="error-msg">Error: {{ error }}</div>
      
      <div v-else-if="gameState">
        <div class="glass-panel players-panel mb-2">
             <div v-if="gameState.jugadores" class="players-grid">
              <div 
                v-for="(jugador, id) in gameState.jugadores" 
                :key="id" 
                class="player-card" 
                :class="{ 'active': gameState.turno_actual === jugador.name }"
              >
                <div class="player-header">
                  <span class="player-name">{{ jugador.name || ('Player ' + id) }}</span>
                  <span v-if="jugador.name === me" class="me-badge">(YOU)</span>
                  <div v-if="gameState.turno_actual === jugador.name && aiThinking" class="ai-spinner" title="AI Thinking...">⏳</div>
                </div>
                <div class="player-score">{{ jugador.puntos }} pts</div>
                <div v-if="gameState.turno_actual === jugador.name" class="turn-indicator">⭐ ACTIVO</div>
              </div>
             </div>
             <div v-else>No player data available.</div>
        </div>

        <!-- Action Bar -->
        <div class="actions-bar" v-if="selectedRow !== null || selectedColor !== null">
          <div class="glass-panel action-panel">
            <span class="action-text">Confirm Move?</span>
            <div class="action-buttons">
              <button 
                v-if="selectedRow !== null" 
                @click="confirmMove" 
                :disabled="confirmingMove" 
                class="btn-primary"
              >
                {{ confirmingMove ? 'Processing...' : 'Confirm Move' }}
              </button>
              
              <button 
                v-if="selectedColor !== null" 
                @click="cancelMove"
                class="btn-secondary"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
        <v-stage
          ref="stageRef"
          :width="Math.max(
            1000,
            Math.max(
              gameState?.expositores?.length * 160 + 100,
              610 + ((gameState?.jugadores && Object.keys(gameState.jugadores).length > 1 ? 2 : 1) * 360)
            )
          )"
          :height="250 + Math.ceil(Object.keys(gameState.jugadores).length / 2) * 240">
          <v-layer>
            <template v-for="(jugador, jIndex) in Object.values(gameState.jugadores)" :key="'jugador-' + jIndex">
              <v-image
                :image="boardImage"
                :x="610 + (jIndex % 2) * 360"
                :y="250 + Math.floor(jIndex / 2) * 240"
                :width="330"
                :height="220"
                :stroke="gameState?.turno_actual === jugador.name ? 'red' : 'black'"
                :strokeWidth="gameState?.turno_actual === jugador.name ? 5 : 1"
              />
              <template v-if="jugador.name === me">
                <template v-for="row in 5" :key="'fila-' + row">
                  <v-rect
                    :x="(610 + (jIndex % 2) * 360) + 13 - 29*row + 29*5"
                    :y="(250 + Math.floor(jIndex / 2) * 240) + 14 + (row-1) * 29"
                    :width="29*row - 2"
                    :height="27"
                    :fill="getRowFillState(row)"
                    :opacity="getRowOpacity(row)"
                    :stroke="selectedRow === row ? 'red' : isSelectableRow(row) ? 'gray' : 'black'"
                    :strokeWidth="selectedRow === row ? 3 : isSelectableRow(row) ? 2 : 1"
                    :onclick="() => handleRowClick(row)"
                  />
                </template>
                <!-- Floor option (row 0) -->
                <v-rect
                  :x="(610 + (jIndex % 2) * 360) + 13"
                  :y="(250 + Math.floor(jIndex / 2) * 240) + 175"
                  :width="210"
                  :height="28"
                  :fill="getRowFillState(0)"
                  :opacity="getRowOpacity(0)"
                  :stroke="selectedRow === 0 ? 'red' : isSelectableRow(0) ? 'gray' : 'black'"
                  :strokeWidth="selectedRow === 0 ? 3 : isSelectableRow(0) ? 2 : 1"
                  :onclick="() => handleRowClick(0)"
                />
              </template>
              <template v-for="(fila, y) in jugador.patrones" :key="'patron-fila-' + y + '-j' + jIndex">
                <template v-for="(casilla, i) in fila" :key="'patron-casilla-' + y + '-' + i + '-j' + jIndex">
                  <template v-if="casilla !== null && casilla !== ''">
                    <v-image
                      :x="(610 + (jIndex % 2) * 360) + 129 - 29 * i"
                      :y="(250 + Math.floor(jIndex / 2) * 240) + 14 + y * 29"
                      :width="28"
                      :height="28"
                      :image="getColorImg(casilla)"
                      :onclick="() => handleRowClick(y + 1)"
                      :stroke="isLastMoveTile(jugador, y, i, false) ? 'yellow' : null"
                      :strokeWidth="isLastMoveTile(jugador, y, i, false) ? 4 : 0"
                      :shadowColor="isLastMoveTile(jugador, y, i, false) ? 'orange' : null"
                      :shadowBlur="isLastMoveTile(jugador, y, i, false) ? 20 : 0"
                    />
                  </template>
                  <template v-else>
                    <v-rect
                      :x="(610 + (jIndex % 2) * 360) + 13 - 29 * (y + 1) + 29 * (i + 1) + 116"
                      :y="(250 + Math.floor(jIndex / 2) * 240) + 14 + y * 29"
                      :width="28"
                      :height="28"
                      :fill="'white'"
                      stroke="black"
                      :onclick="() => handleRowClick(y + 1)"
                    />
                  </template>
                </template>
              </template>
              <!-- Renderizar muro (pared) -->
              <template v-for="(fila, r) in jugador.pared" :key="'pared-fila-' + r + '-j' + jIndex">
                 <template v-for="(casilla, c) in fila" :key="'pared-casilla-' + r + '-' + c + '-j' + jIndex">
                    <v-image v-if="casilla !== null"
                      :x="(610 + (jIndex % 2) * 360) + 175 + c * 29"
                      :y="(250 + Math.floor(jIndex / 2) * 240) + 14 + r * 29"
                      :width="28"
                      :height="28"
                      :image="getColorImg(casilla)"
                    />
                 </template>
              </template>
              <!-- Renderizar fichas del suelo -->
              <template v-if="jugador.suelo">
                <v-image
                  v-for="(casilla, i) in jugador.suelo"
                  :key="'suelo-' + i + '-j' + jIndex"
                  :x="(610 + (jIndex % 2) * 360) + 13 + i * 30"
                  :y="(250 + Math.floor(jIndex / 2) * 240) + 175"
                  :width="28"
                  :height="28"
                  :image="getColorImg(casilla)"
                  :stroke="isLastMoveTile(jugador, -1, i, true) ? 'yellow' : null"
                  :strokeWidth="isLastMoveTile(jugador, -1, i, true) ? 4 : 0"
                  :shadowColor="isLastMoveTile(jugador, -1, i, true) ? 'orange' : null"
                  :shadowBlur="isLastMoveTile(jugador, -1, i, true) ? 20 : 0"
                />
              </template>
              <!-- First player tile on floor -->
              <v-image
                v-if="jugador.tiene_ficha_inicial && !gameState?.first_player_marker_in_center"
                :x="(610 + (jIndex % 2) * 360) + 13 + (jugador.suelo?.length || 0) * 30"
                :y="(250 + Math.floor(jIndex / 2) * 240) + 175"
                :width="30"
                :height="30"
                :image="firstPlayerTileImage"
              />
            </template>
            <template v-for="(expositor, index) in gameState?.expositores || []" :key="index">
              <v-image
                :image="factoryImage"
                :x="index * 160"
                :y="50"
                :width="140"
                :height="140"
              />
              <v-image
                v-for="(color, i) in expositor"
                :key="i"
                :x="index * 160 + 32 + (i % 2) * 50"
                :y="80 + Math.floor(i / 2) * 50"
                :width="30"
                :height="30"
                :image="getColorImg(color)"
                :onclick="() => handleFactoryClick(index, color)"
                :opacity="isSelectable(index, color) ? 1 : 0.4"
                :stroke="isSelected(index, color) ? 'red' : null"
                :strokeWidth="isSelected(index, color) ? 3 : 0"
              />
            </template>
            <template v-for="(color, i) in gameState?.centro" :key="'centro-' + i">
              <v-image
                :x="100 + (i % 5) * 40"
                :y="230 + Math.floor(i / 5) * 40"
                :width="30"
                :height="30"
                :image="getColorImg(color)"
                :onclick="() => handleCenterClick(color)"
                :opacity="isSelectable('centro', color) ? 1 : 0.4"
                :stroke="isSelected('centro', color) ? 'red' : null"
                :strokeWidth="isSelected('centro', color) ? 3 : 0"
              />
            </template>
            <!-- First player tile in center -->
            <v-image
              v-if="gameState?.first_player_marker_in_center"
              :x="60"
              :y="230"
              :width="35"
              :height="35"
              :image="firstPlayerTileImage"
            />
          </v-layer>
          <v-layer>
            <v-image
              v-for="(pieza, i) in animatedPieces"
              :key="'anim-' + i"
              :x="pieza.x"
              :y="pieza.y"
              :width="30"
              :height="30"
              :image="getColorImg(pieza.color)"
              :config="{ id: 'anim-' + i }"
            />
          </v-layer>
        </v-stage>
      </div>
      
      <div v-if="gameState?.log && gameState.log.length > 0" class="game-log" ref="logContainer">
        <h3>Registro de Movimientos</h3>
        <ul>
          <li v-for="(entry, index) in gameState.log" :key="index">{{ entry }}</li>
        </ul>
      </div>
        <div class="debug-section" style="margin-top: 20px; border-top: 1px solid #ccc; padding-top: 10px; display: flex; align-items: center; gap: 20px;">
        <button @click="debugGame">🔍 Debug Estado</button>
        <label v-if="isNeuralVisionAvailable" style="display: flex; align-items: center; gap: 5px; cursor: pointer;">
          <input type="checkbox" v-model="neuralVisionEnabled">
          🧠 Neural Vision (AI Analysis)
        </label>
        <div v-else style="color: grey; font-style: italic; font-size: 0.9em;">
             (Neural Vision not available - No DeepMCTS AI in game)
        </div>
      </div>
      
      <NeuralVision 
        v-if="showNeuralVision" 
        :data="visualizationData" 
        @continue="handleContinue" 
      />

      <GameOverModal
        v-if="gameState?.terminado"
        :players="gameState.jugadores"
        :me="me"
        @home="goHome"
      />
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick, watch, computed } from 'vue'
// ... existing imports ...

function debugGame() {
  console.group("--- DEBUG GAME STATE ---")
  console.log("GameState:", JSON.parse(JSON.stringify(gameState.value)))
  console.log("Me:", me)
  console.log("Selected Color:", selectedColor.value, typeof selectedColor.value)
  console.log("Selected Factory:", selectedFactory.value)
  console.log("Selected Row:", selectedRow.value)

  const jugador = Object.values(gameState.value?.jugadores || {}).find(j => j.name === me || j.id === me)
  if (jugador) {
    console.log("Jugador encontrado:", JSON.parse(JSON.stringify(jugador)))
    console.group("Row Eligibility Check")
    for (let r = 0; r <= 5; r++) {
      const eligible = isSelectableRow(r)
      console.log(`Row ${r}: ${eligible ? 'VALID' : 'INVALID'}`)
      if (r > 0) {
         const rowIndex = r - 1
         const patron = jugador.patrones[rowIndex]
         const filledCount = patron ? patron.filter(c => c !== null && c !== '' && c !== -1).length : 0
         const existingColor = patron ? patron.find(c => c !== null && c !== '' && c !== -1) : undefined
         const colorVal = parseInt(selectedColor.value)
         const wallCol = selectedColor.value !== null ? getWallColumn(r, colorVal) : 'N/A'
         const wallCell = (jugador.pared && jugador.pared[rowIndex] && selectedColor.value !== null) ? jugador.pared[rowIndex][wallCol] : 'N/A'
         
         console.log(`  - Patron:`, patron)
         console.log(`  - Filled: ${filledCount}/${r}`)
         console.log(`  - Existing Color: ${existingColor} vs Selected: ${colorVal}`)
         console.log(`  - Wall Col: ${wallCol}, Cell Value: ${wallCell}`)
      }
    }
    console.groupEnd()
  } else {
    console.error("Jugador NOT found for 'me':", me)
  }
  console.groupEnd()
}
const stageRef = ref(null)
const confirmingMove = ref(false)
const logContainer = ref(null)

import NeuralVision from './NeuralVision.vue'
import GameOverModal from './GameOverModal.vue'
import { useRoute, useRouter } from 'vue-router'
import boardImg from '@/assets/azul/board.png'
import factoryImg from '@/assets/azul/factory_0.png'
import blueImg from '@/assets/azul/blue.png'
import yellowImg from '@/assets/azul/yellow.png'
import redImg from '@/assets/azul/red.png'
import blackImg from '@/assets/azul/black.png'
import orangeImg from '@/assets/azul/orange.png'
import firstPlayerTileImg from '@/assets/azul/first_player_tile.png'
import { useImage } from 'vue-konva'

const [boardImage] = useImage(boardImg)
const [factoryImage] = useImage(factoryImg)

const [blueImage] = useImage(blueImg)
const [yellowImage] = useImage(yellowImg)
const [redImage] = useImage(redImg)
const [blackImage] = useImage(blackImg)
const [orangeImage] = useImage(orangeImg)
const [firstPlayerTileImage] = useImage(firstPlayerTileImg)

const fichaImages = {
  0: blueImage,
  1: yellowImage,
  2: orangeImage,
  3: blackImage,
  4: redImage,
}

const gameState = ref(null)

const isNeuralVisionAvailable = computed(() => {
    if (!gameState.value || !gameState.value.jugadores) return false
    // Check if any player has type 'azul_deep_mcts'
    // Note: The backend logic checks isinstance(ai, (AzulZeroMCTS, AIAzulDeepMCTS))
    // The player.type field comes from the database/creation logic.
    // For AIAzulDeepMCTS, the registered key is "azul_deep_mcts".
    return Object.values(gameState.value.jugadores).some(p => p.type === 'azul_deep_mcts')
})

// Neural Vision refs and logic
const neuralVisionEnabled = ref(false)
const showNeuralVision = ref(false)
const visualizationData = ref(null)
const lastVisualizedTurn = ref(null)
const aiThinking = ref(false)

function isAiTurn() {
    if (!gameState.value) return false
    const currentName = gameState.value.turno_actual
    const player = gameState.value.jugadores[currentName]
    // Assuming backend sends 'type="ai"' in player info. 
    // The player object in 'jugadores' keys is by ID or Name?
    // Based on 'ensurePlayerNames', gameState.jugadores is a Dict[ID, Player]
    // and gameState.turno_actual is Name (or ID converted to name).
    // Let's find the player object by name
    const p = Object.values(gameState.value.jugadores).find(j => j.name === currentName || j.id === currentName)
    return p && (p.type === 'ai' || p.type === 'azul_deep_mcts')
}

watch(() => gameState.value?.turno_actual, async (newTurn) => {
    if (newTurn) {
        if (isAiTurn() && !gameState.value.terminado) {
            if (neuralVisionEnabled.value) {
                // Check if we already visualized this specific turn instance
                if (lastVisualizedTurn.value !== newTurn) {
                    startNeuralVision()
                }
            } else {
                // Auto-trigger AI if visualization is disabled
                // Add a small delay for better UX
                aiThinking.value = true
                setTimeout(() => {
                    handleContinue()
                }, 1000)
            }
        } else {
            // If it's a human turn (or other), reset the tracker
            aiThinking.value = false
            lastVisualizedTurn.value = null
        }
    }
})

watch(() => gameState.value?.terminado, (isTerminated) => {
    if (isTerminated) {
        showNeuralVision.value = false
    }
})

async function startNeuralVision() {
    showNeuralVision.value = true
    visualizationData.value = null
    try {
        const res = await fetch(`${API_BASE}/azul/${gameId}/visualize_ai`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        })
        if (res.ok) {
            visualizationData.value = await res.json()
            lastVisualizedTurn.value = gameState.value.turno_actual
        } else {
             console.error("Failed to visualize", res.status)
             // If not supported (e.g. Heuristic player), just auto continue?
             // Or show error in modal.
             const err = await res.json()
             visualizationData.value = { 
                network_choice: { value_pred: 0, action_idx: -1 },
                saliency: { spatial: [], factories: [], global: [] },
                error: err.detail || "Visualization failed" 
             }
        }
    } catch(e) {
        console.error(e)
    }
}

async function handleContinue() {
    showNeuralVision.value = false
    try {
        await fetch(`${API_BASE}/azul/${gameId}/trigger_ai`, { 
            method: 'POST', 
            headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        })
    } catch(e) {
        console.error("Error triggering AI", e)
    } finally {
        aiThinking.value = false
    }
}

watch(() => gameState.value?.log?.length, () => {
  nextTick(() => {
    if (logContainer.value) {
      logContainer.value.scrollTop = logContainer.value.scrollHeight
    }
  })
})

const selectedFactory = ref(null)
const selectedColor = ref(null)
const selectedRow = ref(null)

const animatedPieces = ref([])

function isPlayerTurn() {
  // console.log('isPlayerTurn check. Me:', me, 'Turno:', gameState.value?.turno_actual)
  return gameState.value?.turno_actual === me || gameState.value?.jugadores?.[gameState.value?.turno_actual]?.id === me
}

function isSelectable(factoryIndex, color) {
  return isPlayerTurn() && color != null
}

function handleFactoryClick(factoryIndex, color) {
  if (!isSelectable(factoryIndex, color)) return
  selectedFactory.value = factoryIndex
  selectedColor.value = color
  selectedRow.value = null // deselecciona fila si se eligen nuevos cristales
}

function handleCenterClick(color) {
  if (!isPlayerTurn()) return
  selectedFactory.value = 'centro'
  selectedColor.value = color
  selectedRow.value = null // deselecciona fila si se eligen nuevos cristales
}

function isLastMoveTile(player, row, index, isFloor) {
  const lm = gameState.value?.last_move
  if (!lm) return false
  
  // Check player. 
  // lm.player_id is the key in players dict or the name?
  // In `aplicar_movimiento`: state.last_move = { "player_id": jugador_id ... }
  // player_id is the id used in state.jugadores dict.
  // In v-for: (jugador, id) in gameState.jugadores
  // So we can pass 'id' from v-for, or check if player.name matches (if IDs are names).
  // The backend uses string IDs mainly.
  // Let's assume we need to check against the player's ID or Name.
  // Let's check both to be safe: 
  // But wait, the v-for yields `jugador` object. We don't have the `key` (id) easily unless passed.
  // The v-for is `(jugador, jIndex) in Object.values(gameState.jugadores)`. 
  // Wait, line 73: `v-for="(jugador, jIndex) in Object.values(gameState.jugadores)"`
  // Here we lose the ID key! 
  // But `jugador.id` should be available inside the object (JugadorAzul model has id field).
  if (lm.player_id !== player.id && lm.player_id !== player.name) return false

  // Check round
  if (lm.round_at_move !== gameState.value.ronda) return false

  if (isFloor) {
     if (lm.added_to_floor <= 0) return false
     // Return true if index is among the last N tiles
     // Total tiles: player.suelo.length
     // Last added: lm.added_to_floor
     // New tiles are from index: length - added
     return index >= (player.suelo.length - lm.added_to_floor)
  } else {
     // Pattern Row
     if (lm.target_row_index !== row) return false
     if (lm.added_to_pattern <= 0) return false
     
     // Pattern is filled from left to right in the array (push).
     // index 0..N
     // New tiles are at the end.
     return index >= (player.patrones[row].length - lm.added_to_pattern)
  }
}



// Nueva lógica para selección de filas de patrones
function getRowFillState(row) {
  if (selectedRow.value === row) return 'rgba(255, 0, 0, 0.3)' // red for selected
  if (isSelectableRow(row)) return 'rgba(0, 255, 0, 0.3)' // green for selectable
  return null;
}

function getRowOpacity(row) {
  if (selectedRow.value === row) return 0.5;
  if (isSelectableRow(row)) return 0.3;
  return 0;
}

// Helper function to get wall column for a color in a row (Azul pattern)
function getWallColumn(row, color) {
  // Row 0: B Y R K O (0 1 2 3 4)
  // Row 1: O B Y R K (4 0 1 2 3)
  // Row 2: K O B Y R (3 4 0 1 2)
  // Row 3: R K O B Y (2 3 4 0 1)
  // Row 4: Y R K O B (1 2 3 4 0)
  return (parseInt(color) + row - 1) % 5
}

function isSelectableRow(row) {
  if (selectedColor.value === null) return false
  
  // Row 0 is the floor - always valid
  if (row === 0) return true
  
  const jugador = Object.values(gameState.value?.jugadores || {}).find(j => j.name === me || j.id === me)
  if (!jugador) {
      console.log('Player not found for me:', me)
      return false
  }
  
  const rowIndex = row - 1 // Convert to 0-based
  const patron = jugador.patrones[rowIndex]
  
  // Check if row is full (count non-null/non-empty items)
  const filledCount = patron ? patron.filter(c => c !== null && c !== '' && c !== -1).length : 0
  if (filledCount >= row) {
      console.log(`Row ${row} full. Filled: ${filledCount}`)
      return false
  }
  
  // Check if row has tiles of a different color
  const colorVal = parseInt(selectedColor.value)
  const existingColor = patron ? patron.find(c => c !== null && c !== '' && c !== -1) : undefined
  if (existingColor !== undefined && existingColor !== colorVal) {
      console.log(`Row ${row} mismatch color. Existing: ${existingColor}, Selected: ${colorVal}`)
      return false
  }
  
  // Check if wall already has this color in this row
  const wallCol = getWallColumn(row, colorVal)
  if (jugador.pared && jugador.pared[rowIndex]) {
      const cell = jugador.pared[rowIndex][wallCol]
      if (cell !== null && cell !== undefined) {
          console.log(`Row ${row} wall occupied at col ${wallCol}. Cell: ${cell}`)
          return false
      }
  }
  
  return true
}

function handleRowClick(row) {
  if (isSelectableRow(row)) {
    selectedRow.value = row;
  }
}

async function confirmMove() {
  confirmingMove.value = true
  try {
    if (selectedRow.value === null || selectedColor.value === null || selectedFactory.value === null) return;

    const color = selectedColor.value
    const origin = selectedFactory.value
    const isCenter = origin === 'centro'
    let origenes = isCenter ? gameState.value.centro : gameState.value.expositores[origin]
    const coords = []

    for (let i = 0; i < origenes.length; i++) {
      if (origenes[i] === color) {
        if (isCenter) {
          coords.push({ x: 100 + (i % 5) * 40, y: 230 + Math.floor(i / 5) * 40 })
        } else {
          const x = origin * 160 + 32 + (i % 2) * 50
          const y = 80 + Math.floor(i / 2) * 50
          coords.push({ x, y })
        }
      }
    }

    const jugadoresArray = Object.values(gameState.value.jugadores)
    const jIndex = jugadoresArray.findIndex(j => j.name === me)
    const offsetX = (jIndex % 2) * 360
    const offsetY = Math.floor(jIndex / 2) * 240

    // Calculate target position based on whether it's floor or pattern row
    let targetX, targetY
    if (selectedRow.value === 0) {
      // Floor position
      targetX = 610 + offsetX + 13 + 15
      targetY = 250 + offsetY + 175 + 15
    } else {
      // Pattern row position
      targetX = 623 + offsetX - 29 * selectedRow.value + 29 * 5 + 15
      targetY = 264 + offsetY + (selectedRow.value - 1) * 29 + 15
    }

    animatedPieces.value = coords.map((c) => ({ x: c.x, y: c.y, color }))

    // Elimina piezas visualmente del origen para que no se dupliquen durante la animación
    // Y mueve el resto al centro si es desde una fábrica
    if (isCenter) {
      gameState.value.centro = gameState.value.centro.filter(c => c !== color)
    } else {
      const leftovers = gameState.value.expositores[origin].filter(c => c !== color)
      gameState.value.centro.push(...leftovers)
      gameState.value.expositores[origin] = []
    }

    await nextTick()

    const konvaNode = stageRef.value?.getNode?.()
    if (!konvaNode) {
      console.warn('Konva node no disponible.')
      return
    }
    const layer = konvaNode.getLayers().slice(-1)[0]

    for (let i = 0; i < animatedPieces.value.length; i++) {
      const shape = layer.findOne('#anim-' + i)
      if (shape) {
        shape.to({ x: targetX, y: targetY, duration: 0.5 })
      }
    }

    await new Promise(resolve => setTimeout(resolve, 600))

    // Añadir fichas al patrón y sobrantes al suelo (visualización local)
    const jugador = Object.values(gameState.value.jugadores).find(j => j.name === me)
    if (jugador && selectedRow.value > 0) {
      // Only update pattern lines if not going to floor
      const filaActual = jugador.patrones[selectedRow.value - 1]
      // Fix: patterns are dynamic arrays matching backend state, not fixed arrays with nulls.
      // Calculate capacity based on row number (1-based)
      const capacity = selectedRow.value
      // Available slots is capacity minus current filled slots (length of dynamic array)
      const huecosDisponibles = capacity - filaActual.length
      
      const fichasAColocar = Math.max(0, Math.min(huecosDisponibles, coords.length))

      // Append new tiles to the dynamic array
      for (let i = 0; i < fichasAColocar; i++) {
        filaActual.push(color)
      }

      const sobrantes = coords.length - fichasAColocar
      for (let i = 0; i < sobrantes; i++) {
        jugador.suelo.push(color)
      }
    } else if (jugador && selectedRow.value === 0) {
      // All tiles go to floor
      for (let i = 0; i < coords.length; i++) {
        jugador.suelo.push(color)
      }
    }


    // Limpiar animación antes de llamar al backend para evitar duplicados mientras la IA piensa
    animatedPieces.value = []

    // Confirmar movimiento en el backend
    // Si Neural Vision está activo, pausamos la IA (trigger_ai=false)
    // FIX: Always pause AI trigger here so we get the state update first.
    // The watcher on turno_actual will trigger the AI.
    const shouldTriggerAi = false 
    const res = await fetch(`${API_BASE}/azul/${gameId}/move?trigger_ai=${shouldTriggerAi}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify({
        factory: selectedFactory.value,
        color: selectedColor.value,
        row: selectedRow.value
      })
    })
    if (!res.ok) {
      console.error('Error al confirmar movimiento en backend:', res.status)
    }
    else {
    const data = await res.json()
    if (data.ok && data.state) {
      const updatedState = data.state
      ensurePlayerNames(updatedState)
      console.log('DEBUG: Updating gameState. Terminado?', updatedState.terminado)
      gameState.value = updatedState
      console.log('DEBUG: gameState updated. Current value:', gameState.value)
      console.log('Movimiento confirmado y estado actualizado:', updatedState)
    } else {
       // Fallback or error handling if needed
       console.error('Respuesta de movimiento inesperada:', data)
    }
    }

  } finally {
    animatedPieces.value = []
    selectedFactory.value = null
    selectedColor.value = null
    selectedRow.value = null
    confirmingMove.value = false
  }
}

function cancelMove() {
  selectedFactory.value = null
  selectedColor.value = null
  selectedRow.value = null
}

function goHome() {
  router.push('/games')
}
function getColorImg(color) {
  return fichaImages[color]?.value || null
}
function getColor(color) {
  return {
    0: 'blue',
    1: 'yellow',
    2: 'orange',
    3: 'black',
    4: 'red',
  }[color] || 'gray'
}
function isSelected(factoryIndex, color) {
  return selectedFactory.value === factoryIndex && selectedColor.value === color
}

import { API_BASE } from '../../config'


const route = useRoute()
const router = useRouter()
const gameId = parseInt(route.params.id)


const loaded = ref(false)
const error = ref(null)

async function fetchState() {
const res = await fetch(`${API_BASE}/azul/${gameId}`, {
  headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
});
if (!res.ok) {
  throw new Error(`HTTP ${res.status}`);
}
const data = await res.json();
  return data;
}


let socket

const token = localStorage.getItem('token')  // tu JWT
const payload = JSON.parse(atob(token.split('.')[1]))
const me = payload.sub   // asume que tu sub es el user.id

function ensurePlayerNames(state) {
  if (state && state.jugadores && typeof state.jugadores === 'object') {
    for (const [id, jugador] of Object.entries(state.jugadores)) {
      if (!('name' in jugador)) {
        jugador.name = null;
      }
      if (state.turno_actual === id) {
        state.turno_actual = jugador.name ?? id;
      }
    }
  }
}


onMounted(async () => {
  socket = new WebSocket(`ws://${window.location.hostname}:8000/ws/azul/${gameId}`)



  socket.onmessage = (event) => {
    const data = JSON.parse(event.data)
    if (data.type === 'update' && data.state) {
      let newState = data.state
      if (typeof newState === 'string') {
        try {
          newState = JSON.parse(newState)
        } catch (e) {
          console.error('Error parsing state from WS:', e)
          return
        }
      }
      ensurePlayerNames(newState)
      gameState.value = newState
    }
  }

  socket.onerror = (e) => {
    console.error('WebSocket error:', e)
  }

  // 2) Carga el estado inicial y comprueba rol
  try {
    const data = await fetchState()
    ensurePlayerNames(data)
    gameState.value = data
    loaded.value = true
  } catch (err) {
    console.error('Error cargando partida:', err)
    error.value = err.message
  }
})

onBeforeUnmount(() => {
if (socket) socket.close()
})
</script>

<style scoped>
/* Main Container */
.azul-game-container {
  padding: 1rem;
  max-width: 1400px;
  margin: 0 auto;
}

/* Header Section */
.header-section {
  display: flex;
  flex-direction: column;
}

.header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.small-btn {
  padding: 0.4rem 0.8rem;
  font-size: 0.9rem;
}

.user-status {
  display: flex;
  gap: 2rem;
}

.label {
  color: var(--text-secondary);
  margin-right: 0.5rem;
}

.highlight {
  color: var(--accent);
  font-weight: 600;
}

/* Players Panel */
.players-panel {
  padding: 1rem;
}

.players-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.player-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-sm);
  padding: 1rem;
  transition: all 0.2s ease;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.player-card.active {
  background: rgba(59, 130, 246, 0.1); /* Primary 10% opacity */
  border-color: var(--primary);
  box-shadow: 0 0 15px rgba(59, 130, 246, 0.2);
}

.player-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.player-name {
  font-weight: 600;
  font-size: 1.1rem;
}

.me-badge {
  background: var(--accent);
  color: black;
  font-size: 0.7rem;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 700;
}

.player-score {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-primary);
}

.turn-indicator {
  color: #fbbf24; /* Amber 400 */
  font-size: 0.9rem;
  font-weight: 600;
  margin-top: auto;
}

/* Action Bar */
.actions-bar {
  position: fixed;
  bottom: 2rem;
  left: 50%;
  transform: translateX(-50%);
  z-index: 100;
}

.action-panel {
  display: flex;
  align-items: center;
  gap: 2rem;
  padding: 1rem 2rem;
  border: 1px solid var(--border-glow);
  box-shadow: 0 10px 40px rgba(0,0,0,0.5);
}

.action-text {
  font-size: 1.2rem;
  font-weight: 600;
}

.action-buttons {
  display: flex;
  gap: 1rem;
}

.btn-secondary {
  background: transparent;
  border: 1px solid var(--text-secondary);
  color: var(--text-secondary);
  padding: 0.75rem 1.5rem;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.2s;
}

.btn-secondary:hover {
  background: rgba(255,255,255,0.1);
  color: white;
  border-color: white;
}

/* Game Log & Debug */
.game-log {
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-sm);
  padding: 1rem;
  max-height: 200px;
  overflow-y: auto;
  margin-top: 2rem;
  color: var(--text-secondary);
}

.game-log li {
  padding: 4px 0;
  border-bottom: 1px solid rgba(255,255,255,0.05);
}

.ai-spinner {
  display: inline-block;
  font-size: 1.2rem;
  animation: spin 2s linear infinite;
  margin-left: auto;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.debug-section {
  color: var(--text-secondary);
  margin-top: 2rem;
  padding-top: 1rem;
  border-top: 1px solid var(--border-light);
}

/* Misc */
.error-msg {
  color: #ef4444;
  background: rgba(239, 68, 68, 0.1);
  padding: 1rem;
  border-radius: var(--radius-sm);
  text-align: center;
  margin: 1rem 0;
}
</style>
