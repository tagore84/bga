<template>
  <div class="glass-panel config-container">
    <h2 class="text-center mb-1">Configura Tres en Raya</h2>
    <p class="text-center mb-3" style="color: var(--text-secondary)">Selecciona los contrincantes</p>

    <div v-if="error" class="error text-center mb-2">{{ error }}</div>

    <div class="board-layout">
      <!-- Player X (Left) -->
      <div class="player-slot x-slot">
        <label class="player-label x-label">❌ Jugador X</label>
        <div class="avatar-ph x-bg"></div>

        <!-- Type Toggle -->
        <div class="type-toggle">
          <button @click="pXType = 'human'" :class="{ active: pXType === 'human' }">Humano</button>
          <button @click="pXType = 'ai'" :class="{ active: pXType === 'ai' }">IA</button>
        </div>

        <select v-model="playerX" class="glass-select">
          <option :value="null" disabled>Seleccionar...</option>
          <option v-for="u in (pXType === 'human' ? humans : ais)" :key="u.id" :value="`${u.id}`">
            {{ u.name }}
          </option>
        </select>
      </div>

      <!-- VS Visual (Center) -->
      <div class="vs-visual">
          <span class="vs-text">VS</span>
      </div>

      <!-- Player O (Right) -->
      <div class="player-slot o-slot">
        <label class="player-label o-label">⭕ Jugador O</label>
        <div class="avatar-ph o-bg"></div>

        <!-- Type Toggle -->
        <div class="type-toggle">
          <button @click="pOType = 'human'" :class="{ active: pOType === 'human' }">Humano</button>
          <button @click="pOType = 'ai'" :class="{ active: pOType === 'ai' }">IA</button>
        </div>

        <select v-model="playerO" class="glass-select">
          <option :value="null" disabled>Seleccionar...</option>
           <option v-for="u in (pOType === 'human' ? humans : ais)" :key="u.id" :value="`${u.id}`">
            {{ u.name }}
          </option>
        </select>
      </div>
    </div>

    <div class="actions mt-3">
      <button @click="goBack" class="btn-secondary">Volver</button>
      <button @click="createGame" :disabled="!isValid" class="btn-primary">Crear partida</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { API_BASE } from '../../config'

const router = useRouter()
const humans = ref([])
const ais = ref([])
const error = ref(null)

const playerX = ref(null)
const playerO = ref(null)
const pXType = ref('human')
const pOType = ref('human')

const isValid = computed(() => playerX.value && playerO.value)

onMounted(async () => {
  try {
    const token = localStorage.getItem('token')

     // 1. Fetch available games to find "tictactoe" ID
    const resGames = await fetch(`${API_BASE}/games`)
    if (!resGames.ok) throw new Error('Error al cargar juegos')
    const gamesData = await resGames.json()
    const allGames = gamesData.games ?? gamesData
    const tttGame = allGames.find(g => g.name === 'tictactoe')

    // 2. Fetch players
    const resPlayers = await fetch(`${API_BASE}/players/`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    if (!resPlayers.ok) throw new Error('No se pudieron cargar los jugadores')
    const rawPlayers = await resPlayers.json()
    
    // 3. Split Humans / AIs
    humans.value = rawPlayers.filter(p => p.type === 'human')
    
    if (tttGame) {
        ais.value = rawPlayers.filter(p => p.type === 'ai' && p.game_id === tttGame.id)
    } else {
        ais.value = []
    }

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
  const playerXId = playerX.value
  const playerOId = playerO.value

  // Find pure objects to get type correctly if needed
  const selectedPlayerX = (pXType.value === 'human' ? humans.value : ais.value).find(p => p.id === parseInt(playerXId, 10))
  const selectedPlayerO = (pOType.value === 'human' ? humans.value : ais.value).find(p => p.id === parseInt(playerOId, 10))

  const payload = {
    game_name: 'tictactoe',
    playerXType: selectedPlayerX?.type || 'human',
    playerXId: parseInt(playerXId, 10),
    playerOType: selectedPlayerO?.type || 'human',
    playerOId: parseInt(playerOId, 10),
  }
  try {
    const token = localStorage.getItem('token')
    const res = await fetch(`${API_BASE}/tictactoe/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`
      },
      body: JSON.stringify(payload)
    })
    if (!res.ok) {
        // Try parsing error
      const text = await res.text()
      try {
          const jsonErr = JSON.parse(text)
          throw new Error(jsonErr.detail || text)
      } catch (e2) {
           throw new Error(text || res.status)
      }
    }
    const data = await res.json()
    router.push(`/tictactoe/${data.id}`)
  } catch (e) {
    console.error(e)
    error.value = e.message
  }
}
</script>

<style scoped>
.config-container {
  max-width: 800px;
  margin: 3rem auto;
  padding: 3rem;
  background: var(--glass-bg);
  backdrop-filter: blur(10px);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
}

.text-center { text-align: center; }
.mb-1 { margin-bottom: 0.5rem; }
.mb-2 { margin-bottom: 1rem; }
.mb-3 { margin-bottom: 2rem; }
.mt-3 { margin-top: 2rem; }

.board-layout {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 2rem;
  position: relative;
}

.player-slot {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  background: rgba(255,255,255,0.03);
  padding: 2rem;
  border-radius: 12px;
  transition: transform 0.2s;
}

.player-slot:hover {
    transform: translateY(-2px);
    background: rgba(255,255,255,0.05);
}

.player-label {
    font-size: 1.1rem;
    font-weight: bold;
    text-transform: uppercase;
    letter-spacing: 1px;
}
.x-label { color: #ff6b6b; text-shadow: 0 0 10px rgba(255,107,107,0.3); }
.o-label { color: #4dabf7; text-shadow: 0 0 10px rgba(77,171,247,0.3); }

.avatar-ph {
    width: 80px;
    height: 80px;
    border-radius: 50%;
    margin-bottom: 0.5rem;
    box-shadow: 0 5px 15px rgba(0,0,0,0.3);
}
.x-bg { background: linear-gradient(135deg, #ff6b6b, #c92a2a); }
.o-bg { background: linear-gradient(135deg, #4dabf7, #1864ab); }

.type-toggle {
    display: flex;
    background: rgba(0,0,0,0.3);
    border-radius: 6px;
    padding: 2px;
    margin-bottom: 0.5rem;
}

.type-toggle button {
    padding: 4px 12px;
    font-size: 0.8rem;
    color: var(--text-secondary);
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

.glass-select {
  width: 100%;
  background: rgba(0, 0, 0, 0.4);
  border: 1px solid var(--border-light);
  color: white;
  padding: 0.8rem;
  border-radius: 6px;
  text-align: center;
  font-size: 1rem;
  outline: none;
  cursor: pointer;
  transition: all 0.2s;
}

.glass-select:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 2px var(--primary-glow);
  background: rgba(0,0,0,0.6);
}

.vs-visual {
    font-size: 2rem;
    font-weight: 900;
    font-style: italic;
    color: var(--primary);
    opacity: 0.5;
}
.vs-text {
    background: -webkit-linear-gradient(#eee, #333);
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
}

.actions {
  display: flex;
  justify-content: center;
}

.btn-primary {
    background: linear-gradient(135deg, var(--primary), var(--primary-dark));
    color: white;
    border: none;
    padding: 1rem 3rem;
    font-size: 1.1rem;
    font-weight: bold;
    border-radius: 30px;
    cursor: pointer;
    box-shadow: 0 4px 15px var(--primary-glow);
    transition: transform 0.2s, box-shadow 0.2s;
}
.btn-primary:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px var(--primary-glow);
}
.btn-primary:active:not(:disabled) {
    transform: translateY(1px);
}
.btn-primary:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    filter: grayscale(1);
}

.btn-secondary {
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    color: white;
    padding: 1rem 3rem;
    font-size: 1.1rem;
    font-weight: bold;
    border-radius: 30px;
    cursor: pointer;
    margin-right: 1rem;
    transition: all 0.2s;
}
.btn-secondary:hover {
    background: rgba(255, 255, 255, 0.2);
}

.error { color: #ef4444; font-weight: bold;}
</style>