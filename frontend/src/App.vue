<template>
  <div id="app">
    <h1>BGA Hola Mundo</h1>
    <div ref="stageContainer"></div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import Konva from 'konva'

const stageContainer = ref(null)

onMounted(() => {
  const stage = new Konva.Stage({
    container: stageContainer.value,
    width: window.innerWidth,
    height: window.innerHeight / 2
  })
  const layer = new Konva.Layer()
  const text = new Konva.Text({
    x: 50, y: 50,
    text: '¡Hola Mundo de Konva en BGA!',
    fontSize: 30
  })
  layer.add(text)
  stage.add(layer)

  // Conexión WebSocket
  const ws = new WebSocket('ws://localhost:8000/ws/cliente1')
  ws.onmessage = event => {
    console.log('Mensaje WS:', event.data)
  }
})
</script>

<style>
#app { text-align: center; padding: 20px; }
</style>