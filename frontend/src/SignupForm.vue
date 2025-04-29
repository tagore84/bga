<template>
    <div class="signup">
      <h2>Crear cuenta</h2>
      <form @submit.prevent="signup">
        <input v-model="name" placeholder="Usuario" required />
        <input v-model="password" type="password" placeholder="Contraseña" required />
        <button type="submit">Registrarse</button>
      </form>
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
  
  const signup = async () => {
    try {
      const signupRes = await fetch(`${API_BASE}/signup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: name.value, password: password.value })
      })
      if (!signupRes.ok) throw new Error('Error al registrar')
      const data = await signupRes.json()
      localStorage.setItem('token', data.access_token)
      //router.push('/games')
      const meRes = await fetch(`${API_BASE}/me?token=${data.access_token}`)
      const user = await meRes.json()
      emit('login-success', { token: data.access_token, name: user.name })
      alert('Registro correcto')
    } catch (e) {
      error.value = e.message
    }
  }
  </script>
  
  <style scoped>
  .signup {
    max-width: 300px;
    margin: 2rem auto;
    padding: 1rem;
    border: 1px solid #ccc;
    border-radius: 8px;
    background: #f9f9f9;
  }
  .signup input {
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