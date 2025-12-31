<template>
  <div class="glass-panel config-container">
    <h2 class="text-center mb-1">Nueva Partida de Nim Misere</h2>
    <p class="text-center mb-3" style="color: var(--text-secondary)">Selecciona los contrincantes</p>

    <div v-if="error" class="error text-center mb-2">{{ error }}</div>

    <div class="board-layout">
        <!-- Player 1 (Left) -->
        <div class="player-slot p1-slot">
            <label class="player-label p1-label">👤 Jugador 1</label>
            <div class="avatar-ph p1-bg"></div>
            <select v-model="player1" class="glass-select">
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

        <!-- Player 2 (Right) -->
        <div class="player-slot p2-slot">
            <label class="player-label p2-label">👤 Jugador 2</label>
            <div class="avatar-ph p2-bg"></div>
            <select v-model="player2" class="glass-select">
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
const player1 = ref(null)
const player2 = ref(null)
const loading = ref(false)

const isValid = computed(() => player1.value && player2.value)

onMounted(async () => {
    try {
        const token = localStorage.getItem('token')
        
        // 1. Fetch available games to find "nim" ID
        const resGames = await fetch(`${API_BASE}/games`)
        if (!resGames.ok) throw new Error('Error al cargar juegos')
        const gamesData = await resGames.json()
        const allGames = gamesData.games ?? gamesData
        const nimGame = allGames.find(g => g.name === 'nim')
        
        // 2. Fetch players
        const resPlayers = await fetch(`${API_BASE}/players/`, {
            headers: { Authorization: `Bearer ${token}` }
        })
        if (!resPlayers.ok) throw new Error('No se pudieron cargar los jugadores')
        const rawPlayers = await resPlayers.json()
        
        // 3. Filter: Humans + Nim AIs or All AIs?
        // Nim AI players should have game_id associated with nim.
        if (nimGame) {
             // Show all Humans AND AIs for Nim. 
             // Maybe show ALL AIs? User said "jugadores de IA de Nim".
             players.value = rawPlayers.filter(p => p.type === 'human' || p.game_id === nimGame.id || p.name.includes("Nim"))
        } else {
             players.value = rawPlayers
        }
        
    } catch (e) {
        console.error(e)
        error.value = e.message
    }
})

function goBack() {
  router.push('/nimActive')
}

async function createGame() {
    error.value = null
    const p1Id = player1.value
    const p2Id = player2.value
  
    if (!p1Id || !p2Id) {
        error.value = "Selecciona ambos jugadores"
        return
    }

    const selP1 = players.value.find(p => p.id === parseInt(p1Id))
    const selP2 = players.value.find(p => p.id === parseInt(p2Id))

    // Auto-generate name
    const dateStr = new Date().toLocaleTimeString();
    const gameName = `Nim ${selP1.name} vs ${selP2.name} (${dateStr})`;

    const payload = {
        game_name: gameName,
        player1Type: selP1.type,
        player1Id: parseInt(p1Id),
        player2Type: selP2.type,
        player2Id: parseInt(p2Id)
    }
    
    loading.value = true;

    try {
        const token = localStorage.getItem('token')
        const res = await fetch(`${API_BASE}/nim/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                Authorization: `Bearer ${token}`
            },
            body: JSON.stringify(payload)
        })
        if (!res.ok) {
             const txt = await res.text()
             // Try to parse JSON error
             try {
                const jsonErr = JSON.parse(txt);
                throw new Error(jsonErr.detail || txt)
             } catch(e) {
                throw new Error(txt || res.status)
             }
        }
        const data = await res.json()
        router.push(`/nim/${data.id}`)
    } catch (e) {
        error.value = e.message
    } finally {
        loading.value = false;
    }
}
</script>

<style scoped>
.config-container {
  max-width: 700px;
  margin: 3rem auto;
  padding: 3rem;
  background: var(--glass-bg); /* Check if defined, else fallback */
  background-color: #1e1e1e;
  backdrop-filter: blur(10px);
  border: 1px solid #444;
  border-radius: 12px;
  color: white;
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
.p1-label { color: #f1c40f; text-shadow: 0 0 10px rgba(241, 196, 15, 0.3); } /* Yellow */
.p2-label { color: #9b59b6; text-shadow: 0 0 10px rgba(155, 89, 182, 0.3); } /* Purple */

.avatar-ph {
    width: 80px;
    height: 80px;
    border-radius: 50%;
    margin-bottom: 0.5rem;
    box-shadow: 0 5px 15px rgba(0,0,0,0.3);
}
.p1-bg { background: linear-gradient(135deg, #f1c40f, #d35400); }
.p2-bg { background: linear-gradient(135deg, #9b59b6, #8e44ad); }

.glass-select {
  width: 100%;
  background: rgba(0, 0, 0, 0.4);
  border: 1px solid #555;
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
  border-color: #3498db;
  box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.3);
  background: rgba(0,0,0,0.6);
}

.vs-visual {
    font-size: 2rem;
    font-weight: 900;
    font-style: italic;
    color: #3498db;
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
    background: linear-gradient(135deg, #2ecc71, #27ae60);
    color: white;
    border: none;
    padding: 1rem 3rem;
    font-size: 1.1rem;
    font-weight: bold;
    border-radius: 30px;
    cursor: pointer;
    box-shadow: 0 4px 15px rgba(46, 204, 113, 0.4);
    transition: transform 0.2s, box-shadow 0.2s;
}
.btn-primary:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(46, 204, 113, 0.6);
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
