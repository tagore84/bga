<template>
    <div class="glass-panel login-container">
      <h2 class="text-center mb-1">Welcome Back</h2>
      <p class="text-center mb-2" style="color: var(--text-secondary)">Sign in to continue to BGA.</p>
      
      <form @submit.prevent="login" class="form-grid">
        <div class="input-group">
          <input v-model="name" placeholder="Username" required />
        </div>
        <div class="input-group">
          <input v-model="password" type="password" placeholder="Password" required />
        </div>
        
        <button type="submit" class="btn-primary w-full mt-1">Sign In</button>
      </form>
      
      <div class="divider"></div>

      <!-- Enlace para ir a la pantalla de registro -->
      <p class="register-link text-center">
        Don't have an account?
        <router-link to="/signup">Create one</router-link>
      </p>
      <p v-if="error" class="error text-center">{{ error }}</p>
    </div>
  </template>
  
  <script setup>
  import { ref } from 'vue'

  const emit = defineEmits(['login-success', 'signup-success'])  
  
  const name = ref('')
  const password = ref('')
  const error = ref('')
  
  const API_BASE = window.location.hostname === 'localhost' 
    ? 'http://localhost:8000' 
    : 'http://backend:8000'
  
  const login = async () => {
    try {
      const loginRes = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: name.value, password: password.value })
      })
      if (!loginRes.ok) throw new Error('Invalid credentials') // More professional message
      const data = await loginRes.json()
      localStorage.setItem('token', data.access_token)
      const meRes = await fetch(`${API_BASE}/auth/me`, {
          headers: { 'Authorization': `Bearer ${data.access_token}` }
      })
      const user = await meRes.json()
      emit('login-success', { token: data.access_token, name: user.name })
      // Removed alert for smoother experience
    } catch (e) {
      error.value = e.message
    }
  }
  </script>
  
  <style scoped>
  .login-container {
    width: 100%;
    max-width: 400px;
    margin: 4rem auto;
  }
  
  .form-grid {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .divider {
    height: 1px;
    background: var(--border-light);
    margin: 1.5rem 0;
  }
  
  .register-link {
    color: var(--text-secondary);
    font-size: 0.9rem;
  }
  
  .error {
    color: #ef4444;
    margin-top: 1rem;
    font-size: 0.9rem;
  }
  </style>
  