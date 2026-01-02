# Santorini Digital — Visual Assets Specification

Este documento describe **la perspectiva, cámara y reglas visuales** usadas para generar todos los assets gráficos del juego *Santorini Digital*.

Su objetivo es garantizar **consistencia visual**, correcta superposición de piezas y facilitar la generación futura de nuevos assets mediante IA o herramientas gráficas.

---

## 1. Sistema de Perspectiva

### 1.1 Tipo de vista

- **Isometric 3/4 view**
- No es una perspectiva realista
- No existe punto de fuga

Esta vista permite:
- Representación clara de altura (edificios apilables)
- Alineación perfecta en cuadrícula
- Superposición limpia de piezas

---

### 1.2 Parámetros de cámara

| Parámetro | Valor |
|---------|------|
| Rotación horizontal | 45° |
| Inclinación vertical | ~30° |
| Zoom | Constante |
| Distorsión | Ninguna |

⚠️ **Todos los assets deben compartir exactamente estos parámetros**

---

### 1.3 Orientación espacial

- La esquina inferior izquierda del asset apunta hacia el observador
- Las líneas del grid siguen ejes diagonales
- La base del objeto siempre es paralela al plano del tablero

---

## 2. Escala y Proporciones

### 2.1 Sistema de alturas

| Elemento | Altura relativa |
|--------|----------------|
| Jugador | ≈ Nivel 2 |
| Edificio nivel 1 | 1 unidad |
| Edificio nivel 2 | 2 unidades |
| Edificio nivel 3 | 3 unidades |
| Domo | +0.5 unidades |

- Las alturas son **visualmente proporcionales**, no realistas
- El jugador debe encajar claramente en un edificio nivel 2

---

### 2.2 Relación tablero ↔ piezas

- El tablero es una cuadrícula **5×5**
- Cada celda debe permitir:
  - 1 edificio
  - 1 jugador
- No debe existir solapamiento visual incorrecto

---

## 3. Iluminación

### 3.1 Fuente de luz

- Luz neutra y uniforme
- Dirección: superior izquierda
- Intensidad moderada

---

### 3.2 Sombras

- Sombras suaves
- Sin sombras proyectadas fuera del objeto
- Sin sombras duras o dramáticas

Las sombras deben:
- Dar sensación de volumen
- No interferir con la eliminación del fondo

---

## 4. Estilo Artístico

### 4.1 Estilo general

- **Ilustración 3D estilizada**
- Inspiración mediterránea
- Superficies limpias
- Bordes definidos

🚫 No fotorealismo  
🚫 No texturas complejas  
🚫 No desgaste excesivo  

---

### 4.2 Detalle visual

- Detalle suficiente para diferenciar piezas
- No exceso de microdetalles
- Formas simples y legibles a tamaños pequeños

---

## 5. Fondo y Transparencia

### 5.1 Fondo

- Color sólido uniforme
- Recomendado:
  - Verde croma `#00FF00`
  - Magenta `#FF00FF`

---

### 5.2 Reglas del fondo

- Sin gradientes
- Sin ruido
- Sin sombras externas
- Alto contraste con el objeto

El fondo está diseñado para ser **eliminado posteriormente** y generar imágenes con transparencia.

---

## 6. Encadre y Composición

### 6.1 Posicionamiento

- Objeto centrado
- Totalmente visible
- Sin recortes

---

### 6.2 Márgenes

- Margen visual uniforme alrededor del objeto
- Evita que el asset “toque” los bordes de la imagen

---

## 7. Reglas específicas por tipo de asset

### 7.1 Tablero

- Debe estar **completamente vacío**
- Grid visible
- Sin edificios ni jugadores
- Base sólida

---

### 7.2 Edificios

- Cada nivel es claramente distinguible
- El domo solo aparece en el nivel final
- Diseñados para apilarse visualmente

---

### 7.3 Jugadores

- Misma forma base para todos
- Diferenciación solo por color
- Sin rasgos faciales detallados
- Pose neutra, sin acción

---

## 8. Consistencia Global (Regla de Oro)

> **Cualquier asset nuevo debe poder colocarse junto a uno existente sin que se note que fue generado en otro momento.**

Esto implica:
- Misma cámara
- Misma iluminación
- Mismo estilo
- Misma escala

---

## 9. Uso previsto

Estos assets están pensados para:
- Juegos digitales
- Motores 2D con simulación isométrica
- Superposición por capas (z-index)
- Renderizado con transparencia

---

## 10. Nota para IAs que generen o usen assets

Este documento actúa como un **contrato visual**.

Cualquier IA que:
- Genere nuevos assets
- Modifique existentes
- Reescale o combine piezas

**Debe respetar estrictamente esta especificación**.


## 11. Sistema de Coordenadas del Tablero (Pixel Mapping)
Esta sección describe cómo se han calculado las coordenadas en píxeles de cada casilla del tablero, a partir de la imagen final del asset del tablero.

11.1 Imagen de referencia • Resolución del tablero: 1536 × 838 px • Vista: isométrica 3/4 según lo descrito en las secciones anteriores • El cálculo se realiza sobre el grid interior, excluyendo el marco decorativo

⚠️ Si la imagen del tablero cambia (escala, recorte, nueva generación), estas coordenadas deberán recalcularse.

⸻

## 11.2 Sistema de referencia  
    - Coordenadas absolutas en píxeles (x, y) 
    - Origen (0,0) en la esquina superior izquierda de la imagen 
    - Cada casilla se identifica como (fila, columna): • (0,0) → esquina superior izquierda del grid • (4,4) → esquina inferior derecha del grid

Las coordenadas corresponden al centro visual de cada casilla, lo cual es ideal para: • Posicionar jugadores • Posicionar edificios • Animaciones • Cálculo de profundidad (z-order)

⸻

## 11.3 Coordenadas de las casillas (centro)

Fila 0: (0,0): (300, 160) (0,1): (525, 195) (0,2): (750, 230) (0,3): (975, 265) (0,4): (1200, 300)

Fila 1: (1,0): (332, 295) (1,1): (558, 311) (1,2): (783, 328) (1,3): (1008, 344) (1,4): (1233, 360)

Fila 2: (2,0): (365, 430) (2,1): (590, 428) (2,2): (815, 425) (2,3): (1040, 423) (2,4): (1265, 420)

Fila 3: (3,0): (398, 565) (3,1): (623, 544) (3,2): (848, 523) (3,3): (1073, 501) (3,4): (1298, 480)

Fila 4: (4,0): (430, 700) (4,1): (655, 660) (4,2): (880, 620) (4,3): (1105, 580) (4,4): (1330, 540)

⸻

## 11.4 Representación como estructura de datos

Ejemplo en Python:

BOARD_CELLS = { (0,0): (300, 160), (0,1): (525, 195), (0,2): (750, 230), (0,3): (975, 265), (0,4): (1200, 300), (1,0): (332, 295), (1,1): (558, 311), (1,2): (783, 328), (1,3): (1008, 344), (1,4): (1233, 360), (2,0): (365, 430), (2,1): (590, 428), (2,2): (815, 425), (2,3): (1040, 423), (2,4): (1265, 420), (3,0): (398, 565), (3,1): (623, 544), (3,2): (848, 523), (3,3): (1073, 501), (3,4): (1298, 480), (4,0): (430, 700), (4,1): (655, 660), (4,2): (880, 620), (4,3): (1105, 580), (4,4): (1330, 540), }

⸻

## 11.5 Z-order recomendado

Para un correcto pintado en isométrico:

z_index = fila + columna

Alternativamente: • Renderizar por filas de arriba a abajo • Dentro de cada fila, de izquierda a derecha

⸻

## 11.6 Nota sobre robustez futura

Estas coordenadas están pensadas para la imagen actual del tablero.

Para un sistema más robusto a cambios futuros, se recomienda: • Definir las 4 esquinas del grid • Calcular las posiciones por interpolación

Esto permite adaptar automáticamente las coordenadas si cambia la resolución o el asset.

⸻

Fin del documento.