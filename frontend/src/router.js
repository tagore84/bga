// frontend/src/router.js
import { createRouter, createWebHistory } from 'vue-router'
import LoginForm from './LoginForm.vue'
import SignupForm from './SignupForm.vue'
import GamesList from './GamesList.vue'
import TicTacToe from './components/tictactoe/TicTacToe.vue'
import TicTacToeConfig from './components/tictactoe/TicTacToeConfig.vue'
import AzulConfig from './components/azul/AzulConfig.vue'
import TicTacToeActiveGames from './components/tictactoe/TicTacToeActiveGames.vue'
import AzulActiveGames from './components/azul/AzulActiveGames.vue'
import AzulGame from './components/azul/AzulGame.vue'
import ErrorPage from './Error.vue'

const routes = [
  { path: '/', redirect: '/login' },
  { path: '/login', component: LoginForm },
  { path: '/signup', component: SignupForm },
  { path: '/games', component: GamesList, meta: { requiresAuth: true } },
  { path: '/tictactoe/:id', component: TicTacToe, meta: { requiresAuth: true } },
  { path: '/tictactoeActive', component: TicTacToeActiveGames, meta: { requiresAuth: true } },
  { path: '/tictactoeConfig', component: TicTacToeConfig, meta: { requiresAuth: true } },
  { path: '/azulConfig', component: AzulConfig, meta: { requiresAuth: true } },
  { path: '/azulActive', component: AzulActiveGames, meta: { requiresAuth: true } },
  { path: '/azul/:id', component: AzulGame, meta: { requiresAuth: true } },
  { path: '/error', component: ErrorPage },
  { path: '/:pathMatch(.*)*', redirect: '/error' }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.meta.requiresAuth && !token) {
    next('/login')
  } else {
    next()
  }
})

export default router