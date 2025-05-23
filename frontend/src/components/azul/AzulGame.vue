<template>
  <div class="azul-game">
      <h2>Partida Azul #{{ gameId }}</h2>
      <div v-if="!loaded">Cargando...</div>
      <div v-else-if="error">Error: {{ error }}</div>
      <div v-else-if="gameState">
        <div v-if="gameState.jugadores">
          <div v-for="(jugador, id) in gameState.jugadores" :key="id" class="jugador">
            <h3>{{ jugador.name || ('Jugador ' + id) }} - {{ jugador.puntos }} puntos</h3>
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
        <div class="centro" v-if="gameState.centro">
          <h3>Centro</h3>
          <div class="centro-fichas">
            <div
              v-for="(ficha, i) in gameState.centro"
              :key="'centro-' + i"
              class="ficha"
            >
              <img :src="fichaImages[ficha]" alt="ficha" class="ficha-img" />
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
                    :x="623 - 29*row + 29*5"
                    :y="264 + jIndex * 240 + (row-1) * 29"
                    :width="29*row - 2"
                    :height="27"
                    :fill="getRowFillState(row)"
                    :opacity="getRowOpacity(row)"
                    :stroke="selectedRow === row ? 'red' : isSelectableRow(row) ? 'gray' : 'black'"
                    :strokeWidth="selectedRow === row ? 3 : isSelectableRow(row) ? 2 : 1"
                    :onclick="() => handleRowClick(row)"
                  />
                </template>
              </template>
              <template v-for="(fila, y) in jugador.patrones" :key="'patron-fila-' + y + '-j' + jIndex">
                <v-rect
                  v-for="(casilla, i) in fila"
                  :key="'patron-casilla-' + y + '-' + i + '-j' + jIndex"
                  :x="610 - i * 30"
                  :y="250 + jIndex * 240 + y * 30"
                  :width="28"
                  :height="28"
                  :fill="getColor(casilla)"
                  stroke="black"
                />
              </template>
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

            <template v-for="(color, i) in gameState?.centro || []" :key="'centro-' + i">
              <v-circle
                :x="100 + i * 35"
                :y="300"
                :radius="15"
                :fill="getColor(color)"
                :onclick="() => handleCenterClick(color)"
                :opacity="isSelectable('centro', color) ? 1 : 0.4"
                :stroke="isSelected(index, color) ? 'black' : null"
                :strokeWidth="isSelected(index, color) ? 3 : 0"
              />
            </template>
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
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
const stageRef = ref(null)
const confirmingMove = ref(false)
import { useRoute, useRouter } from 'vue-router'
import boardImg from '@/assets/azul/board.png'
import factoryImg from '@/assets/azul/factory_0.png'
import blueImg from '@/assets/azul/blue.png'
import yellowImg from '@/assets/azul/yellow.png'
import redImg from '@/assets/azul/red.png'
import blackImg from '@/assets/azul/black.png'
import orangeImg from '@/assets/azul/orange.png'
import { useImage } from 'vue-konva'

const [boardImage] = useImage(boardImg)
const [factoryImage] = useImage(factoryImg)

const [blueImage] = useImage(blueImg)
const [yellowImage] = useImage(yellowImg)
const [redImage] = useImage(redImg)
const [blackImage] = useImage(blackImg)
const [orangeImage] = useImage(orangeImg)

const fichaImages = {
  blue: blueImage,
  yellow: yellowImage,
  red: redImage,
  black: blackImage,
  orange: orangeImage,
}

const gameState = ref(null)

const selectedFactory = ref(null)
const selectedColor = ref(null)
const selectedRow = ref(null)

const animatedPieces = ref([])

function isPlayerTurn() {
  return gameState.value?.turno_actual === me
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

function isSelectableRow(row) {
  // ejemplo simple: hay algo seleccionado y cabría en esa fila
  const selected = selectedColor.value;
  return selected != null; // extender lógica según reglas reales
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

    const targetX = 623 - 29 * selectedRow.value + 29 * 5 + 15
    const targetY = 264 + 0 * 240 + (selectedRow.value - 1) * 29 + 15

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
    if (jugador) {
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
      const updatedState = await fetchState()
      gameState.value = updatedState
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
function getColorImg(color) {
  const colorImg = {
    blue: blueImage,
    yellow: yellowImage,
    red: redImage,
    black: blackImage,
    orange: orangeImage
  }[color]
  return colorImg.value
}
function getColor(color) {
  return {
    blue: 'blue',
    yellow: 'yellow',
    red: 'red',
    black: 'black',
    orange: 'orange'
  }[color] || 'gray'
}
function isSelected(factoryIndex, color) {
  return selectedFactory.value === factoryIndex && selectedColor.value === color
}

const API_BASE = window.location.hostname === 'localhost'
? 'http://localhost:8000'
: 'http://backend:8000'

const route = useRoute()
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


onMounted(async () => {
  socket = new WebSocket(`ws://${window.location.hostname}:8000/ws/azul/${gameId}`)

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

  socket.onmessage = (event) => {
    const data = JSON.parse(event.data)
    if (data.type === 'update' && data.state) {
      ensurePlayerNames(data.state)
      gameState.value = data.state
    }
  }

  socket.onerror = (e) => {
    console.error('WebSocket error:', e)
  }

  // 2) Carga el estado inicial y comprueba rol
  try {
    const data = await fetchState()
    ensurePlayerNames(data)
    gameState.value = data  // <--- AÑADE ESTA LÍNEA
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
justify-content: flex-end;
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
</style>

.confirm-button[disabled] {
  opacity: 0.5;
  cursor: not-allowed;
}
