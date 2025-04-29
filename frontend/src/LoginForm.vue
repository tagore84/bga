<template>
    <div class="login">
      <h2>Iniciar sesión</h2>
      <form @submit.prevent="login">
        <input v-model="name" placeholder="Usuario" required />
        <input v-model="password" type="password" placeholder="Contraseña" required />
        <button type="submit">Entrar</button>
      </form>
      <!-- Enlace para ir a la pantalla de registro -->
      <p class="register-link">
        ¿No tienes cuenta?
        <router-link to="/signup">Regístrate aquí</router-link>
      </p>
      <p v-if="error" class="error">{{ error }}</p>
    </div>
  </template>
  
  <script setup>
  import { ref } from 'vue'
  import { defineEmits } from 'vue'
  const emit = defineEmits(['login-success', 'signup-success'])  
  
  const name = ref('')
  const password = ref('')
  const error = ref('')
  
  const API_BASE = window.location.hostname === 'localhost' 
    ? 'http://localhost:8000' 
    : 'http://backend:8000'
  
  const login = async () => {
    try {
      const loginRes = await fetch(`${API_BASE}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: name.value, password: password.value })
      })
      if (!loginRes.ok) throw new Error('Error de login')
      const data = await loginRes.json()
      localStorage.setItem('token', data.access_token)
      const meRes = await fetch(`http://localhost:8000/me?token=${data.access_token}`)
      const user = await meRes.json()
      emit('login-success', { token: data.access_token, name: user.name })
      alert('Login correcto')
    } catch (e) {
      error.value = e.message
    }
  }
  </script>
  
  <style scoped>
  .login {
    max-width: 300px;
    margin: 2rem auto;
    padding: 1rem;
    border: 1px solid #ccc;
    border-radius: 8px;
    background: #f9f9f9;
  }
  .login input {
    display: block;
    margin: 0.5rem 0;
    width: 100%;
    padding: 0.5rem;
  }
  .error {
    color: red;
    margin-top: 1rem;
  }
  </style>
  