<template>
  <div class="games-list">
    <h2>Selecciona un juego</h2>
    <ul>
      <li v-for="game in games" :key="game.key">
        <button @click="selectGame(game)">{{ game.name }}</button>
      </li>
    </ul>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const API_BASE = window.location.hostname === 'localhost'
  ? 'http://localhost:8000'
  : 'http://backend:8000'

// Lista de juegos con su endpoint
const games = ref([
  { key: 'tictactoe', name: 'Tres en Raya' },
  // Más juegos futuribles
])

async function selectGame(game) {
  try {
    // Crear nueva partida
    const res = await fetch(`${API_BASE}/${game.key}/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    })
    if (!res.ok) throw new Error('Error al crear la partida')
    const data = await res.json()
    // Redirigir a la partida creada
    router.push(`/games/${data.id}`)
  } catch (e) {
    console.error(e)
    alert(e.message)
  }
}
</script>

<style scoped>
.games-list {
  text-align: center;
  padding: 2rem;
}
.games-list ul {
  list-style: none;
  padding: 0;
}
.games-list li {
  margin: 0.5rem 0;
}
</style>