<template>
  <div class="glass-panel config-container">
    <h2 class="text-center mb-1">Create Azul Game</h2>
    <p class="text-center mb-2" style="color: var(--text-secondary)">Select players for the match</p>

    <div v-if="error" class="error text-center mb-1">{{ error }}</div>
    
    <div class="board-layout">
      <!-- Top (Player 1) -->
      <div class="player-slot top">
        <label>Player 1</label>
         <div class="type-toggle">
            <button @click="playerTypes[0] = 'human'" :class="{ active: playerTypes[0] === 'human' }">Humano</button>
            <button @click="playerTypes[0] = 'ai'" :class="{ active: playerTypes[0] === 'ai' }">IA</button>
        </div>
        <select v-model="selectedPlayers[0]" class="glass-select">
          <option :value="null">Empty</option>
          <option v-for="player in getAvailablePlayers(0)" :key="player.id" :value="player.id">{{ player.displayName }}</option>
        </select>
      </div>

      <!-- Left (Player 2) -->
      <div class="player-slot left">
        <label>Player 2</label>
        <div class="type-toggle">
            <button @click="playerTypes[1] = 'human'" :class="{ active: playerTypes[1] === 'human' }">Humano</button>
            <button @click="playerTypes[1] = 'ai'" :class="{ active: playerTypes[1] === 'ai' }">IA</button>
        </div>
        <select v-model="selectedPlayers[1]" class="glass-select">
          <option :value="null">Empty</option>
          <option v-for="player in getAvailablePlayers(1)" :key="player.id" :value="player.id">{{ player.displayName }}</option>
        </select>
      </div>

      <!-- Center (Visual) -->
      <div class="center-visual">
        <div class="table-visual"></div>
      </div>

      <!-- Right (Player 4) -->
      <div class="player-slot right">
        <label>Player 4</label>
        <div class="type-toggle">
            <button @click="playerTypes[3] = 'human'" :class="{ active: playerTypes[3] === 'human' }">Humano</button>
            <button @click="playerTypes[3] = 'ai'" :class="{ active: playerTypes[3] === 'ai' }">IA</button>
        </div>
        <select v-model="selectedPlayers[3]" class="glass-select">
          <option :value="null">Empty</option>
          <option v-for="player in getAvailablePlayers(3)" :key="player.id" :value="player.id">{{ player.displayName }}</option>
        </select>
      </div>

      <!-- Bottom (Player 3) -->
      <div class="player-slot bottom">
        <label>Player 3</label>
        <div class="type-toggle">
            <button @click="playerTypes[2] = 'human'" :class="{ active: playerTypes[2] === 'human' }">Humano</button>
            <button @click="playerTypes[2] = 'ai'" :class="{ active: playerTypes[2] === 'ai' }">IA</button>
        </div>
        <select v-model="selectedPlayers[2]" class="glass-select">
          <option :value="null">Empty</option>
          <option v-for="player in getAvailablePlayers(2)" :key="player.id" :value="player.id">{{ player.displayName }}</option>
        </select>
      </div>
    </div>

    <div class="actions mt-2">
      <button @click="goBack" class="btn-secondary">Back</button>
      <button @click="createGame" class="btn-primary">Start Game</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { API_BASE } from '../../config'

const router = useRouter()
const players = ref([])
const error = ref(null)
const selectedPlayers = ref([null, null, null, null])
const playerTypes = ref(['human', 'human', 'human', 'human'])

const humans = ref([])
const ais = ref([])

function getAvailablePlayers(index) {
    return playerTypes.value[index] === 'human' ? humans.value : ais.value;
}

onMounted(async () => {
  try {
    const token = localStorage.getItem('token')
    
    // 1. Fetch available games to find "azul" ID
    const resGames = await fetch(`${API_BASE}/games`)
    if (!resGames.ok) throw new Error('Error al cargar juegos')
    const gamesData = await resGames.json()
    const allGames = gamesData.games ?? gamesData
    const azulGame = allGames.find(g => g.name === 'azul')

    // 2. Fetch players
    const resPlayers = await fetch(`${API_BASE}/players/`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    if (!resPlayers.ok) throw new Error('Could not load players')
    const rawPlayers = await resPlayers.json()
    
    // Get current user
    let currentUserName = null
    try {
      const resMe = await fetch(`${API_BASE}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      if (resMe.ok) {
        const dataMe = await resMe.json()
        currentUserName = dataMe.name
      }
    } catch (e) {
      console.error("Error fetching current user", e)
    }

    const allowedAI = {
      'Azul Fácil (IA)': 'Fácil',
      'Azul Medio (IA)': 'Medio',
      'Azul Difícil (IA)': 'Difícil',
      'Experimental (IA)': 'Experimental'
    }

    const processedPlayers = rawPlayers
      .filter(p => p.game_id === (azulGame ? azulGame.id : 2) || p.game_id === null)
      .filter(p => p.type !== 'ai' || Object.keys(allowedAI).includes(p.name))
      .map(p => {
        let newName = p.name
        if (p.type === 'ai' && allowedAI[p.name]) {
          newName = allowedAI[p.name]
        }
        
        let displayName = newName
        if (p.type === 'ai') {
          displayName = `${newName} (IA)`
        } else if (currentUserName && p.name === currentUserName) {
          displayName = `${newName} (tú)`
        }

        return { ...p, name: newName, displayName, originalName: p.name }
      })
      .sort((a, b) => {
        const getPriority = (p) => {
          if (currentUserName && p.name === currentUserName) return 0
          if (p.type !== 'ai') return 1
          
          if (p.name === 'Fácil') return 2
          if (p.name === 'Medio') return 3
          if (p.name === 'Difícil') return 4
          if (p.name === 'Experimental') return 5
          return 6
        }
        return getPriority(a) - getPriority(b)
      })
      
      humans.value = processedPlayers.filter(p => p.type === 'human')
      ais.value = processedPlayers.filter(p => p.type === 'ai')

  } catch (e) {
    console.error(e)
    error.value = e.message
  }
})

function goBack() {
  router.push('/games')
}

async function createGame() {
  error.value = null
  const selected = selectedPlayers.value.filter(p => p !== null)
  if (selected.length < 2) {
    error.value = "Select at least 2 players."
    return
  }

  const participantes = selected.map(id => {
    // Look in both lists to find the player
    const jugador = humans.value.find(p => p.id === id) || ais.value.find(p => p.id === id)
    let pType = jugador?.type || 'human'
    
    // Fix: If it's the DeepMCTS player (Experimental), set the specific type
    if (jugador?.name === 'Experimental') {
      pType = 'azul_deep_mcts'
    }

    return {
      id,
      type: pType,
      name: jugador?.originalName || jugador?.name
    }
  })

  const payload = {
    game_name: 'azul',
    jugadores: participantes
  }

  try {
    const token = localStorage.getItem('token')
    const res = await fetch(`${API_BASE}/azul/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`
      },
      body: JSON.stringify(payload)
    })
    if (!res.ok) {
      const text = await res.text()
      throw new Error(text || res.status)
    }
    const data = await res.json()
    router.push(`/azul/${data.azul_id}`)
  } catch (e) {
    console.error(e)
    error.value = e.message
  }
}
</script>

<style scoped>
.config-container {
  max-width: 800px;
  margin: 2rem auto;
  padding: 3rem;
  background: var(--glass-bg, rgba(30, 30, 30, 0.9));
  backdrop-filter: blur(10px);
  border: 1px solid var(--border-light, #555);
  border-radius: 12px;
  color: white;
}

.board-layout {
  display: grid;
  grid-template-areas:
    ".    top     ."
    "left center right"
    ".   bottom   .";
  grid-template-columns: 1fr auto 1fr;
  grid-template-rows: auto auto auto;
  gap: 2rem;
  justify-items: center;
  align-items: center;
  margin-top: 2rem;
}

.player-slot {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}

.player-slot.top { grid-area: top; }
.player-slot.left { grid-area: left; }
.player-slot.right { grid-area: right; }
.player-slot.bottom { grid-area: bottom; }

.center-visual {
  grid-area: center;
  width: 100px;
  height: 100px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.table-visual {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: radial-gradient(circle, var(--primary, #3498db), transparent);
  opacity: 0.2;
  box-shadow: 0 0 20px var(--primary, #3498db);
}

.glass-select {
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid var(--border-light, #555);
  color: white;
  padding: 0.5rem;
  border-radius: 4px;
  min-width: 150px;
  text-align: center;
  outline: none;
}

.glass-select:focus {
  border-color: var(--primary, #3498db);
  box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.3);
}

.glass-select option {
  background: #333;
  color: white;
}

.type-toggle {
    display: flex;
    background: rgba(0,0,0,0.3);
    border-radius: 6px;
    padding: 2px;
    margin-bottom: 0.2rem;
}

.type-toggle button {
    padding: 2px 8px;
    font-size: 0.7rem;
    color: #aaa;
    background: transparent;
    border: none;
    cursor: pointer;
    border-radius: 4px;
    transition: all 0.2s;
}

.type-toggle button.active {
    background: rgba(255,255,255,0.1);
    color: white;
    font-weight: bold;
}


.actions {
  display: flex;
  justify-content: center;
  margin-top: 3rem;
}

.error {
  color: #ef4444;
}

.btn-secondary {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: white;
  padding: 0.8rem 2rem;
  border-radius: 30px;
  cursor: pointer;
  margin-right: 1rem;
  transition: all 0.2s;
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.2);
}

.btn-primary {
    background: linear-gradient(135deg, var(--primary, #3498db), #2980b9);
    color: white;
    border: none;
    padding: 0.8rem 2rem;
    font-weight: bold;
    border-radius: 30px;
    cursor: pointer;
    box-shadow: 0 4px 15px rgba(52, 152, 219, 0.4);
    transition: transform 0.2s, box-shadow 0.2s;
}
</style>
