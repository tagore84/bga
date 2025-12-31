<template>
  <div class="nim-game-container">
    <div v-if="loading" class="loading">Cargando partida...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    
    <div v-else class="game-board">
      <div class="header">
        <h2>Nim Misere (Partida #{{ game.id }})</h2>
        <div class="status-bar">
          <span :class="{ 'active-turn': isMyTurn }">
            Turno: {{ currentTurnName }} 
            <span v-if="isMyTurn">(Te toca)</span>
          </span>
          <span class="game-status" v-if="game.status !== 'in_progress'">
            {{ statusMessage }}
          </span>
        </div>
      </div>

      <div class="piles-container">
        <div 
          v-for="(count, index) in game.board" 
          :key="index" 
          class="pile-row"
          :class="{ 
            'selectable': isMyTurn && (selectedPile === null || selectedPile === index) && count > 0,
            'selected': selectedPile === index 
          }"
          @click="selectPile(index)"
        >
          <div class="pile-info">Fila {{ index + 1 }}</div>
          <div class="items">
            <!-- Render items as visual elements -->
             <!-- If selected, we can show selection UI locally or just click items to augment count -->
             <!-- Simplified Interaction: 
                  1. Click Row -> Selects Row.
                  2. Input Number to remove OR Click individual items to toggle removal.
                  Let's do click items to mark for removal.
              -->
            <div 
              v-for="n in count" 
              :key="n" 
              class="item"
              :class="{ 'to-remove': selectedPile === index && n > (count - itemsToRemove) }"
              @click.stop="toggleItemRemoval(index, n)"
            >
            </div>
          </div>
          <div class="pile-count">{{ count }}</div>
        </div>
      </div>

      <div class="controls" v-if="isMyTurn && game.status === 'in_progress'">
        <div v-if="selectedPile !== null" class="action-panel">
          <p>Retirar <strong>{{ itemsToRemove }}</strong> objeto(s) de la Fila {{ selectedPile + 1 }}</p>
          <input 
            type="range" 
            min="1" 
            :max="game.board[selectedPile]" 
            v-model.number="itemsToRemove"
            class="range-slider"
          />
          <div class="buttons">
             <button @click="cancelSelection" class="btn-cancel">Cancelar</button>
             <button @click="submitMove" class="btn-confirm" :disabled="itemsToRemove < 1">Confirmar Movimiento</button>
          </div>
        </div>
        <div v-else class="instruction">
          Selecciona una fila para eliminar objetos.
        </div>
      </div>
      
      <div v-if="game.status !== 'in_progress'" class="game-over">
        <h3>Fin de la partida</h3>
        <p>{{ statusMessage }}</p>
        <button @click="$router.push('/nimActive')" class="btn-home">Volver</button>
      </div>

    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, computed, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { API_BASE, WS_BASE } from '../../config';

export default {
  name: 'NimGame',
  setup() {
    const route = useRoute();
    const router = useRouter();
    const gameId = route.params.id;
    
    const game = ref(null);
    const loading = ref(true);
    const error = ref('');
    const currentUser = ref(null);
    
    // Game State
    const selectedPile = ref(null);
    const itemsToRemove = ref(1);
    
    // WebSocket
    let socket = null;

    // Computed
    const isPlayer1 = computed(() => currentUser.value?.id === game.value?.config?.player1Id);
    const isPlayer2 = computed(() => currentUser.value?.id === game.value?.config?.player2Id);
    
    const currentTurnName = computed(() => {
      if (!game.value) return '';
      if (game.value.current_turn === '1') return game.value.player_1_name || 'Jugador 1';
      return game.value.player_2_name || 'Jugador 2';
    });
    
    const isMyTurn = computed(() => {
      if (!game.value || !currentUser.value) return false;
      if (game.value.status !== 'in_progress') return false;
      
      const mySymbol = isPlayer1.value ? '1' : (isPlayer2.value ? '2' : null);
      return game.value.current_turn === mySymbol;
    });

    const statusMessage = computed(() => {
        if (!game.value) return '';
        if (game.value.status === 'in_progress') return 'En curso';
        
        // "1_won" or "2_won"
        const winnerSymbol = game.value.status.replace('_won', '');
        const winnerName = winnerSymbol === '1' ? game.value.player_1_name : game.value.player_2_name;
        
        // Misere logic check: 
        // Backend says WHO WON. 
        // "1_won" means Player 1 won.
        
        if (winnerSymbol === '1') {
             return `${game.value.player_1_name} ha ganado!`;
        } else {
             return `${game.value.player_2_name} ha ganado!`;
        }
    });

    // Actions
    const fetchGame = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) { 
           // try fetch without auth if spectator? But we need auth usually.
        }
        
        // Get User first
        if (!currentUser.value && token) {
            const resMe = await fetch(`${API_BASE}/auth/me`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (resMe.ok) currentUser.value = await resMe.json();
        }

        const res = await fetch(`${API_BASE}/nim/${gameId}`, {
             headers: token ? { 'Authorization': `Bearer ${token}` } : {}
        });
        if (!res.ok) throw new Error("No se pudo cargar la partida");
        game.value = await res.json();
        loading.value = false;
        
      } catch (e) {
        error.value = e.message;
        loading.value = false;
      }
    };
    
    onMounted(() => {
        fetchGame();
        
        // Initialize WebSocket
        socket = new WebSocket(`${WS_BASE}/ws/nim/${gameId}`);
        
        socket.onmessage = ({ data }) => {
            try {
                const msg = JSON.parse(data);
                
                // If it's a move/update, we could either re-fetch or trust the payload
                // The backend sends full board and status in payload for moves
                if (msg.board) {
                    game.value.board = JSON.parse(msg.board);
                }
                if (msg.status) {
                    game.value.status = msg.status;
                }
                if (msg.current_turn) {
                    game.value.current_turn = msg.current_turn; 
                    // Note: backend msg usually relies on "by" field or status to imply turn, 
                    // or we should ensure backend sends current_turn.
                    // Nim backend 'move' event sends: pile_index, count, by, board, status.
                    // It does NOT send current_turn explicitly in the redis message in nim.py?
                    // Let's check nim.py: 
                    // "by": game.current_turn if status_val != "in_progress" else ...
                    // It doesn't send 'current_turn'.
                    // So we might need to re-fetch OR deduce. 
                    // To be safe and simple: fetchGame() on any move event.
                    fetchGame();
                } else {
                    // Fallback if we just want to trigger refresh
                    fetchGame();
                }
                
            } catch (e) {
                console.error("WS Error", e);
            }
        };
    });

    onUnmounted(() => {
        if (socket) {
            socket.close();
        }
    });

    const selectPile = (index) => {
      if (!isMyTurn.value) return;
      if (game.value.board[index] === 0) return;
      
      if (selectedPile.value === index) {
        // Deselect? No, just keep selected.
      } else {
        selectedPile.value = index;
        itemsToRemove.value = 1;
      }
    };

    const toggleItemRemoval = (pileIndex, n) => {
        if (!isMyTurn.value) return;
        
        // If clicking a different pile, switch selection
        if (selectedPile.value !== pileIndex) {
            selectPile(pileIndex);
        }
        
        // Calculate items to remove based on clicking item 'n' (1-based index)
        // User intention: Click item N means "Remove N and everything to its right"
        // Wait, visually usually we remove from the end.
        // If items are 1, 2, 3, 4, 5.
        // If I click 4, I want to remove 4 and 5? That is 2 items.
        // Formula: count - n + 1
        const count = game.value.board[pileIndex];
        const newToRemove = count - n + 1;
        
        itemsToRemove.value = newToRemove;
    };

    const cancelSelection = () => {
      selectedPile.value = null;
      itemsToRemove.value = 1;
    };

    const submitMove = async () => {
      if (selectedPile.value === null) return;
      
      try {
        const token = localStorage.getItem('token');
        const res = await fetch(`${API_BASE}/nim/${gameId}/move`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                pile_index: selectedPile.value,
                count: itemsToRemove.value
            })
        });
        
        if (!res.ok) {
            const err = await res.json();
            alert(err.detail);
            return;
        }
        
        // Update local state immediately
        const updatedGame = await res.json();
        game.value = updatedGame;
        cancelSelection();
        
      } catch (e) {
        console.error("Move failed", e);
      }
    };

    return {
      game, loading, error,
      currentUser,
      selectedPile, itemsToRemove,
      isMyTurn, currentTurnName, statusMessage,
      selectPile, toggleItemRemoval, cancelSelection, submitMove
    };
  }
};
</script>

<style scoped>
.nim-game-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
  color: #fff;
}
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #444;
  padding-bottom: 20px;
  margin-bottom: 30px;
}
.active-turn {
  color: #4CAF50;
  font-weight: bold;
}
.game-status {
  margin-left: 20px;
  padding: 5px 10px;
  background: #34495e;
  border-radius: 4px;
}

/* Board & Piles */
.piles-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
  align-items: center;
}
.pile-row {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 10px 20px;
  background: #222;
  border-radius: 50px; /* Pill shape for row */
  transition: all 0.3s;
  border: 2px solid transparent;
  width: 80%;
  justify-content: space-between;
}
.pile-row.selectable:hover {
  background: #333;
  cursor: pointer;
  border-color: #555;
}
.pile-row.selected {
  border-color: #3498db;
  background: #2c3e50;
}

.pile-info {
  font-size: 0.9em;
  color: #888;
  width: 60px;
}
.items {
  display: flex;
  gap: 10px;
  flex-grow: 1;
  justify-content: center;
}
.item {
  width: 20px;
  height: 40px;
  background: #e67e22; /* Objects look like sticks or stones */
  border-radius: 4px;
  box-shadow: 0 2px 5px rgba(0,0,0,0.5);
  transition: all 0.2s;
  cursor: pointer;
}
.item:hover {
  filter: brightness(1.2);
}
.item.to-remove {
  opacity: 0.3;
  background: #c0392b;
  transform: scale(0.9);
}

.pile-count {
  font-weight: bold;
  font-size: 1.2em;
  width: 30px;
  text-align: right;
}

/* Controls */
.controls {
  margin-top: 40px;
  background: #252525;
  padding: 20px;
  border-radius: 8px;
  text-align: center;
}
.instruction {
  color: #aaa;
}
.action-panel {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
}
.range-slider {
  width: 100%;
  max-width: 300px;
}
.buttons {
  display: flex;
  gap: 10px;
}
.btn-cancel {
  background: transparent;
  border: 1px solid #666;
  color: #ccc;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}
.btn-confirm {
  background: #2ecc71;
  border: none;
  color: white;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}
.btn-confirm:disabled {
  background: #555;
  cursor: not-allowed;
}

.game-over {
  text-align: center;
  margin-top: 50px;
  padding: 30px;
  background: rgba(46, 204, 113, 0.1);
  border-radius: 12px;
}
.btn-home {
  margin-top: 20px;
  padding: 10px 20px;
  background: #3498db;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
</style>
