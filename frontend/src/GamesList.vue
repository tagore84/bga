<!-- frontend/src/components/GamesList.vue -->
<template>
  <div class="games-list">
    <h2>Selecciona un juego</h2>

    <!-- Aquí añadimos el botón para ir a la lista de partidas activas -->
    <button @click="goToActive" class="active-games-btn">
      Ver partidas activas
    </button>

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
const games = ref([
  { key: 'tictactoe', name: 'Tres en Raya', configRoute: '/configure/tictactoe' },
  // otros juegos…
])

function selectGame(game) {
  router.push(game.configRoute)
}

function goToActive() {
  router.push('/active')
}
</script>

<style scoped>
.active-games-btn {
  margin-bottom: 1rem;
  padding: 0.5em 1em;
  background: #28a745;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
.active-games-btn:hover {
  background: #218838;
}
</style>