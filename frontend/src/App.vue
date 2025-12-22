<template>
  <router-view v-slot="{ Component }">
    <component
      :is="Component"
      @login-success="onLoginSuccess"
      @signup-success="onLoginSuccess"
    />
  </router-view>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const token = ref('')
const username = ref('')

function onLoginSuccess({ token: t, username: u }) {
  token.value = t
  username.value = u
  localStorage.setItem('token', t)
  router.push('/games')
}
</script>

<style>
/* Global styles are now in style.css */
</style>

