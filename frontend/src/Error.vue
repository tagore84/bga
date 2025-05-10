<template>
  <div class="error-page">
    <h1>Error 404</h1>
    <p>La página que buscas no existe o ha ocurrido un error.</p>
    <router-link to="/games">Volver al inicio</router-link>
  </div>
</template>

<script>
export default {
  name: 'ErrorPage'
}
</script>

<style scoped>
.error-page {
  text-align: center;
  margin-top: 50px;
}
.error-page h1 {
  font-size: 3em;
  color: red;
}
</style>
