<template>
  <div class="active-games-container">
    <div class="header-actions">
       <div class="left-action">
         <button @click="goBack" class="btn-secondary back-btn">
           <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 12H5"/><path d="M12 19l-7-7 7-7"/></svg>
           Volver
         </button>
       </div>
       <h2 class="page-title">Partidas Activas</h2>
       <div class="right-action">
         <button @click="createNewGame" class="btn-primary">+ Nueva Partida</button>
       </div>
    </div>

    <div v-if="loading" class="status-msg">Cargando partidas...</div>
    <div v-else-if="error" class="status-msg error">{{ error }}</div>
    
    <div v-else class="games-grid">
      <div v-if="games.length === 0" class="empty-state">
        <p>No hay partidas en curso.</p>
        <button @click="createNewGame" class="btn-primary mt-2">Crear la primera</button>
      </div>

      <div v-else v-for="game in games" :key="game.id" class="glass-panel game-card">
        <div class="card-header">
          <span class="game-id">Partida #{{ game.id }}</span>
          <span class="turn-badge">Turno: {{ game.state.turno_actual }}</span>
        </div>
        
        <div class="card-body">
             <div class="info-row">
               <span>Ronda:</span> <strong>{{ game.state.ronda || 1 }}</strong>
             </div>
             <div class="info-row">
               <span>Jugadores:</span> <strong>{{ Object.keys(game.state.jugadores || {}).length }}</strong>
             </div>
        </div>

        <div class="card-actions">
          <button @click="joinGame(game.id)" class="btn-primary full-width">Jugar</button>
          <button @click="deleteGame(game.id)" class="btn-danger-outline full-width">Eliminar</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const games = ref([])
const loading = ref(true)
const error = ref(null)
import { API_BASE } from '../../config'


async function fetchActiveGames() {
  try {
    const res = await fetch(`${API_BASE}/azul/`)
    if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`)
    games.value = await res.json()
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

function joinGame(id) {
  router.push(`/azul/${id}`)
}

function goBack() {
  router.back()
}

function createNewGame() {
  router.push('/azulConfig')
}

async function deleteGame(id) {
  if (!confirm(`¿Estás seguro de que quieres eliminar la partida #${id}?`)) {
    return
  }
  
  try {
    const res = await fetch(`${API_BASE}/azul/${id}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    })
    
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}: ${await res.text()}`)
    }
    
    // Refresh the list after deletion
    await fetchActiveGames()
  } catch (e) {
    alert(`Error al eliminar la partida: ${e.message}`)
  }
}


onMounted(fetchActiveGames)
</script>

<style scoped>
.active-games-container {
  max-width: 1200px;
  margin: 2rem auto;
  padding: 0 2rem;
}

/* Header layout with Grid for perfect centering */
.header-actions {
  display: grid;
  grid-template-columns: 200px 1fr 200px; /* Sidebar widths fixed, center flexible */
  align-items: center;
  margin-bottom: 2rem;
  gap: 1rem;
}

.left-action {
  justify-self: start;
}

.right-action {
  justify-self: end;
}

.page-title {
  font-family: 'Outfit', sans-serif;
  font-size: 2rem;
  margin: 0;
  text-align: center;
  white-space: nowrap; /* Prevent wrapping if possible */
  background: linear-gradient(to right, #ffffff, #a5f3fc);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

/* Styled Back Button */
.back-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: rgba(255, 255, 255, 0.05); /* Slightly visible */
  border: 1px solid var(--border-light);
  color: var(--text-secondary);
  padding: 0.5rem 1rem;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 0.95rem;
}

.back-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: white;
  border-color: rgba(255, 255, 255, 0.3);
  transform: translateX(-2px);
}

.status-msg {
  text-align: center;
  font-size: 1.2rem;
  color: var(--text-secondary);
  margin-top: 3rem;
}

.error {
  color: #ef4444;
}

/* Grid Layout */
.games-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.5rem;
}

.empty-state {
  grid-column: 1 / -1;
  text-align: center;
  padding: 4rem;
  background: rgba(255,255,255,0.02);
  border-radius: var(--radius-md);
}

/* Game Card */
.game-card {
  display: flex;
  flex-direction: column;
  height: 100%;
  transition: transform 0.2s, box-shadow 0.2s;
}

.game-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 25px rgba(0,0,0,0.3);
  border-color: var(--primary-glow);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid rgba(255,255,255,0.1);
}

.game-id {
  font-weight: 700;
  font-size: 1.1rem;
}

.turn-badge {
  background: rgba(59, 130, 246, 0.2);
  color: #93c5fd;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 0.8rem;
}

.card-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
  color: var(--text-secondary);
}

.info-row {
  display: flex;
  justify-content: space-between;
}

.card-actions {
  display: flex;
  gap: 0.5rem;
}

.full-width {
  flex: 1;
}

.btn-danger-outline {
  background: transparent;
  border: 1px solid #ef4444;
  color: #ef4444;
  padding: 0.5rem;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.2s;
}

.btn-danger-outline:hover {
  background: #ef4444;
  color: white;
}
</style>
