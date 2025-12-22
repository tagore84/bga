<template>
  <div class="games-container p-4">
    <div class="header-section text-center mb-2">
      <h2>Available Games</h2>
      <p style="color: var(--text-secondary)">Select a game to start playing</p>
    </div>
    
    <div class="games-grid">
      <div v-for="game in games" :key="game.key" class="game-card glass-panel">
        <div class="card-content">
          <div class="game-icon">
            {{ getGameIcon(game.name) }}
          </div>
          <h3 class="game-title">{{ formatGameName(game.name) }}</h3>
          <button @click="selectGame(game)" class="btn-primary w-full">Play Now</button>
        </div>
        
        <button 
          @click="deleteGame(game.id)" 
          class="btn-danger delete-btn" 
          v-if="game.name.startsWith('test_')"
          title="Delete Test Game"
        >
          🗑️
        </button>
      </div>
    </div>
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

function getGameIcon(name) {
  if (name === 'tictactoe') return '⭕❌'
  if (name === 'azul') return '💠'
  return '🎮'
}

function formatGameName(name) {
  return name.charAt(0).toUpperCase() + name.slice(1)
}

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
  if (!confirm('Are you sure you want to delete this test game?')) {
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
    alert(`Error deleting game: ${e.message}`)
  }
}
</script>

<style scoped>
.games-container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 2rem;
}

.games-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 1.5rem;
}

.game-card {
  position: relative;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  display: flex;
  flex-direction: column;
  align-items: center;
  overflow: hidden;
}

.game-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 12px 40px 0 rgba(0, 0, 0, 0.4);
  border-color: var(--primary-glow);
}

.card-content {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 1rem;
}

.game-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.game-title {
  margin-bottom: 1.5rem;
  font-size: 1.5rem;
  text-transform: capitalize;
}

.delete-btn {
  position: absolute;
  top: 10px;
  right: 10px;
  padding: 5px;
  font-size: 0.8rem;
  opacity: 0.7;
}

.delete-btn:hover {
  opacity: 1;
}
</style>