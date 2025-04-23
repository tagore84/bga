<template>
  <div class='games-list'>
    <h2>Partidas activas</h2>

    <!-- Volver a selección de juegos -->
    <button @click='goToSelection' class='new-game-btn'>
      Nueva partida
    </button>

    <ul>
      <li v-for='game in games' :key='game.id' class='game-item'>
        <strong>[{{ game.game_name }}] ID {{ game.id }}</strong> – Creada: {{ new Date(game.created_at).toLocaleString() }}
        <button @click='joinGame(game.id)' class='join-btn'>Unirse</button>
        <button @click='deleteGame(game.id)' class='delete-btn'>Borrar</button>
      </li>
    </ul>

    <p v-if='error' class='error'>{{ error }}</p>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const games = ref([])
const error = ref(null)
const API_BASE = window.location.hostname === 'localhost'
  ? 'http://localhost:8000'
  : 'http://backend:8000'

async function loadGames() {
  error.value = null
  try {
    const token = localStorage.getItem('token')
    const res = await fetch(`${API_BASE}/tictactoe/`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    games.value = await res.json()
  } catch (e) {
    console.error('Error cargando partidas:', e)
    error.value = 'No se pudo obtener las partidas activas'
  }
}

function joinGame(id) {
  router.push(`/games/${id}`)
}

async function deleteGame(id) {
  if (!confirm(`¿Eliminar partida #${id}?`)) return
  try {
    const token = localStorage.getItem('token')
    const res = await fetch(`${API_BASE}/tictactoe/${id}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (res.status === 404) throw new Error('No encontrada')
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    games.value = games.value.filter(g => g.id !== id)
  } catch (e) {
    console.error('Error borrando partida:', e)
    alert('Error al borrar: ' + e.message)
  }
}

function goToSelection() {
  router.push('/')
}

onMounted(loadGames)
</script>

<style scoped>
.games-list {
  max-width: 600px;
  margin: 2rem auto;
  text-align: left;
}
.new-game-btn {
  margin-bottom: 1rem;
  padding: 0.5em 1em;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
.new-game-btn:hover {
  background: #0056b3;
}
ul {
  list-style: none;
  padding: 0;
}
.game-item {
  margin-bottom: 0.8rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.join-btn, .delete-btn {
  margin-left: 0.5rem;
  padding: 0.3em 0.6em;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
.join-btn {
  background: #28a745;
  color: white;
}
.join-btn:hover {
  background: #218838;
}
.delete-btn {
  background: #dc3545;
  color: white;
}
.delete-btn:hover {
  background: #c82333;
}
.error {
  color: red;
  margin-top: 1rem;
}
</style>
