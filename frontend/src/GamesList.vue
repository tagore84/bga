<template>
    <div class="games-list">
      <h2>Selecciona un juego</h2>
      <ul>
        <li v-for="game in games" :key="game.id">
          <button @click="selectGame(game.id)">{{ game.name }}</button>
        </li>
      </ul>
    </div>
  </template>
  
  <script setup>
  import { ref, onMounted } from 'vue'
  import { useRouter } from 'vue-router'
  
  const games = ref([])
  const router = useRouter()
  
  // Mock de juegos
  onMounted(() => {
    games.value = [
      { id: 1, name: 'Tres en Raya' },
      { id: 2, name: 'Azul' }
    ]
  })
  
  function selectGame(id) {
    // redirigir a partida o detalle
    router.push(`/games/${id}`)
  }
  </script>
  
  <style scoped>
  .games-list { text-align: center; padding: 2rem; }
  .games-list ul { list-style: none; padding: 0; }
  .games-list li { margin: 0.5rem 0; }
  </style>