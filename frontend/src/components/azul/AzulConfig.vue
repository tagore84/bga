<template>
  <div class="azul-config">
    <h2>Configurar nueva partida de Azul</h2>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="board-layout">
      <select v-model="selectedPlayers[0]" class="selector top">
        <option :value="null">Vacío</option>
        <option v-for="player in players" :key="player.id" :value="player.id">{{ player.name }}</option>
      </select>
      <select v-model="selectedPlayers[1]" class="selector left">
        <option :value="null">Vacío</option>
        <option v-for="player in players" :key="player.id" :value="player.id">{{ player.name }}</option>
      </select>
      <select v-model="selectedPlayers[2]" class="selector bottom">
        <option :value="null">Vacío</option>
        <option v-for="player in players" :key="player.id" :value="player.id">{{ player.name }}</option>
      </select>
      <select v-model="selectedPlayers[3]" class="selector right">
        <option :value="null">Vacío</option>
        <option v-for="player in players" :key="player.id" :value="player.id">{{ player.name }}</option>
      </select>
    </div>
    <button @click="createGame">Crear partida</button>
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
    if (!resPlayers.ok) throw new Error('No se pudieron cargar los jugadores')
    const rawPlayers = await resPlayers.json()
    players.value = rawPlayers.filter(p => p.game_id === 2 || p.game_id === null)
  } catch (e) {
    console.error(e)
    error.value = e.message
  }
})
async function createGame() {
  error.value = null
  const selected = selectedPlayers.value.filter(p => p !== null)
  if (selected.length < 2) {
    error.value = "Debes seleccionar al menos 2 jugadores para Azul."
    return
  }

  const participantes = selected.map(id => {
    const jugador = players.value.find(p => p.id === id)
    return {
      id,
      type: jugador?.type || 'human',
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
.azul-config {
  text-align: center;
}
.board-layout {
  display: grid;
  grid-template-areas:
    ".    top     ."
    "left center right"
    ".   bottom   .";
  grid-template-columns: 1fr auto 1fr;
  grid-template-rows: auto auto auto;
  gap: 1em;
  justify-items: center;
  align-items: center;
}
.selector.top {
  grid-area: top;
}
.selector.left {
  grid-area: left;
}
.selector.right {
  grid-area: right;
}
.selector.bottom {
  grid-area: bottom;
}
.error {
  color: red;
  margin-bottom: 1em;
}
</style>
