<template>
  <div class="tic-tac-toe">
    <div v-if="error" class="error">{{ error }}</div>
    <div v-else-if="!loaded" class="loading">Cargando partida…</div>
    <div v-else>
      <div v-if="status !== 'in_progress'" class="result">
        <p v-if="status === 'draw'">¡Empate!</p>
        <p v-else>¡{{ status === 'X_won' ? 'X' : 'O' }} ha ganado!</p>
        <button @click="goBack" class="back-button">Volver a selección de juegos</button>
      </div>
      <v-stage :config="{ width: 300, height: 300 }">
        <v-layer>
          <!-- Líneas del tablero -->
          <v-line :points="[100,0,100,300]" stroke="#000" />
          <v-line :points="[200,0,200,300]" stroke="#000" />
          <v-line :points="[0,100,300,100]" stroke="#000" />
          <v-line :points="[0,200,300,200]" stroke="#000" />

          <!-- Fichas X/O -->
          <template v-for="(cell, idx) in board" :key="idx">
            <v-text
              v-if="cell"
              :text="cell"
              :x="(idx % 3) * 100 + 35"
              :y="Math.floor(idx / 3) * 100 + 30"
              fontSize="50"
            />
          </template>

          <!-- Áreas clicables -->
          <template v-for="idx in 9" :key="idx">
            <v-rect
              :x="((idx - 1) % 3) * 100"
              :y="Math.floor((idx - 1) / 3) * 100"
              width="100"
              height="100"
              fill="transparent"
              @click="onClick(idx - 1)"
            />
          </template>
        </v-layer>
      </v-stage>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'


const API_BASE = window.location.hostname === 'localhost'
  ? 'http://localhost:8000'
  : 'http://backend:8000'

const route = useRoute()
const router = useRouter()
const gameId = parseInt(route.params.id)

const board = ref(Array(9).fill(null))
const currentTurn = ref(null)
const status = ref('in_progress')
const loaded = ref(false)
const error = ref(null)
const player_o = ref(null)
const player_x = ref(null)
const config = ref(null)

async function fetchState() {
  const res = await fetch(`${API_BASE}/tictactoe/${gameId}`, {
    headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
  });
  if (!res.ok) {
    throw new Error(`HTTP ${res.status}`);
  }
  const data = await res.json();
  // Actualiza tus reactive state
  board.value = data.board;
  currentTurn.value = data.current_turn;
  status.value = data.status;
  // si quieres guardar el config completo:
  config.value = data.config;
  player_x.value = data.player_x;
  player_o.value = data.player_o;
  return data;
}

async function onClick(pos) {
  // sólo me dejo clicar si mi turno Y soy ese jugador
  if (
    board.value[pos] ||
    status.value !== 'in_progress' ||
    (currentTurn.value === 'X' && !isPlayerX.value) ||
    (currentTurn.value === 'O' && !isPlayerO.value)
  ) return
  if (board.value[pos] || status.value !== 'in_progress') return
  try {
    const moveRes = await fetch(
      `${API_BASE}/tictactoe/${gameId}/move`,
      {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ position: pos })
      }
    )
    if (!moveRes.ok) {
      const text = await moveRes.text()
      throw new Error(text || `HTTP ${moveRes.status}`)
    }
    await fetchState()
    
  } catch (e) {
    error.value = e.message
  }
}

function goBack() {
  router.push('/games')
}

let socket

const token = localStorage.getItem('token')  // tu JWT
const payload = JSON.parse(atob(token.split('.')[1]))
const meId = payload.sub   // asume que tu sub es el user.id

const isPlayerX = ref(false)
const isPlayerO = ref(false)

const meUsername = JSON.parse(atob(localStorage
  .getItem('token')
  .split('.')[1]))
  .sub; // esto es tu username

onMounted(async () => {
  // 1) Conecta WebSocket…
  socket = new WebSocket(
    `ws://${window.location.hostname}:8000/ws/tictactoe/${gameId}`
  );
  socket.onmessage = ({ data }) => {
    try {
      const msg = JSON.parse(data)
      // 1) Si viene el tablero, actualízalo
      if (msg.board) {
        board.value = JSON.parse(msg.board)
      }
      // 2) Estado y turno
      if (msg.status) {
        status.value = msg.status
      }
      if (msg.by) {
        currentTurn.value = msg.by
      }
    } catch (e) {
      console.error('Error parseando WS:', e, data)
    }
  }

  // 2) Carga el estado inicial y comprueba rol
  try {
    const data = await fetchState();
    // Si tu config usa playerXName:
    isPlayerX.value = (player_x.value === meUsername);
    isPlayerO.value = (player_o.value === meUsername);
    loaded.value = true
  } catch (err) {
    console.error('Error cargando partida:', err);
    error.value = err.message;
  }
});

 onBeforeUnmount(() => {
   socket && socket.close()
 })
</script>

<style scoped>
.loading { font-size: 1.2em; color: #666; }
.error { color: red; margin: 1em; }
.result { font-size: 1.5em; margin-bottom: 1em; }
.back-button { padding: 0.5em 1em; font-size: 1em; margin-top: 0.5em; cursor: pointer; }
.tic-tac-toe { display: flex; flex-direction: column; align-items: center; margin-top: 2rem; }
</style>
