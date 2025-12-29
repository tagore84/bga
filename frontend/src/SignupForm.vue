<template>
    <div class="glass-panel signup-container">
      <h2 class="text-center mb-1">Crear Cuenta</h2>
      <p class="text-center mb-2" style="color: var(--text-secondary)">Únete a la comunidad.</p>

      <form @submit.prevent="signup" class="form-grid">
        <div class="input-group"> 
          <input v-model="name" placeholder="Nombre de usuario" required />
        </div>
        <div class="input-group">
          <input v-model="password" type="password" placeholder="Contraseña" required />
        </div>
        
        <button type="submit" class="btn-primary w-full mt-1">Registrarse</button>
      </form>
      
      <p v-if="error" class="error text-center">{{ error }}</p>
    </div>
  </template>
  
  <script setup>
  import { ref } from 'vue'

  const emit = defineEmits(['login-success', 'signup-success'])
  
  const name = ref('')
  const password = ref('')
  const error = ref('')
  
  import { API_BASE } from './config'

  
  const signup = async () => {
    try {
      const signupRes = await fetch(`${API_BASE}/auth/signup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: name.value, password: password.value })
      })
      if (!signupRes.ok) throw new Error('Error en el registro')
      const data = await signupRes.json()
      localStorage.setItem('token', data.access_token)
      //router.push('/games')
      const meRes = await fetch(`${API_BASE}/auth/me`, {
        headers: { Authorization: `Bearer ${data.access_token}` }
      })
      const user = await meRes.json()
      emit('login-success', { token: data.access_token, name: user.name })
      // Removed alert
    } catch (e) {
      error.value = e.message
    }
  }
  </script>
  
  <style scoped>
  .signup-container {
      width: 100%;
      max-width: 400px;
      margin: 4rem auto;
  }
  
  .form-grid {
      display: flex;
      flex-direction: column;
      gap: 1rem;
  }
  
  .error {
      color: #ef4444;
      margin-top: 1rem;
      font-size: 0.9rem;
  }
  </style>