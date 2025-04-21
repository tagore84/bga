<template>
  <div class="tic-tac-toe">
    <div v-if="error" class="error">{{ error }}</div>
    <div v-else-if="!loaded" class="loading">Cargando partida…</div>
    <div v-else>
      <div v-if="status !== 'in_progress'" class="result">
        <p v-if="status === 'draw'">¡Empate!</p>
        <p v-else>¡{{ status === 'X_won' ? 'X' : 'O' }} ha ganado!</p>
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
              width=100
              height=100
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
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'

const API_BASE = window.location.hostname === 'localhost'
  ? 'http://localhost:8000'
  : 'http://backend:8000'

const route = useRoute()
const gameId = parseInt(route.params.id)

const board = ref(Array(9).fill(null))
const currentTurn = ref(null)
const status = ref('in_progress')
const loaded = ref(false)
const error = ref(null)

async function fetchState() {
  try {
    const res = await fetch(`${API_BASE}/tictactoe/${gameId}`)
    if (!res.ok) throw new Error(`HTTP ${res.status} - ${await res.text()}`)
    const data = await res.json()
    board.value = data.board
    currentTurn.value = data.current_turn
    status.value = data.status
    loaded.value = true
  } catch (e) {
    error.value = e.message
  }
}

async function onClick(pos) {
  if (board.value[pos] || status.value !== 'in_progress') return
  try {
    const moveRes = await fetch(
      `${API_BASE}/tictactoe/${gameId}/move`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
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

onMounted(fetchState)
</script>

<style scoped>
.loading { font-size: 1.2em; color: #666; }
.error { color: red; margin: 1em; }
.result { font-size: 1.5em; margin-bottom: 1em; }
.tic-tac-toe { display: flex; flex-direction: column; align-items: center; margin-top: 2rem; }
</style>
