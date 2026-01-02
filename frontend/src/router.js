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
import ChessConfig from './components/chess/ChessConfig.vue'
import ChessActiveGames from './components/chess/ChessActiveGames.vue'
import ChessGame from './components/chess/ChessGame.vue';

// Nim Components
import NimActiveGames from './components/nim/NimActiveGames.vue';
import NimConfig from './components/nim/NimConfig.vue';
import NimGame from './components/nim/NimGame.vue';
import WythoffActiveGames from './components/wythoff/WythoffActiveGames.vue';
import WythoffConfig from './components/wythoff/WythoffConfig.vue';
import WythoffGame from './components/wythoff/WythoffGame.vue';
import Connect4Config from './components/connect4/Connect4Config.vue'
import Connect4ActiveGames from './components/connect4/Connect4ActiveGames.vue'
import Connect4Game from './components/connect4/Connect4Game.vue'
import SantoriniActiveGames from './components/santorini/SantoriniActiveGames.vue'
import SantoriniConfig from './components/santorini/SantoriniConfig.vue'
import SantoriniGame from './components/santorini/SantoriniGame.vue'
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
  { path: '/chessConfig', component: ChessConfig, meta: { requiresAuth: true } },
  { path: '/chessActive', component: ChessActiveGames, meta: { requiresAuth: true } },
  { path: '/chess/:id', component: ChessGame, meta: { requiresAuth: true } },

  // Nim Routes
  { path: '/nimActive', component: NimActiveGames, meta: { requiresAuth: true } },
  { path: '/nimConfig', component: NimConfig, meta: { requiresAuth: true } },
  { path: '/nim/:id', component: NimGame, meta: { requiresAuth: true } },

  // Wythoff Routes
  { path: '/wythoffActive', component: WythoffActiveGames, meta: { requiresAuth: true } },
  { path: '/wythoffConfig', component: WythoffConfig, meta: { requiresAuth: true } },
  { path: '/wythoff/:id', component: WythoffGame, meta: { requiresAuth: true } },
  { path: '/connect4Config', component: Connect4Config, meta: { requiresAuth: true } },
  { path: '/connect4Active', component: Connect4ActiveGames, meta: { requiresAuth: true } },
  { path: '/connect4/:id', component: Connect4Game, meta: { requiresAuth: true } },

  // Santorini Routes
  { path: '/santoriniActive', component: SantoriniActiveGames, meta: { requiresAuth: true } },
  { path: '/santoriniConfig', component: SantoriniConfig, meta: { requiresAuth: true } },
  { path: '/santorini/:id', component: SantoriniGame, meta: { requiresAuth: true } },

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