<template>
  <div class="games-list">
    <h2>Selecciona un juego</h2>
    <ul>
      <li v-for="game in games" :key="game.key" class="game-item">
        <button @click="selectGame(game)" class="select-btn">{{ game.name }}</button>
        <button @click="deleteGame(game.id)" class="delete-btn" v-if="game.name.startsWith('test_')">🗑️</button>
      </li>
    </ul>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'


const games = ref([])
const router = useRouter()

const API_BASE = window.location.hostname === 'localhost' 
    ? 'http://localhost:8000' 
    : 'http://backend:8000'

async function fetchGames() {
  try {
    const response = await fetch(`${API_BASE}/games`)
    if (!response.ok) {
      throw new Error('Error fetching games')
    }
    const data = await response.json()
    // Support APIs that return either an array directly or an object with a `games` property
    games.value = data.games ?? data
  } catch (error) {
    console.error('Failed to fetch games:', error)
  }
}

// Fetch games when the component is mounted
onMounted(() => {
  fetchGames()
})

function selectGame(game) {
  if (game.name === 'tictactoe') {
    router.push('/tictactoeActive')
  } else if (game.name === 'azul') {
    router.push('/azulActive')
  } else {
    console.warn(`No config route defined for game ${game.name}`)
  }
}

async function deleteGame(gameId) {
  if (!confirm('¿Estás seguro de que quieres eliminar este juego de prueba?')) {
    return
  }
  
  try {
    const res = await fetch(`${API_BASE}/games/${gameId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    })
    
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`)
    }
    
    // Refresh the list
    await fetchGames()
  } catch (e) {
    alert(`Error al eliminar el juego: ${e.message}`)
  }
}


</script>

<style scoped>
.active-games-btn {
  margin-bottom: 1rem;
  padding: 0.5em 1em;
  background: #28a745;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
.active-games-btn:hover {
  background: #218838;
}

.game-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.select-btn {
  flex: 1;
  padding: 10px;
  font-size: 16px;
}

.delete-btn {
  background: #dc3545;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 8px 12px;
  cursor: pointer;
  font-size: 16px;
}

.delete-btn:hover {
  background: #c82333;
}
</style>