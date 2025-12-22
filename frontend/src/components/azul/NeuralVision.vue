<template>
  <div v-if="!minimized" class="neural-vision-overlay">
    <div class="neural-vision-modal">
      <div class="header-row">
          <h2>Neural Vision: DeepMCTSPlayer Analysis</h2>
          <div class="header-controls">
              <button @click="minimized = true" class="minimize-btn">👁️ View Board</button>
          </div>
      </div>
      
      <div v-if="data" class="vision-content">
        <div class="network-choice">
            <h3>Predicted Value: {{ data.network_choice.value_pred.toFixed(3) }}</h3>
            
            <div class="choice-row">
                <div class="choice-item filtered">
                    <span class="choice-label">✅ Best Legal Move:</span>
                    <strong class="choice-val">{{ data.network_choice.masked.action_desc }}</strong>
                    <small>(Index: {{ data.network_choice.masked.action_idx }})</small>
                </div>
                
                <div class="choice-item raw">
                    <span class="choice-label">🧠 Raw Network Instinct:</span>
                    <span class="choice-val">{{ data.network_choice.raw.action_desc }}</span>
                    <small>(Index: {{ data.network_choice.raw.action_idx }})</small>
                </div>
            </div>
        </div>
        
        <div class="saliency-sections">
            <!-- Spatial: 5x5 grid(s) -->
            <div class="section spatial">
                <h4>Spatial Attention</h4>
                <div class="spatial-grids-container">
                    <template v-if="data.saliency.spatial_breakdown && data.saliency.spatial_breakdown.length > 0">
                        <div v-for="(item, idx) in data.saliency.spatial_breakdown" :key="idx" class="spatial-item">
                            <h5>{{ item.label }}</h5>
                            <div class="heatmap-grid">
                                <div v-for="(row, r) in item.map" :key="r" class="heatmap-row">
                                    <div v-for="(val, c) in row" :key="c" 
                                         class="heatmap-cell"
                                         :style="{ backgroundColor: `rgba(255, 0, 0, ${val})` }"
                                         :title="`${item.label} (${r},${c}): ${val.toFixed(2)}`">
                                         {{ val.toFixed(1) }}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </template>
                    <template v-else>
                        <!-- Legacy Single Map -->
                         <h5>Board (Combined)</h5>
                         <div class="heatmap-grid">
                            <div v-for="(row, r) in data.saliency.spatial" :key="r" class="heatmap-row">
                                <div v-for="(val, c) in row" :key="c" 
                                     class="heatmap-cell"
                                     :style="{ backgroundColor: `rgba(255, 0, 0, ${val})` }"
                                     :title="`Attention: ${val.toFixed(2)}`">
                                     {{ val.toFixed(1) }}
                                </div>
                            </div>
                        </div>
                    </template>
                </div>
            </div>
            
            <!-- Factories: List of factories with color weights -->
            <div class="section factories">
                 <h4>Factories Attention</h4>
                 <div class="factories-list">
                    <div v-for="(row, i) in data.saliency.factories" :key="i" class="factory-item">
                        <span class="factory-label">{{ i === data.saliency.factories.length - 1 ? 'Center' : 'Fact ' + i }}</span>
                        <div class="colors-bar">
                             <!-- 5 colors per factory -->
                             <div v-for="(val, c) in row" :key="c" 
                                  class="color-saliency"
                                  :style="{ height: Math.max(5, val * 50) + 'px', opacity: val * 0.8 + 0.2, backgroundColor: getColor(c) }"
                                  :title="`Color ${c}: ${val.toFixed(2)}`">
                                  <span v-if="val > 0.5" class="val-text">{{ val.toFixed(1) }}</span>
                             </div>
                        </div>
                    </div>
                 </div>
            </div>

            <!-- Global: List of global features -->
            <div class="section global">
                <h4>Global Features Attention</h4>
                <div class="global-bars">
                    <div v-for="(val, i) in data.saliency.global" :key="i" class="global-bar-item" 
                         :title="`${getGlobalLabel(i)}: ${val.toFixed(4)}`">
                         <div class="bar-fill" :style="{ width: (val * 100) + '%' }"></div>
                         <span class="bar-label">{{ getGlobalLabel(i) }}: {{ val.toFixed(2) }}</span>
                    </div>
                </div>
            </div>
        </div>
      </div>
      <div v-else class="loading">
        Analyzing Neural Network State...
      </div>
      
      <div class="actions">
        <button @click="$emit('continue')" class="continue-btn">Continue Game</button>
      </div>
    </div>
  </div>
  
  <div v-else class="neural-floating-controls">
      <div class="floating-content">
          <span>🧠 Neural Vision Active</span>
          <button @click="minimized = false" class="restore-btn">Show Analysis</button>
          <button @click="$emit('continue')" class="continue-small-btn">▶ Continue</button>
      </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'


defineEmits(['continue'])

const minimized = ref(false)

function getColor(idx) {
    const colors = ['blue', 'yellow', 'orange', 'black', 'red'];
    return colors[idx] || 'white';
}

const props = defineProps({
  data: Object
})

function getGlobalLabel(index) {
    if (props.data && props.data.saliency && props.data.saliency.global_labels && props.data.saliency.global_labels[index]) {
        return props.data.saliency.global_labels[index]
    }
    return `Feat ${index}`
}
</script>

<style scoped>
.neural-vision-overlay {
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(0,0,0,0.8);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 9999;
}
.neural-vision-modal {
    background: rgba(30,30,30, 0.95);
    color: white;
    padding: 20px;
    border-radius: 12px;
    width: 90%;
    height: 90%;
    overflow-y: auto;
    font-family: 'Courier New', monospace;
    display: flex;
    flex-direction: column;
}
.vision-content {
    flex: 1;
    overflow-y: auto;
}
.network-choice {
    background: #333;
    padding: 10px;
    margin-bottom: 20px;
    border-radius: 4px;
}
.choice-row {
    display: flex;
    gap: 20px;
    margin-top: 10px;
    flex-wrap: wrap;
}
.choice-item {
    flex: 1;
    background: rgba(0,0,0,0.2);
    padding: 10px;
    border-radius: 4px;
    display: flex;
    flex-direction: column;
    gap: 5px;
}
.choice-item.filtered {
    border-left: 4px solid #4CAF50;
}
.choice-item.raw {
    border-left: 4px solid #FF9800;
}
.choice-label {
    font-size: 0.8em;
    color: #aaa;
    text-transform: uppercase;
}
.choice-val {
    font-size: 1.1em;
}
.saliency-sections {
    display: flex;
    gap: 20px;
    flex-wrap: wrap;
}
.section {
    background: rgba(255,255,255,0.05);
    padding: 15px;
    border-radius: 8px;
    flex: 1;
    min-width: 300px;
}
.spatial-grids-container {
    display: flex;
    flex-wrap: wrap;
    gap: 15px;
    justify-content: center;
}
.spatial-item {
    display: flex;
    flex-direction: column;
    align-items: center;
}
.spatial-item h5 {
    margin: 5px 0;
    font-size: 0.9em;
    color: #ccc;
}
.heatmap-grid {
    display: flex;
    flex-direction: column;
    gap: 2px;
    align-items: center;
}
.heatmap-row {
    display: flex;
    gap: 2px;
}
.heatmap-cell {
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 1px solid #555;
    font-size: 0.8em;
    color: white;
    text-shadow: 1px 1px 1px black;
}
.factories-list {
    display: flex;
    flex-direction: column;
    gap: 10px;
}
.factory-item {
    display: flex;
    align-items: center;
    gap: 10px;
    height: 60px;
    border-bottom: 1px solid #444;
}
.factory-label {
    width: 60px;
    font-size: 0.9em;
}
.colors-bar {
    display: flex;
    gap: 4px;
    align-items: flex-end;
    height: 50px;
    flex: 1;
}
.color-saliency {
    width: 30px;
    border: 1px solid white;
    position: relative;
    display: flex;
    justify-content: center;
    align-items: flex-start;
}
.val-text {
    font-size: 0.7em;
    color: black;
    font-weight: bold;
    background: rgba(255,255,255,0.7);
    padding: 1px;
}
.global-bars {
    max-height: 400px;
    overflow-y: auto;
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
    gap: 5px;
}
.global-bar-item {
    background: #444;
    height: 20px;
    position: relative;
    border-radius: 2px;
}
.bar-fill {
    background: lime;
    height: 100%;
    opacity: 0.7;
}
.bar-label {
    position: absolute;
    left: 5px;
    top: 2px;
    font-size: 10px;
    color: white;
    text-shadow: 1px 1px 1px black;
}
.actions {
    margin-top: 20px;
    display: flex;
    justify-content: center;
}
.continue-btn {
    padding: 12px 30px;
    font-size: 1.2em;
    background: #4CAF50;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-weight: bold;
}
.continue-btn:hover {
    background: #45a049;
}
.loading {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 300px;
    font-size: 1.5em;
    color: #888;
}

/* Header & Controls */
.header-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
}
.header-controls {
    display: flex;
    gap: 10px;
}
.minimize-btn {
    background: #555;
    color: white;
    border: none;
    padding: 8px 12px;
    border-radius: 4px;
    cursor: pointer;
}
.minimize-btn:hover {
    background: #666;
}

/* Floating Controls */
.neural-floating-controls {
    position: fixed;
    top: 10px;
    right: 10px;
    z-index: 9998;
    background: rgba(30, 30, 30, 0.9);
    padding: 10px 15px;
    border-radius: 8px;
    color: white;
    box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    border: 1px solid #444;
}
.floating-content {
    display: flex;
    align-items: center;
    gap: 15px;
}
.restore-btn {
    background: #2196F3;
    color: white;
    border: none;
    padding: 6px 12px;
    border-radius: 4px;
    cursor: pointer;
    font-weight: bold;
}
.restore-btn:hover {
    background: #1976D2;
}
.continue-small-btn {
    background: #4CAF50;
    color: white;
    border: none;
    padding: 6px 12px;
    border-radius: 4px;
    cursor: pointer;
}
.continue-small-btn:hover {
    background: #388E3C;
}
</style>
