<template>
  <div class="active-games">
    <button @click="goBack" class="back-btn">← Volver</button>
    <button @click="createNewGame" class="new-btn">+ Crear partida</button>
    <h2>Partidas Activas</h2>
    <div v-if="loading" class="loading">Cargando partidas...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <ul v-else>
      <li v-for="game in games" :key="game.id" class="game-item">
        <span>Partida #{{ game.id }} - Turno: {{ game.state.turno_actual }}</span>
        <button @click="joinGame(game.id)">Unirse</button>
      </li>
      <li v-if="games.length === 0">No hay partidas en curso.</li>
    </ul>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const games = ref([])
const loading = ref(true)
const error = ref(null)
const API_BASE = window.location.hostname === 'localhost'
  ? 'http://localhost:8000'
  : 'http://backend:8000'

async function fetchActiveGames() {
  try {
    const res = await fetch(`${API_BASE}/azul/`)
    if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`)
    games.value = await res.json()
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

function joinGame(id) {
  router.push(`/azul/${id}`)
}

function goBack() {
  router.back()
}

function createNewGame() {
  router.push('/azulConfig')
}

onMounted(fetchActiveGames)
</script>

<style scoped>
.active-games {
  max-width: 400px;
  margin: 2rem auto;
  text-align: left;
}
.back-btn {
  margin-bottom: 1rem;
  background: transparent;
  border: none;
  color: #007bff;
  cursor: pointer;
  font-size: 1em;
}
.back-btn:hover {
  text-decoration: underline;
}
.game-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0;
  border-bottom: 1px solid #eee;
}
.loading, .error {
  text-align: center;
  margin: 1rem 0;
}
button {
  padding: 0.3em 0.6em;
  border: none;
  background: #007bff;
  color: white;
  border-radius: 4px;
  cursor: pointer;
}
button:hover {
  background: #0056b3;
}
  .new-btn {
    margin-left: 1rem;
  }
</style>
