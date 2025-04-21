<template>
  <div id="app">
    <h1>BGA Hola Mundo</h1>

    <!-- Si no hay token, mostramos login/registro -->
    <div v-if="!token">
      <button @click="view = 'login'">Iniciar sesión</button>
      <button @click="view = 'signup'">Registrarse</button>
      <LoginForm v-if="view === 'login'" @login-success="onLoginSuccess" />
      <SignupForm v-if="view === 'signup'" @signup-success="onLoginSuccess" />
    </div>

    <!-- Si hay token, mostramos bienvenida + selección de juegos -->
    <div v-else>
      <p>Bienvenido, {{ username }}.</p>
      <button @click="logout">Cerrar sesión</button>
      <!-- Aquí importamos y renderizamos tu GamesList -->
      <GamesList />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import LoginForm from './LoginForm.vue'
import SignupForm from './SignupForm.vue'
import GamesList from './GamesList.vue'

const view = ref('login')
const token = ref('')
const username = ref('')

// Al montar, comprobamos si ya había token almacenado
onMounted(async () => {
  const t = localStorage.getItem('token')
  if (t) {
    token.value = t
    // (re)obtenemos el nombre de usuario
    const res = await fetch(`http://localhost:8000/me?token=${t}`)
    const data = await res.json()
    username.value = data.username
  }
})

// Cuando LoginForm/SignupForm emiten 'login-success'
function onLoginSuccess({ token: t, username: u }) {
  token.value = t
  username.value = u
}

// Cerrar sesión
function logout() {
  localStorage.removeItem('token')
  token.value = ''
  username.value = ''
  view.value = 'login'
}
</script>