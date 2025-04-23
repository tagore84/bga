<template>
  <div class="config">
    <h2>Configura Tres en Raya</h2>

    <div class="field">
      <label>Jugador X:</label>
      <select v-model="playerX">
        <option value="ia">IA</option>
        <option
          v-for="u in users"
          :key="u.id"
          :value="u.username"
        >
          {{ u.username }}
        </option>
      </select>
    </div>

    <div class="field">
      <label>Jugador O:</label>
      <select v-model="playerO">
        <option value="ia">IA</option>
        <option
          v-for="u in users"
          :key="u.id"
          :value="u.username"
        >
          {{ u.username }}
        </option>
      </select>
    </div>

    <button @click="createGame">Crear partida</button>
    <p v-if="error" class="error">{{ error }}</p>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const users = ref([])
const error = ref(null)

// Cada dropdown almacena el nombre del jugador o 'ia'
const playerX = ref('ia')
const playerO = ref('ia')

const API = 'http://localhost:8000'

onMounted(async () => {
  try {
    const token = localStorage.getItem('token')
    const res = await fetch(`${API}/users/`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (!res.ok) {
      console.error('Error al cargar usuarios:', res.status, await res.text())
      error.value = 'No pude cargar la lista de usuarios'
      return
    }
    users.value = await res.json()
  } catch (e) {
    console.error(e)
    error.value = 'Error de conexión al cargar usuarios'
  }
})

async function createGame() {
  error.value = null
  // Determinar tipo e id (nombre) según selección
  const payload = {
    playerXType: playerX.value === 'ia' ? 'ia' : 'user',
    playerXId:   playerX.value === 'ia' ? null : playerX.value,
    playerOType: playerO.value === 'ia' ? 'ia' : 'user',
    playerOId:   playerO.value === 'ia' ? null : playerO.value,
  }

  try {
    const token = localStorage.getItem('token')
    const res = await fetch(`${API}/tictactoe/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(payload)
    })
    if (!res.ok) {
      const text = await res.text()
      throw new Error(text || `HTTP ${res.status}`)
    }
    const data = await res.json()
    router.push(`/games/${data.id}`)
  } catch (e) {
    error.value = e.message
  }
}
</script>

<style scoped>
.config {
  max-width: 400px;
  margin: 2rem auto;
  text-align: left;
}
.field {
  margin-bottom: 1rem;
}
label {
  display: block;
  margin-bottom: 0.3rem;
  font-weight: bold;
}
select {
  width: 100%;
  padding: 0.4em;
  border-radius: 4px;
  border: 1px solid #ccc;
}
button {
  padding: 0.5em 1em;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
button:hover {
  background: #0056b3;
}
.error {
  color: red;
  margin-top: 1rem;
}
</style>
