<template>
  <div class="modal-overlay">
    <div class="glass-panel modal-content">
      <h2 class="modal-title">Game Over</h2>
      
      <div class="winner-section mb-2" v-if="winner">
        <div class="trophy">🏆</div>
        <h3>{{ winner.name }} Wins!</h3>
        <p class="final-score">{{ winner.puntos }} Points</p>
      </div>

      <div class="scores-list mb-2">
        <div 
          v-for="(player, index) in sortedPlayers" 
          :key="player.id"
          class="score-row"
          :class="{ 'is-winner': index === 0 }"
        >
          <div class="player-rank">#{{ index + 1 }}</div>
          <div class="player-info">
            <span class="player-name">{{ player.name || 'Player ' + player.id }}</span>
            <span v-if="player.isMe" class="me-badge">(YOU)</span>
          </div>
          <div class="player-points">{{ player.puntos }} pts</div>
        </div>
      </div>

      <div class="actions">
        <button @click="$emit('home')" class="btn-primary w-full">
          Back to Menu
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  players: {
    type: Object, // Dict of players from gameState
    required: true
  },
  me: {
    type: String,
    required: true
  }
})

defineEmits(['home'])

const sortedPlayers = computed(() => {
  return Object.values(props.players)
    .map(p => ({
      ...p,
      isMe: p.name === props.me || p.id === props.me
    }))
    .sort((a, b) => b.puntos - a.puntos)
})

const winner = computed(() => sortedPlayers.value[0])
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(15, 23, 42, 0.8); /* Darkened bg */
  backdrop-filter: blur(8px);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: fadeIn 0.5s ease-out;
}

.modal-content {
  width: 100%;
  max-width: 450px;
  text-align: center;
  animation: slideUp 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
  border: 1px solid var(--border-glow);
  box-shadow: 0 0 40px rgba(59, 130, 246, 0.2);
}

.modal-title {
  font-size: 2.5rem;
  background: var(--gradient-main);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin-bottom: 2rem;
  letter-spacing: -0.05em;
}

.winner-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 2rem;
}

.trophy {
  font-size: 4rem;
  margin-bottom: 0.5rem;
  filter: drop-shadow(0 0 20px rgba(255, 215, 0, 0.3));
  animation: float 3s ease-in-out infinite;
}

.final-score {
  font-size: 1.5rem;
  color: var(--accent);
  font-weight: 700;
}

.scores-list {
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
}

.score-row {
  display: flex;
  align-items: center;
  padding: 1rem;
  background: rgba(255, 255, 255, 0.03);
  border-radius: var(--radius-sm);
  border: 1px solid transparent;
  transition: all 0.2s;
}

.score-row.is-winner {
  background: rgba(255, 215, 0, 0.1);
  border-color: rgba(255, 215, 0, 0.3);
}

.player-rank {
  font-weight: 700;
  margin-right: 1rem;
  color: var(--text-secondary);
  width: 1.5rem;
}

.is-winner .player-rank {
  color: #ffd700;
}

.player-info {
  flex: 1;
  text-align: left;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.player-name {
  font-weight: 500;
}

.me-badge {
  font-size: 0.7rem;
  background: var(--primary);
  padding: 0.1rem 0.4rem;
  border-radius: 4px;
  color: white;
}

.player-points {
  font-weight: 700;
  font-size: 1.1rem;
}

.actions {
  margin-top: 2rem;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideUp {
  from { transform: translateY(50px) scale(0.9); opacity: 0; }
  to { transform: translateY(0) scale(1); opacity: 1; }
}

@keyframes float {
  0% { transform: translateY(0px); }
  50% { transform: translateY(-10px); }
  100% { transform: translateY(0px); }
}
</style>
