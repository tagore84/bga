<template>
  <div class="glass-panel config-container">
    <h2 class="text-center mb-1 text-3xl font-bold text-white">Nueva Partida de Wythoff Nim</h2>
    <p class="text-center mb-3" style="color: var(--text-secondary)">Selecciona los contrincantes</p>

    <div v-if="error" class="error text-center mb-2">{{ error }}</div>

    <div class="board-layout">
        <!-- Player 1 (Left) -->
        <div class="player-slot p1-slot">
            <label class="player-label p1-label">👤 Jugador 1</label>
            <div class="avatar-ph p1-bg"></div>
            <select v-model="selectedP1" class="glass-select">
                <option :value="null" disabled>Seleccionar...</option>
                <option v-for="p in availablePlayers1" :key="p.id" :value="p">
                     {{ p.name }} ({{ p.type === 'ai' ? 'IA' : 'Humano' }})
                </option>
            </select>
        </div>

        <!-- VS Visual (Center) -->
        <div class="vs-visual">
            <span class="vs-text">VS</span>
        </div>

        <!-- Player 2 (Right) -->
        <div class="player-slot p2-slot">
            <label class="player-label p2-label">👤 Jugador 2</label>
            <div class="avatar-ph p2-bg"></div>
            <select v-model="selectedP2" class="glass-select">
                 <option :value="null" disabled>Seleccionar...</option>
                <option v-for="p in availablePlayers2" :key="p.id" :value="p">
                     {{ p.name }} ({{ p.type === 'ai' ? 'IA' : 'Humano' }})
                </option>
            </select>
        </div>
    </div>

    <div class="actions mt-24 flex justify-between gap-4">
        <button @click="$router.push('/wythoffActive')" class="btn-secondary">Volver</button>
        <button @click="createGame" :disabled="!isValid" class="btn-primary">
            Comenzar Partida
        </button>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { API_BASE } from '../../config';

export default {
  setup() {
    const router = useRouter();
    const players = ref([]);
    const selectedP1 = ref(null);
    const selectedP2 = ref(null);
    const error = ref(null);

    const fetchPlayers = async () => {
      try {
        const token = localStorage.getItem('token');
        const res = await fetch(`${API_BASE}/players/`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) {
            const all = await res.json();
            // Filter: Humans + Wythoff AI
            players.value = all.filter(p => {
                if (p.type === 'human') return true;
                if (p.type === 'ai') {
                    return p.name.toLowerCase().includes('wythoff');
                }
                return false;
            });
            
            // Avoid null defaults to match "Seleccionar..." appearance if desired, 
            // OR set defaults like Nim? Nim defaults to null?
            // "Seleccionar..." option is provided, so let's default to null or try to pick smart.
            // Nim config usually forces selection.
             const humans = players.value.filter(p => p.type === 'human');
            if (humans.length > 0) selectedP1.value = humans[0];
            
            const ais = players.value.filter(p => p.type === 'ai');
            if (ais.length > 0) selectedP2.value = ais[0];
            else if (humans.length > 1) selectedP2.value = humans[1];

        }
      } catch (e) {
        console.error(e);
        error.value = "Error cargando jugadores";
      }
    };

    const createGame = async () => {
        try {
            const token = localStorage.getItem('token');
            const dateStr = new Date().toLocaleTimeString();
            // Ensure values are objects
            const p1 = selectedP1.value;
            const p2 = selectedP2.value;
            
            const gameName = `Wythoff ${p1.name} vs ${p2.name} (${dateStr})`;
            
            const payload = {
                game_name: gameName,
                player1Type: p1.type,
                player1Id: p1.id,
                player2Type: p2.type,
                player2Id: p2.id
            };
            
            const res = await fetch(`${API_BASE}/wythoff/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(payload)
            });
            
            if (res.ok) {
                const game = await res.json();
                router.push(`/wythoff/${game.id}`);
            } else {
                error.value = "Error al crear la partida";
            }
        } catch (e) {
            console.error(e);
            error.value = e.message;
        }
    };

    onMounted(fetchPlayers);

    return {
        availablePlayers1: players,
        availablePlayers2: players,
        selectedP1,
        selectedP2,
        createGame,
        error,
        isValid: computed(() => selectedP1.value && selectedP2.value)
    };
  }
};
</script>

<style scoped>
.config-container {
  max-width: 800px; /* Slightly wider than Nim */
  margin: 4rem auto;
  padding: 3rem;
  background-color: #1e1e1e; /* Fallback */
  background: linear-gradient(145deg, #1e1e1e, #2a2a2a);
  border: 1px solid #444;
  border-radius: 16px;
  color: white;
  box-shadow: 0 10px 30px rgba(0,0,0,0.5);
}

.board-layout {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 2rem;
  margin-top: 2rem;
}

@media (max-width: 768px) {
    .board-layout {
        flex-direction: column;
    }
}

.player-slot {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.5rem;
  background: rgba(255,255,255,0.03);
  padding: 2.5rem;
  border-radius: 16px;
  transition: transform 0.2s, background 0.2s;
  min-width: 250px;
}

.player-slot:hover {
    transform: translateY(-5px);
    background: rgba(255,255,255,0.06);
    box-shadow: 0 5px 15px rgba(0,0,0,0.2);
}

.player-label {
    font-size: 1.1rem;
    font-weight: bold;
    text-transform: uppercase;
    letter-spacing: 1px;
}
.p1-label { color: #f1c40f; text-shadow: 0 0 10px rgba(241, 196, 15, 0.3); } /* Yellow */
.p2-label { color: #9b59b6; text-shadow: 0 0 10px rgba(155, 89, 182, 0.3); } /* Purple */

.avatar-ph {
    width: 100px;
    height: 100px;
    border-radius: 50%;
    margin-bottom: 0.5rem;
    box-shadow: 0 8px 20px rgba(0,0,0,0.4);
}
.p1-bg { background: linear-gradient(135deg, #f1c40f, #d35400); }
.p2-bg { background: linear-gradient(135deg, #9b59b6, #8e44ad); }

.glass-select {
  width: 100%;
  background: rgba(0, 0, 0, 0.6);
  border: 1px solid #555;
  color: white;
  padding: 1rem;
  border-radius: 8px;
  text-align: center;
  font-size: 1rem;
  outline: none;
  cursor: pointer;
  transition: all 0.2s;
}

.glass-select:focus {
  border-color: #3498db;
  box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.3);
  background: rgba(0,0,0,0.8);
}

.vs-visual {
    font-size: 2.5rem;
    font-weight: 900;
    font-style: italic;
    color: #555;
    opacity: 0.6;
}

.btn-primary {
    background: linear-gradient(135deg, #6b7280, #4b5563);
    color: white;
    border: none;
    padding: 1rem 2.5rem;
    font-size: 1.1rem;
    font-weight: bold;
    border-radius: 9999px; /* Pill */
    cursor: pointer;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    transition: all 0.2s;
}
.btn-primary:not(:disabled) {
    background: linear-gradient(135deg, #6b7280, #4b5563); /* Keep greyish or make pop? User screenshot had grey buttons */
}
/* Wait, screenshot shows Start Button as Grey? Or Blue/Purple? 
   The uploaded image 1767146029496 is "Comenzar Partida" in grey.
   Let's match that.
*/
.btn-primary:hover:not(:disabled) {
    background: linear-gradient(135deg, #7f1d1d, #b91c1c); /* Maybe keep consistent with other games? No, match screenshots. */
     background: linear-gradient(135deg, #4b5563, #374151);
     transform: translateY(-2px);
}
.btn-primary:active:not(:disabled) {
    transform: translateY(1px);
}
.btn-primary:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.btn-secondary {
    background: transparent;
    border: 1px solid rgba(255, 255, 255, 0.3);
    color: white;
    padding: 1rem 2.5rem;
    font-size: 1.1rem;
    font-weight: bold;
    border-radius: 9999px;
    cursor: pointer;
    transition: all 0.2s;
}
.btn-secondary:hover {
    background: rgba(255, 255, 255, 0.1);
    border-color: rgba(255, 255, 255, 0.5);
}

.error { color: #ef4444; font-weight: bold;}
</style>
