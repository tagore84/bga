<template>
  <div class="glass-panel config-container">
    <h2 class="text-center mb-1">Nueva Partida de Conecta Cuatro</h2>
    <p class="text-center mb-3" style="color: var(--text-secondary)">Selecciona los contrincantes</p>

    <div v-if="error" class="error text-center mb-2">{{ error }}</div>

    <div class="board-layout">
        <!-- Red Player (Left) -->
        <div class="player-slot red-slot">
            <label class="player-label red-label">🔴 Jugador Rojo</label>
            <div class="avatar-ph red-bg"></div>
            <select v-model="playerRed" class="glass-select">
                <option :value="null" disabled>Seleccionar...</option>
                <option v-for="player in players" :key="player.id" :value="player.id">
                    {{ player.name }}
                </option>
            </select>
        </div>

        <!-- VS Visual (Center) -->
        <div class="vs-visual">
            <span class="vs-text">VS</span>
        </div>

        <!-- Blue Player (Right) -->
        <div class="player-slot blue-slot">
            <label class="player-label blue-label">🔵 Jugador Azul</label>
            <div class="avatar-ph blue-bg"></div>
            <select v-model="playerBlue" class="glass-select">
                 <option :value="null" disabled>Seleccionar...</option>
                <option v-for="player in players" :key="player.id" :value="player.id">
                     {{ player.name }}
                </option>
            </select>
        </div>
    </div>

    <div class="actions mt-3">
        <button @click="goBack" class="btn-secondary">Volver</button>
        <button @click="createGame" :disabled="!isValid" class="btn-primary">
            Comenzar Partida
        </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { API_BASE } from '../../config'

const router = useRouter()
const players = ref([])
const error = ref(null)
const playerRed = ref(null)
const playerBlue = ref(null)

const isValid = computed(() => playerRed.value && playerBlue.value)

onMounted(async () => {
    try {
        const token = localStorage.getItem('token')
        
        // 1. Fetch available games to find "connect4" ID
        const resGames = await fetch(`${API_BASE}/games`)
        if (!resGames.ok) throw new Error('Error al cargar juegos')
        const gamesData = await resGames.json()
        const allGames = gamesData.games ?? gamesData
        const c4Game = allGames.find(g => g.name === 'connect4')
        
        // 2. Fetch players
        const resPlayers = await fetch(`${API_BASE}/players/`, {
            headers: { Authorization: `Bearer ${token}` }
        })
        if (!resPlayers.ok) throw new Error('No se pudieron cargar los jugadores')
        const rawPlayers = await resPlayers.json()
        
        // 3. Filter: Humans + Connect4 AIs
        if (c4Game) {
            players.value = rawPlayers.filter(p => p.type === 'human' || p.game_id === c4Game.id)
        } else {
             players.value = rawPlayers
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
    const pRedId = playerRed.value
    const pBlueId = playerBlue.value
  
    if (!pRedId || !pBlueId) {
        error.value = "Selecciona ambos jugadores"
        return
    }

    const selRed = players.value.find(p => p.id === parseInt(pRedId))
    const selBlue = players.value.find(p => p.id === parseInt(pBlueId))

    const payload = {
        game_name: 'connect4',
        playerRedType: selRed.type,
        playerRedId: parseInt(pRedId),
        playerBlueType: selBlue.type,
        playerBlueId: parseInt(pBlueId)
    }

    try {
        const token = localStorage.getItem('token')
        const res = await fetch(`${API_BASE}/connect4/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                Authorization: `Bearer ${token}`
            },
            body: JSON.stringify(payload)
        })
        if (!res.ok) {
             const txt = await res.text()
             throw new Error(txt || res.status)
        }
        const data = await res.json()
        router.push(`/connect4/${data.id}`)
    } catch (e) {
        error.value = e.message
    }
}
</script>

<style scoped>
.config-container {
  max-width: 700px;
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
.blue-label { color: #4dabf7; text-shadow: 0 0 10px rgba(77,171,247,0.3); }

.avatar-ph {
    width: 80px;
    height: 80px;
    border-radius: 50%;
    margin-bottom: 0.5rem;
    box-shadow: 0 5px 15px rgba(0,0,0,0.3);
}
.red-bg { background: linear-gradient(135deg, #ff6b6b, #c92a2a); }
.blue-bg { background: linear-gradient(135deg, #4dabf7, #1864ab); }

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
