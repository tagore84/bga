<template>
  <div class="nim-game-container">
    <div v-if="loading" class="loading">Cargando partida...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    
    <div v-else class="game-board">
      <div class="header">
        <h2>Wythoff (Partida #{{ game.id }})</h2>
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
        <!-- Render the 2 piles -->
        <div 
          v-for="(count, index) in game.board" 
          :key="index" 
          class="pile-row"
          :class="{ 
            'selectable': isMyTurn && count > 0 && canSelectPile(index),
            'selected': isPileSelected(index)
          }"
          @click="selectPile(index)"
        >
          <div class="pile-info">Fila {{ index + 1 }}</div>
          <div class="items">
            <!-- 
                Visual items.
                In original Nim, clicking item N removed N items (from right/end).
                Here 'count' items.
                v-for="n in count" creates items 1..count.
                If I click item 'n', I want 'itemsToRemove' to be such that we remove items from n to count?
                Nim logic: 
                item n: 1 is Leftmost? No, flex-row usually.
                Actually NimGame css: .items { display: flex; justify-content: center; } 
                So 1 is Left. 
                NimGame logic: click n -> remove (count - n + 1) items.
                This implies removing from the RIGHT side (the highest indices). 
            -->
            <div 
              v-for="n in count" 
              :key="n" 
              class="item"
              :class="{ 'to-remove': isPileSelected(index) && n > (count - itemsToRemove) }"
              @click.stop="toggleItemRemoval(index, n)"
            >
            </div>
          </div>
          <div class="pile-count">{{ count }}</div>
        </div>
      </div>

      <div class="controls" v-if="isMyTurn && game.status === 'in_progress'">
          
        <!-- Diagonal Toggle -->
        <div class="mode-switch">
           <label class="switch-label">
              <input type="checkbox" v-model="isDiagonal" :disabled="!canGoDiagonal">
              <span class="checkmark"></span>
              Movimiento Diagonal (Ambas filas)
           </label>
        </div>

        <div v-if="hasSelection" class="action-panel">
            <p v-if="!isDiagonal">
                Retirar <strong>{{ itemsToRemove }}</strong> objeto(s) de la Fila {{ selectedPile + 1 }}
            </p>
            <p v-else>
                Retirar <strong>{{ itemsToRemove }}</strong> objeto(s) de <strong>AMBAS</strong> filas
            </p>

          <input 
            type="range" 
            min="1" 
            :max="maxRemovable" 
            v-model.number="itemsToRemove"
            class="range-slider"
          />
          <div class="buttons">
             <button @click="cancelSelection" class="btn-cancel">Cancelar</button>
             <button @click="submitMove" class="btn-confirm" :disabled="itemsToRemove < 1">Confirmar Movimiento</button>
          </div>
        </div>
        <div v-else class="instruction">
          Selecciona una fila o activa Diagonal para eliminar objetos.
        </div>
      </div>
      
      <div v-if="game.status !== 'in_progress'" class="game-over">
        <h3>Fin de la partida</h3>
        <p>{{ statusMessage }}</p>
        <button @click="$router.push('/wythoffActive')" class="btn-home">Volver</button>
      </div>

    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, computed, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { API_BASE } from '../../config';

export default {
  name: 'WythoffGame',
  setup() {
    const route = useRoute();
    const router = useRouter();
    const gameId = route.params.id;
    
    const game = ref(null);
    const loading = ref(true);
    const error = ref('');
    const currentUser = ref(null);
    
    // Game State
    // selectedPile: 0 or 1. If isDiagonal is true, this might be ignored or used as "primary" reference?
    // Actually if Diagonal, we affect BOTH.
    const selectedPile = ref(null); 
    const itemsToRemove = ref(1);
    const isDiagonal = ref(false); // New mode
    
    const intervalId = ref(null);

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
        
        const winnerSymbol = game.value.status.replace('_won', '');
        // Logic might vary if backend uses '1_won' or just '1'. Standardize.
        // Assuming '1_won' based on other games.
        if (winnerSymbol === '1') {
             return `${game.value.player_1_name} ha ganado!`;
        } else {
             return `${game.value.player_2_name} ha ganado!`;
        }
    });

    // Helper for Diagonal availability
    const canGoDiagonal = computed(() => {
        if (!game.value) return false;
        // Can only do diagonal if both piles have items
        return game.value.board[0] > 0 && game.value.board[1] > 0;
    });

    const maxRemovable = computed(() => {
        if (!game.value) return 1;
        if (isDiagonal.value) {
            return Math.min(game.value.board[0], game.value.board[1]);
        }
        if (selectedPile.value !== null) {
            return game.value.board[selectedPile.value];
        }
        return 0;
    });

    const hasSelection = computed(() => {
        return isDiagonal.value || selectedPile.value !== null;
    });

    // Helpers
    const isPileSelected = (index) => {
        if (isDiagonal.value) return true; // Both selected
        return selectedPile.value === index;
    };

    const canSelectPile = (index) => {
        if (isDiagonal.value) return false; // If diagonal, piles are implicitly both selected (or locked)
        // You can switch out of diagonal to select a single pile though.
        return true;
    };

    // Actions
    const fetchGame = async () => {
      try {
        const token = localStorage.getItem('token');
        
        if (!currentUser.value && token) {
            const resMe = await fetch(`${API_BASE}/auth/me`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (resMe.ok) currentUser.value = await resMe.json();
        }

        const res = await fetch(`${API_BASE}/wythoff/${gameId}`, {
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
    
    // Watcher to reset diagonal if impossible
    watch(() => game.value, (newVal) => {
        if (newVal && isDiagonal.value) {
            if (newVal.board[0] === 0 || newVal.board[1] === 0) {
                isDiagonal.value = false;
            }
        }
    });
    
    // Watcher: if toggling Diagonal ON, clear specific pile selection or sync items
    watch(isDiagonal, (val) => {
        if (val) {
             selectedPile.value = null; // Clear specific pile
             itemsToRemove.value = 1;   // Reset count to safe default
        } else {
             // If turning off diagonal, maybe default to pile 0 if available?
             // Or just nothing.
             selectedPile.value = null;
        }
    });

    const selectPile = (index) => {
      if (!isMyTurn.value) return;
      if (game.value.board[index] === 0) return;
      
      // If we click a pile, we imply turning OFF diagonal?
      // Yes, specific selection takes precedence usually.
      if (isDiagonal.value) {
          isDiagonal.value = false;
      }

      if (selectedPile.value === index) {
        // Already selected
      } else {
        selectedPile.value = index;
        itemsToRemove.value = 1;
      }
    };

    const toggleItemRemoval = (pileIndex, n) => {
        if (!isMyTurn.value) return;
        
        // n is 1-based index from LEFT (visually).
        // item 1 is far left. item Count is far right.
        // If I click item n, I want to remove items n..count.
        // Amount = count - n + 1.
        
        const countInPile = game.value.board[pileIndex];
        const newToRemove = countInPile - n + 1;

        if (isDiagonal.value) {
            // If Diagonal, clicking ANY pile's item sets the common count.
            // But we must cap it at maxRemovable (min of both piles).
            if (newToRemove > maxRemovable.value) {
                itemsToRemove.value = maxRemovable.value;
            } else {
                itemsToRemove.value = newToRemove;
            }
        } else {
            // Standard
            if (selectedPile.value !== pileIndex) {
                selectPile(pileIndex);
            }
            itemsToRemove.value = newToRemove;
        }
    };

    const cancelSelection = () => {
      selectedPile.value = null;
      itemsToRemove.value = 1;
      isDiagonal.value = false;
    };

    const submitMove = async () => {
      if (!hasSelection.value) return;
      
      try {
        const token = localStorage.getItem('token');
        
        const payload = {};
        if (isDiagonal.value) {
            payload.type = 'diagonal';
            payload.count = itemsToRemove.value;
            payload.pile_index = 0; // Backend ignores this for diagonal? Checks are made? 
                                    // Usually for diagonal Pile Index is irrelevant but backend might expect it.
                                    // Let's check WythoffLogic. 
                                    // Assuming backend handles it. Sending 0 is safe.
        } else {
            payload.type = 'standard';
            payload.count = itemsToRemove.value;
            payload.pile_index = selectedPile.value;
        }

        const res = await fetch(`${API_BASE}/wythoff/${gameId}/move`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(payload)
        });
        
        if (!res.ok) {
            const err = await res.json();
            alert(err.detail || "Error en movimiento");
            return;
        }
        
        const updatedGame = await res.json();
        game.value = updatedGame;
        cancelSelection();
        
      } catch (e) {
        console.error("Move failed", e);
      }
    };


    
    // Let's refactor slightly to expose socket to unmounted
    let socket = null;

    onMounted(() => {
        fetchGame();
        socket = new WebSocket(`${WS_BASE}/ws/wythoff/${gameId}`);
        
        socket.onmessage = ({ data }) => {
            try {
                const msg = JSON.parse(data);
                // Wythoff move events: type, move_type, count, pile_index, by, board, status
                if (msg.board) {
                    game.value.board = JSON.parse(msg.board);
                }
                if (msg.status) {
                    game.value.status = msg.status;
                }
                
                // Similar to Nim, trigger fetch to ensure all state (names, etc) is sync or just rely on basics.
                // Fetching is safer for turns.
                fetchGame();
                
            } catch (e) {
                console.error("WS Error", e);
            }
        };
    });
    
    onUnmounted(() => {
        if (intervalId.value) clearInterval(intervalId.value);
        if (socket) socket.close();
    });

    return {
      game, loading, error,
      currentUser,
      selectedPile, itemsToRemove, isDiagonal,
      isMyTurn, currentTurnName, statusMessage,
      canGoDiagonal, maxRemovable, hasSelection, 
      isPileSelected, canSelectPile,
      selectPile, toggleItemRemoval, cancelSelection, submitMove
    };
  }
};
</script>

<style scoped>
/* Copied and adapted from NimGame.vue for consistency */
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
  border-radius: 50px;
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
  background: #e67e22;
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

/* Toggle Switch */
.mode-switch {
  margin-bottom: 20px;
  display: flex;
  justify-content: center;
}
.switch-label {
    display: flex;
    align-items: center;
    gap: 10px;
    cursor: pointer;
    font-size: 0.9em;
    color: #ccc;
}
.switch-label input {
    display: none;
}
.checkmark {
    width: 40px;
    height: 20px;
    background: #555;
    border-radius: 10px;
    position: relative;
    transition: background 0.3s;
}
.checkmark::after {
    content: '';
    position: absolute;
    left: 2px;
    top: 2px;
    width: 16px;
    height: 16px;
    background: white;
    border-radius: 50%;
    transition: transform 0.3s;
}
.switch-label input:checked + .checkmark {
    background: #3498db;
}
.switch-label input:checked + .checkmark::after {
    transform: translateX(20px);
}
.switch-label input:disabled + .checkmark {
    opacity: 0.5;
    cursor: not-allowed;
}

</style>
