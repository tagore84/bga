<template>
  <div class="config">
    <h2>Configura Tres en Raya</h2>

    <div v-if="error" class="error">{{ error }}</div>

    <div class="field">
      <label>Jugador X:</label>
      <select v-model="playerX">
        <option
          v-for="u in players"
          :key="`player_id`"
          :value="`${u.id}`"
        >
          {{ u.name }}
        </option>
      </select>
    </div>

    <div class="field">
      <label>Jugador O:</label>
      <select v-model="playerO">
        <option
          v-for="u in players"
          :key="`player_id`"
          :value="`${u.id}`"
        >
          {{ u.name }}
        </option>
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

const playerX = ref(null)
const playerO = ref(null)

const API = 'http://localhost:8000'

onMounted(async () => {
  try {
    const token = localStorage.getItem('token')
    const resPlayers = await fetch(`${API}/players/`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    if (!resPlayers.ok) throw new Error('No se pudieron cargar los jugadores')
    const rawPlayers = await resPlayers.json()
    players.value = rawPlayers.filter(p => p.game_id === 1 || p.game_id === null)
  } catch (e) {
    console.error(e)
    error.value = e.message
  }
})

async function createGame() {
  error.value = null
  // Extraer tipo e ID
  const playerXId = playerX.value
  const playerOId = playerO.value
  const selectedPlayerX = players.value.find(p => p.id === parseInt(playerXId, 10))
  const selectedPlayerO = players.value.find(p => p.id === parseInt(playerOId, 10))
  const playerXType_ = selectedPlayerX?.type
  const playerOType_ = selectedPlayerO?.type
  // ToDo
  const payload = {
    game_name: 'tictactoe',
    playerXType: playerXType_,
    playerXId: parseInt(playerXId, 10),
    playerOType: playerOType_,
    playerOId: parseInt(playerOId, 10),
  }
  try {
    const token = localStorage.getItem('token')
    const res = await fetch(`${API}/tictactoe/`, {
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
    router.push(`/tictactoe/${data.id}`)
  } catch (e) {
    console.error(e)
    error.value = e.message
  }
}
</script>

<style scoped>
.config { max-width: 400px; margin: 2rem auto; }
.field { margin-bottom: 1rem; }
label { display: block; font-weight: bold; margin-bottom: 0.5rem; }
select { width: 100%; padding: 0.5rem; }
button { padding: 0.5rem 1rem; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
button:hover { background: #0056b3; }
.error { color: red; margin-top: 1rem; }
</style>