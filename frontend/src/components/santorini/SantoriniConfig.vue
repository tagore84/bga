<template>
  <div class="glass-panel config-container">
    <h2 class="text-center mb-1">Nueva Partida de Santorini</h2>
    <p class="text-center mb-3" style="color: var(--text-secondary)">Configura tu partida</p>

    <div v-if="error" class="error text-center mb-2">{{ error }}</div>

    <div class="board-layout">
        <!-- Yellow Player (Left) - Santorini P1 -->
        <div class="player-slot yellow-slot">
            <label class="player-label yellow-label">� Jugador 1</label>
            <div class="avatar-ph yellow-bg"></div>
            
            <!-- Type Toggle -->
            <div class="type-toggle">
                <button @click="p1Type = 'human'" :class="{ active: p1Type === 'human' }">Humano</button>
                <button @click="p1Type = 'ai'" :class="{ active: p1Type === 'ai' }">IA</button>
            </div>

            <select v-model="p1Id" class="glass-select">
                <option :value="null" disabled>Seleccionar...</option>
                <option v-for="player in (p1Type === 'human' ? humans : ais)" :key="player.id" :value="player.id">
                    {{ player.name }}
                </option>
            </select>
        </div>

        <!-- VS Visual (Center) -->
        <div class="vs-visual">
            <span class="vs-text">VS</span>
        </div>

        <!-- Red Player (Right) - Santorini P2 -->
        <div class="player-slot red-slot">
            <label class="player-label red-label">🔴 Jugador 2</label>
            <div class="avatar-ph red-bg"></div>

             <!-- Type Toggle -->
            <div class="type-toggle">
                <button @click="p2Type = 'human'" :class="{ active: p2Type === 'human' }">Humano</button>
                <button @click="p2Type = 'ai'" :class="{ active: p2Type === 'ai' }">IA</button>
            </div>

            <select v-model="p2Id" class="glass-select">
                 <option :value="null" disabled>Seleccionar...</option>
                <option v-for="player in (p2Type === 'human' ? humans : ais)" :key="player.id" :value="player.id">
                     {{ player.name }}
                </option>
            </select>
        </div>
    </div>

    <div class="actions mt-3">
        <button @click="goBack" class="btn-secondary">Volver</button>
        <button @click="createGame" :disabled="!isValid || creating" class="btn-primary">
            {{ creating ? 'Creando...' : 'Comenzar Partida' }}
        </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { API_BASE } from '../../config'

const router = useRouter()
const p1Type = ref('human')
const p2Type = ref('human')
const p1Id = ref(null)
const p2Id = ref(null)
const humans = ref([])
const ais = ref([])
const creating = ref(false)
const error = ref(null)

const isValid = computed(() => {
  return p1Id.value && p2Id.value
})

async function fetchPlayers() {
  try {
    const token = localStorage.getItem('token')
    
    // 1. Fetch games to find Santorini ID
    const resGames = await fetch(`${API_BASE}/games`)
    if (!resGames.ok) throw new Error('Error al cargar juegos')
    const gamesData = await resGames.json()
    const allGames = gamesData.games ?? gamesData
    const santoriniGame = allGames.find(g => g.name === 'santorini')
    
    // 2. Fetch players
    const resPlayers = await fetch(`${API_BASE}/players`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    const data = await resPlayers.json()
    
    // 3. Filter
    humans.value = data.filter(p => p.type === 'human')
    
    if (santoriniGame) {
         ais.value = data.filter(p => p.type === 'ai' && p.game_id === santoriniGame.id)
    } else {
         console.warn("Santorini game not found in DB")
         ais.value = []
    }
    
    // Auto-select current user for P1
    if (token) {
        const username = JSON.parse(atob(token.split('.')[1])).sub
        const me = data.find(p => p.name === username)
        if (me) {
            p1Id.value = me.id
        }
    }
  } catch (e) {
    console.error(e)
    error.value = "Error al cargar datos iniciales"
  }
}

function goBack() {
  router.push('/games')
}

async function createGame() {
  if (!p1Id.value) return error.value = 'Selecciona Jugador 1'
  if (!p2Id.value) return error.value = 'Selecciona Jugador 2'

  creating.value = true
  error.value = null

  try {
    const payload = {
      game_name: 'Santorini',
      playerP1Type: p1Type.value,
      playerP1Id: p1Id.value,
      playerP2Type: p2Type.value,
      playerP2Id: p2Id.value
    }

    const res = await fetch(`${API_BASE}/santorini`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify(payload)
    })

    if (!res.ok) throw new Error('Error al crear la partida')
    
    const game = await res.json()
    router.push(`/santorini/${game.id}`)
  } catch (e) {
    error.value = e.message
  } finally {
    creating.value = false
  }
}

onMounted(() => {
  fetchPlayers()
})
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
.red-label { color: #ff6b6b; text-shadow: 0 0 10px rgba(255,107,107,0.3); }
.yellow-label { color: #fcc419; text-shadow: 0 0 10px rgba(252,196,25,0.3); }

.avatar-ph {
    width: 80px;
    height: 80px;
    border-radius: 50%;
    margin-bottom: 0.5rem;
    box-shadow: 0 5px 15px rgba(0,0,0,0.3);
}
.red-bg { background: linear-gradient(135deg, #ff6b6b, #c92a2a); }
.yellow-bg { background: linear-gradient(135deg, #fcc419, #f08c00); }

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

.glass-input, .glass-select {
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

.glass-input:focus, .glass-select:focus {
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
