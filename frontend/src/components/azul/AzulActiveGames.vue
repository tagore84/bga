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
        <div class="button-group">
          <button @click="joinGame(game.id)" class="join-btn">Unirse</button>
          <button @click="deleteGame(game.id)" class="delete-btn">🗑️ Eliminar</button>
        </div>
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

async function deleteGame(id) {
  if (!confirm(`¿Estás seguro de que quieres eliminar la partida #${id}?`)) {
    return
  }
  
  try {
    const res = await fetch(`${API_BASE}/azul/${id}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    })
    
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}: ${await res.text()}`)
    }
    
    // Refresh the list after deletion
    await fetchActiveGames()
  } catch (e) {
    alert(`Error al eliminar la partida: ${e.message}`)
  }
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
.button-group {
  display: flex;
  gap: 0.5rem;
}
.delete-btn {
  background: #dc3545;
}
.delete-btn:hover {
  background: #c82333;
}
.join-btn {
  background: #28a745;
}
.join-btn:hover {
  background: #218838;
}

</style>
