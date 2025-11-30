<template>
  <div class="azul-game">
      <div class="header-container">
        <h2>Partida Azul #{{ gameId }}</h2>
        <button @click="goHome" class="back-button">Volver al Inicio</button>
      </div>
      <div class="user-info">
        <p><strong>Usuario:</strong> {{ me }}</p>
        <p><strong>Turno actual:</strong> <span :class="{ 'active-turn': true }">{{ gameState?.turno_actual }}</span></p>
      </div>
      <div v-if="!loaded">Cargando...</div>
      <div v-else-if="error">Error: {{ error }}</div>
      <div v-else-if="gameState">
        <div v-if="gameState.jugadores">
          <div v-for="(jugador, id) in gameState.jugadores" :key="id" class="jugador-info" :class="{ 'is-active': gameState.turno_actual === jugador.name }">
            <h3>
              {{ jugador.name || ('Jugador ' + id) }} 
              <span v-if="jugador.name === me">(TÚ)</span>
              - {{ jugador.puntos }} puntos
              <span v-if="gameState.turno_actual === jugador.name">⭐ TURNO</span>
            </h3>
          </div>
          <template v-if="selectedRow !== null">
            <button @click="confirmMove" :disabled="confirmingMove" class="confirm-button">
              <span v-if="confirmingMove">Confirmando...</span>
              <span v-else>OK</span>
            </button>
          </template>
          <template v-if="selectedColor !== null">
            <button @click="cancelMove">Cancelar</button>
          </template>
        </div>
        <div v-else>
          <p>No hay datos de jugadores.</p>
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
                      :x="(610 + (jIndex % 2) * 360) + 129 - 29 * (y + 1) + 29 * (i + 1 + (y + 1 - fila.length))"
                      :y="(250 + Math.floor(jIndex / 2) * 240) + 14 + y * 29"
                      :width="28"
                      :height="28"
                      :image="getColorImg(casilla)"
                      :onclick="() => handleRowClick(y + 1)"
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
                :x="32 + (i % 2) * 50"
                :y="230 + Math.floor(i / 2) * 50"
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
              :x="50"
              :y="200"
              :width="40"
              :height="40"
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
      <div class="debug-section" style="margin-top: 20px; border-top: 1px solid #ccc; padding-top: 10px;">
        <button @click="debugGame">🔍 Debug Estado</button>
      </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
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
          coords.push({ x: 100 + i * 35, y: 300 })
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
    if (isCenter) {
      gameState.value.centro = gameState.value.centro.filter(c => c !== color)
    } else {
      gameState.value.expositores[origin] = gameState.value.expositores[origin].filter(c => c !== color)
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
      const huecosDisponibles = filaActual.length - filaActual.filter(c => c !== null && c !== '').length
      const fichasAColocar = Math.min(huecosDisponibles, coords.length)
      let colocadas = 0
      for (let i = 0; i < filaActual.length && colocadas < fichasAColocar; i++) {
        if (filaActual[i] === null || filaActual[i] === '') {
          filaActual[i] = color
          colocadas++
        }
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

    // Confirmar movimiento en el backend
    const res = await fetch(`${API_BASE}/azul/${gameId}/move`, {
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
      gameState.value = updatedState
      console.log('Movimiento confirmado y estado actualizado:', updatedState)
    } else {
       // Fallback or error handling if needed
       console.error('Respuesta de movimiento inesperada:', data)
    }
    }

    animatedPieces.value = []

    selectedFactory.value = null
    selectedColor.value = null
    selectedRow.value = null
  } finally {
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

const API_BASE = window.location.hostname === 'localhost'
? 'http://localhost:8000'
: 'http://backend:8000'

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
.loading { font-size: 1.2em; color: #666; }
.error { color: red; margin: 1em; }
.result { font-size: 1.5em; margin-bottom: 1em; }
.back-button { padding: 0.5em 1em; font-size: 1em; margin-top: 0.5em; cursor: pointer; }
.header-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1em;
}
.tic-tac-toe { display: flex; flex-direction: column; align-items: center; margin-top: 2rem; }

.jugador {
margin-bottom: 2em;
}
.fila {
display: grid;
grid-template-columns: repeat(5, 2em);
gap: 0.2em;
}
.casilla {
text-align: center;
border: 1px solid #ccc;
padding: 0.3em;
}
.expositores, .centro {
margin-top: 1rem;
padding: 1rem;
background: #f9f9f9;
border-radius: 8px;
}

.expositor {
margin-bottom: 0.5rem;
}

.tablero-fondo {
width: 100%;
height: auto;
display: block;
}

.grid-pared {
position: absolute;
top: 0;
left: 0;
display: grid;
grid-template-columns: repeat(5, 1fr);
grid-template-rows: repeat(5, 1fr);
width: 100%;
height: 100%;
}

.casilla {
display: flex;
justify-content: center;
align-items: center;
font-weight: bold;
color: white; /* o negro si prefieres */
}

.grid-patrones {
position: absolute;
top: 17.5%;
left: 8.2%;
width: 14%;
height: 63%;
display: grid;
grid-template-rows: repeat(5, 1fr);
gap: 4.5%; /* espacio entre filas, puede afinarse */
}

.patron-fila {
display: flex;
flex-direction: flex-end;
gap: 3%; /* espacio entre losetas dentro de cada fila */
}
.patron-casilla {
width: 1em;
height: 1em;
background-color: rgba(255, 255, 255, 0.4); /* para depuración */
border-radius: 4px;
}
.expositor-contenedor {
position: relative;
width: 150px; /* ajusta según tu imagen */
height: 150px;
margin: 1em auto;
}

.expositor-fondo {
width: 100%;
height: 100%;
display: block;
}

.expositor-fichas {
position: absolute;
top: 0;
left: 0;
display: flex;
flex-wrap: wrap;
justify-content: center;
align-items: center;
width: 100%;
height: 100%;
padding: 0.5em;
gap: 0.5em;
}

.ficha {
width: 2em;
height: 2em;
background-color: white;
border-radius: 50%;
display: flex;
justify-content: center;
align-items: center;
font-weight: bold;
}

.ficha-img {
width: 100%;
height: 100%;
object-fit: contain;
}

.fabrica-lista {
display: flex;
flex-wrap: wrap;
justify-content: center;
gap: 1em;
margin: 2em 0;
}

.centro-fichas {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 0.5em;
  margin-top: 1em;
}

.user-info {
  background: #eef;
  padding: 10px;
  border-radius: 5px;
  margin-bottom: 10px;
}

.active-turn {
  color: #d32f2f;
  font-weight: bold;
}

.jugador-info {
  padding: 5px;
  border-radius: 4px;
}

.jugador-info.is-active {
  background-color: #fff3e0;
  border: 1px solid #ff9800;
}

.game-log {
  margin-top: 20px;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 5px;
  max-height: 200px;
  overflow-y: auto;
  background: #fff;
}
.game-log ul {
  list-style-type: none;
  padding: 0;
  margin: 0;
}
.game-log li {
  padding: 5px 0;
  border-bottom: 1px solid #eee;
}

.confirm-button[disabled] {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
