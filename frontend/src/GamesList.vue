<template>
  <div class="games-list">
    <h2>Selecciona un juego</h2>
    <ul>
      <li v-for="game in games" :key="game.key">
        <button @click="selectGame(game)">{{ game.name }}</button>
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
  } else {
    console.warn(`No config route defined for game ${game.name}`)
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
</style>