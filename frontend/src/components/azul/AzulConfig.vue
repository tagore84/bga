<template>
  <div class="glass-panel config-container">
    <h2 class="text-center mb-1">Create Azul Game</h2>
    <p class="text-center mb-2" style="color: var(--text-secondary)">Select players for the match</p>

    <div v-if="error" class="error text-center mb-1">{{ error }}</div>
    
    <div class="board-layout">
      <!-- Top -->
      <div class="player-slot top">
        <label>Player 1</label>
        <select v-model="selectedPlayers[0]" class="glass-select">
          <option :value="null">Empty</option>
          <option v-for="player in players" :key="player.id" :value="player.id">{{ player.displayName }}</option>
        </select>
      </div>

      <!-- Left -->
      <div class="player-slot left">
        <label>Player 2</label>
        <select v-model="selectedPlayers[1]" class="glass-select">
          <option :value="null">Empty</option>
          <option v-for="player in players" :key="player.id" :value="player.id">{{ player.displayName }}</option>
        </select>
      </div>

      <!-- Center (Visual) -->
      <div class="center-visual">
        <div class="table-visual"></div>
      </div>

      <!-- Right -->
      <div class="player-slot right">
        <label>Player 4</label>
        <select v-model="selectedPlayers[3]" class="glass-select">
          <option :value="null">Empty</option>
          <option v-for="player in players" :key="player.id" :value="player.id">{{ player.displayName }}</option>
        </select>
      </div>

      <!-- Bottom -->
      <div class="player-slot bottom">
        <label>Player 3</label>
        <select v-model="selectedPlayers[2]" class="glass-select">
          <option :value="null">Empty</option>
          <option v-for="player in players" :key="player.id" :value="player.id">{{ player.displayName }}</option>
        </select>
      </div>
    </div>

    <div class="actions mt-2">
      <button @click="createGame" class="btn-primary">Start Game</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const players = ref([])
const error = ref(null)
const selectedPlayers = ref([null, null, null, null])


const API = 'http://localhost:8000'

onMounted(async () => {
  try {
    const token = localStorage.getItem('token')
    const resPlayers = await fetch(`${API}/players/`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    if (!resPlayers.ok) throw new Error('Could not load players')
    const rawPlayers = await resPlayers.json()
    
    // Obtener usuario actual
    let currentUserName = null
    try {
      const resMe = await fetch(`${API}/auth/me`, {
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
      'Fácil': 'Fácil',
      'Medio': 'Medio',
      'Difícil': 'Difícil',
      'Experimental': 'Experimental'
    }

    players.value = rawPlayers
      .filter(p => p.game_id === 2 || p.game_id === null)
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

        return { ...p, name: newName, displayName }
      })
      .sort((a, b) => {
        const getPriority = (p) => {
          if (currentUserName && p.name === currentUserName) return 0
          if (p.type !== 'ai') return 1
          
          // AI ordering based on mapped name (which is in p.name now)
          if (p.name === 'Fácil') return 2
          if (p.name === 'Medio') return 3
          if (p.name === 'Difícil') return 4
          if (p.name === 'Experimental') return 5
          return 6
        }
        return getPriority(a) - getPriority(b)
      })
  } catch (e) {
    console.error(e)
    error.value = e.message
  }
})
async function createGame() {
  error.value = null
  const selected = selectedPlayers.value.filter(p => p !== null)
  if (selected.length < 2) {
    error.value = "Select at least 2 players."
    return
  }

  const participantes = selected.map(id => {
    const jugador = players.value.find(p => p.id === id)
    let pType = jugador?.type || 'human'
    
    // Fix: If it's the DeepMCTS player (Experimental), set the specific type
    // so the frontend knows to enable Neural Vision.
    if (jugador?.name === 'Experimental') {
      pType = 'azul_deep_mcts'
    }

    return {
      id,
      type: pType,
      name: jugador?.name
    }
  })



  const payload = {
    game_name: 'azul',
    jugadores: participantes
  }

  try {
    const token = localStorage.getItem('token')
    const res = await fetch(`${API}/azul/`, {
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
  background: radial-gradient(circle, var(--primary), transparent);
  opacity: 0.2;
  box-shadow: 0 0 20px var(--primary);
}

.glass-select {
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid var(--border-light);
  color: white;
  padding: 0.5rem;
  border-radius: var(--radius-sm);
  min-width: 150px;
  text-align: center;
  outline: none;
}

.glass-select:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 2px var(--primary-glow);
}

.glass-select option {
  background: var(--bg-dark);
  color: white;
}

.actions {
  display: flex;
  justify-content: center;
  margin-top: 3rem;
}

.error {
  color: #ef4444;
}
</style>
