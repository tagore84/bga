import { createRouter, createWebHistory } from 'vue-router'
import LoginForm from './LoginForm.vue'
import SignupForm from './SignupForm.vue'
import GamesList from './GamesList.vue'
import TicTacToe from './components/TicTacToe.vue'
import TicTacToeConfig from './components/TicTacToeConfig.vue'
import ActiveGames from './components/ActiveGames.vue'

const routes = [
  { path: '/', redirect: '/login' },
  { path: '/login', component: LoginForm },
  { path: '/signup', component: SignupForm },
  { path: '/games', component: GamesList, meta: { requiresAuth: true } },
  { path: '/games/:id', component: TicTacToe, meta: { requiresAuth: true } },
  { path: '/configure/tictactoe', component: TicTacToeConfig, meta: { requiresAuth: true } },
  { path: '/:pathMatch(.*)*', redirect: '/login' },
  { path: '/active', component: ActiveGames, meta: { requiresAuth: true } }
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