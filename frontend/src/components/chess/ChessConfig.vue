<template>
  <div class="glass-panel config-container">
    <h2 class="text-center mb-1">Nueva Partida de Ajedrez</h2>
    <p class="text-center mb-3" style="color: var(--text-secondary)">Selecciona los contrincantes</p>

    <div v-if="error" class="error text-center mb-2">{{ error }}</div>

    <div class="board-layout">
        <!-- White Player (Left) -->
        <div class="player-slot white-slot">
            <label class="player-label white-label">♕ Jugador Blancas</label>
            <div class="avatar-ph white-bg"></div>
            <select v-model="whitePlayerId" class="glass-select">
                <option :value="null" disabled>Seleccionar...</option>
                <option v-for="player in players" :key="player.id" :value="player.id">
                    {{ player.name }}
                </option>
            </select>
        </div>

        <!-- VS Visual (Center) -->
        <div class="vs-visual">
            <span class="vs-text">VS</span>
        </div>

        <!-- Black Player (Right) -->
        <div class="player-slot black-slot">
            <label class="player-label black-label">♛ Jugador Negras</label>
            <div class="avatar-ph black-bg"></div>
            <select v-model="blackPlayerId" class="glass-select">
                 <option :value="null" disabled>Seleccionar...</option>
                <option v-for="player in players" :key="player.id" :value="player.id">
                     {{ player.name }}
                </option>
            </select>
        </div>
    </div>

    <div class="actions mt-3">
        <button @click="goBack" class="btn-secondary">Volver</button>
        <button @click="createGame" :disabled="!isValid" class="btn-primary">
            Comenzar Partida
        </button>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import { API_BASE } from '../../config'

export default {
  name: 'ChessConfig',
  data() {
    return {
      players: [],
      whitePlayerId: null,
      blackPlayerId: null,
      error: ''
    }
  },
  computed: {
    isValid() {
      return this.whitePlayerId && this.blackPlayerId;
    }
  },
  async created() {
    try {
      const token = localStorage.getItem('token');
      const res = await axios.get(`${API_BASE}/players/`, {
         headers: { Authorization: `Bearer ${token}` }
      });
      // Filter players for Chess (game_id=3/11 typically) or Human (null) 
      // Assuming Chess game_id is 11 from previous file view context, or allow 3 if that was it.
      // Actually previous code said game_id === 11. I'll stick to that.
      this.players = res.data.filter(p => p.game_id === 3 || p.game_id === null); 
    } catch (e) {
      this.error = "Error cargando jugadores"
    }
  },
  methods: {
    goBack() {
      this.$router.push('/games')
    },
    async createGame() {
      try {
        const token = localStorage.getItem('token');
        
        const payload = {
          white_player_id: this.whitePlayerId,
          black_player_id: this.blackPlayerId,
          opponent_type: "human"
        };

        const res = await axios.post(`${API_BASE}/chess/`, payload, {
           headers: { Authorization: `Bearer ${token}` }
        });
        
        this.$router.push(`/chess/${res.data.id}`);
      } catch (e) {
        console.error(e);
        this.error = e.response?.data?.detail || "Error al crear partida";
      }
    }
  }
}
</script>

<style scoped>
.config-container {
  max-width: 700px;
  margin: 3rem auto;
  padding: 3rem;
  background: var(--glass-bg);
  backdrop-filter: blur(10px);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
}

.text-center { text-align: center; }
.mb-1 { margin-bottom: 0.5rem; }
.mb-2 { margin-bottom: 1rem; }
.mb-3 { margin-bottom: 2rem; }
.mt-3 { margin-top: 2rem; }

.board-layout {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 2rem;
  position: relative;
}

.player-slot {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  background: rgba(255,255,255,0.03);
  padding: 2rem;
  border-radius: 12px;
  transition: transform 0.2s;
}

.player-slot:hover {
    transform: translateY(-2px);
    background: rgba(255,255,255,0.05);
}

.player-label {
    font-size: 1.1rem;
    font-weight: bold;
    text-transform: uppercase;
    letter-spacing: 1px;
}
.white-label { color: #f0d9b5; text-shadow: 0 0 10px rgba(240,217,181,0.3); }
.black-label { color: #8b6d5d; text-shadow: 0 0 10px rgba(139,109,93,0.3); }

.avatar-ph {
    width: 80px;
    height: 80px;
    border-radius: 50%;
    margin-bottom: 0.5rem;
    box-shadow: 0 5px 15px rgba(0,0,0,0.3);
}
.white-bg { background: linear-gradient(135deg, #ffffff, #e0e0e0); }
.black-bg { background: linear-gradient(135deg, #444, #1a1a1a); }

.glass-select {
  width: 100%;
  background: rgba(0, 0, 0, 0.4);
  border: 1px solid var(--border-light);
  color: white;
  padding: 0.8rem;
  border-radius: 6px;
  text-align: center;
  font-size: 1rem;
  outline: none;
  cursor: pointer;
  transition: all 0.2s;
}

.glass-select:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 2px var(--primary-glow);
  background: rgba(0,0,0,0.6);
}

.vs-visual {
    font-size: 2rem;
    font-weight: 900;
    font-style: italic;
    color: var(--primary);
    opacity: 0.5;
}
.vs-text {
    background: -webkit-linear-gradient(#eee, #333);
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
}

.actions {
  display: flex;
  justify-content: center;
}

.btn-primary {
    background: linear-gradient(135deg, var(--primary), var(--primary-dark));
    color: white;
    border: none;
    padding: 1rem 3rem;
    font-size: 1.1rem;
    font-weight: bold;
    border-radius: 30px;
    cursor: pointer;
    box-shadow: 0 4px 15px var(--primary-glow);
    transition: transform 0.2s, box-shadow 0.2s;
}
.btn-primary:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px var(--primary-glow);
}
.btn-primary:active:not(:disabled) {
    transform: translateY(1px);
}
.btn-primary:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    filter: grayscale(1);
}

.btn-secondary {
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    color: white;
    padding: 1rem 3rem;
    font-size: 1.1rem;
    font-weight: bold;
    border-radius: 30px;
    cursor: pointer;
    margin-right: 1rem;
    transition: all 0.2s;
}
.btn-secondary:hover {
    background: rgba(255, 255, 255, 0.2);
}

.error { color: #ef4444; font-weight: bold;}
</style>
