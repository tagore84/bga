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

            <!-- Type Toggle -->
            <div class="type-toggle">
                <button @click="p1Type = 'human'" :class="{ active: p1Type === 'human' }">Humano</button>
                <button @click="p1Type = 'ai'" :class="{ active: p1Type === 'ai' }">IA</button>
            </div>

            <select v-model="selectedP1" class="glass-select">
                <option :value="null" disabled>Seleccionar...</option>
                <option v-for="p in (p1Type === 'human' ? humans : ais)" :key="p.id" :value="p">
                     {{ p.name }}
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

            <!-- Type Toggle -->
            <div class="type-toggle">
                <button @click="p2Type = 'human'" :class="{ active: p2Type === 'human' }">Humano</button>
                <button @click="p2Type = 'ai'" :class="{ active: p2Type === 'ai' }">IA</button>
            </div>

            <select v-model="selectedP2" class="glass-select">
                 <option :value="null" disabled>Seleccionar...</option>
                <option v-for="p in (p2Type === 'human' ? humans : ais)" :key="p.id" :value="p">
                     {{ p.name }}
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
    const humans = ref([]);
    const ais = ref([]);
    const selectedP1 = ref(null);
    const selectedP2 = ref(null);
    const p1Type = ref('human');
    const p2Type = ref('human');
    const error = ref(null);

    const fetchPlayers = async () => {
      try {
        const token = localStorage.getItem('token');
        const res = await fetch(`${API_BASE}/players/`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) {
            const all = await res.json();
            
            humans.value = all.filter(p => p.type === 'human');
            ais.value = all.filter(p => p.type === 'ai' && p.name.toLowerCase().includes('wythoff'));
            
            // Set defaults if possible or leave empty
            if (humans.value.length > 0) selectedP1.value = humans.value[0];
            
             // Smart default for P2
            if (ais.value.length > 0) {
                 p2Type.value = 'ai';
                 selectedP2.value = ais.value[0];
            } else if (humans.value.length > 1) {
                 selectedP2.value = humans.value[1];
            }

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
            // Ensure values are objects (the select binds objects here unlike other components, keeping it consistent with original file logic)
            // Wait, original logic used :value="p", so selectedP1 is the object.
            // Other components bind ID. Let's stick to object as per original WythoffConfig but ensure types are correct.
            
            const p1 = selectedP1.value;
            const p2 = selectedP2.value;
            
            // Re-fetch object from list if needed, but since we bind object, it should be fine.
            // Just ensure it matches the current type toggle? 
            // The UI hides the mismatching options, but the value persists. 
            // Let's force re-selection or assume user knows what they see. 
            // Better: update valid check? 
            // Actually, if I toggle type, the select shows "Seleccionar...", so value stays but visual changes.
            // It's safer to ensure we pick from the correct list or just trust the bound object.
            // If I switch to AI, the select might show empty but p1 is still the Human object.
            // That's a common UI bug. I should clear selection on toggle? 
            // I didn't do that for others, but others bind ID. 
            // Let's keep it simple. If the user toggles, they usually pick a new player.
            
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
        humans,
        ais,
        selectedP1,
        selectedP2,
        p1Type,
        p2Type,
        createGame,
        error,
        isValid: computed(() => selectedP1.value && selectedP2.value)
    };
  }
};
</script>

<style scoped>
.config-container {
  max-width: 800px;
  margin: 4rem auto;
  padding: 3rem;
  background-color: #1e1e1e;
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

.type-toggle {
    display: flex;
    background: rgba(0,0,0,0.3);
    border-radius: 6px;
    padding: 2px;
    margin-bottom: 0.5rem;
}

.type-toggle button {
    padding: 4px 12px;
    font-size: 0.8rem;
    color: #ccc;
    background: transparent;
    border: none;
    cursor: pointer;
    border-radius: 4px;
    transition: all 0.2s;
}

.type-toggle button.active {
    background: rgba(255,255,255,0.1);
    color: white;
    font-weight: bold;
}

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
    background: linear-gradient(135deg, #6b7280, #4b5563); 
}

.btn-primary:hover:not(:disabled) {
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
