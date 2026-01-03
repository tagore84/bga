# 🏛️ Santorini — Reglas del juego

[Santorini](chatgpt://generic-entity?number=0) es un juego de mesa abstracto de estrategia para **2 jugadores**, con reglas simples y gran profundidad táctica.

---

## 🎯 Objetivo del juego

Gana el jugador que **mueva uno de sus trabajadores a una casilla de nivel 3** (la tercera planta de una torre).

---

## 🧩 Componentes

- Tablero de **5 × 5 casillas**
- **2 trabajadores por jugador**
- Piezas de construcción:
  - Nivel 1
  - Nivel 2
  - Nivel 3
  - Cúpulas (domos)

---

## ⚙️ Preparación

1. Coloca el tablero vacío.
2. Cada jugador coloca **sus 2 trabajadores** en **casillas distintas** del tablero.
3. No hay construcciones al inicio de la partida.

---

## 🔄 Turno de juego

En su turno, un jugador debe realizar **obligatoriamente**, en este orden:

1. **Mover**
2. **Construir**

---

## 🚶 Movimiento

- Elige **uno de tus trabajadores**.
- Muévelo a una **casilla adyacente** (horizontal, vertical o diagonal).

### Reglas de movimiento
- No puedes moverte a una casilla ocupada.
- No puedes moverte a una casilla con cúpula.
- Puedes subir **como máximo 1 nivel**.
- Puedes bajar cualquier número de niveles.

### Ejemplos
- Nivel 1 → Nivel 2 ✔️  
- Nivel 2 → Nivel 3 ✔️  
- Nivel 1 → Nivel 3 ❌  

---

## 🏗️ Construcción

- Tras mover, el mismo trabajador debe **construir en una casilla adyacente**.

### Reglas de construcción
- La casilla no puede estar ocupada.
- No puede tener una cúpula.
- Solo se construye **una pieza por turno**.
- El orden de construcción es:
  1. Nivel 1
  2. Nivel 2
  3. Nivel 3
  4. Cúpula

---

## 🏆 Condición de victoria

Un jugador **gana inmediatamente** cuando uno de sus trabajadores:

- Se mueve desde un nivel inferior a una casilla de **nivel 3**.

> No es necesario construir después de alcanzar el nivel 3.

---

## ☠️ Condición de derrota

Un jugador **pierde** si, al comenzar su turno:

- Ninguno de sus trabajadores puede realizar un **movimiento legal seguido de una construcción**.

---

## 🧠 Notas estratégicas

- El control del centro es clave.
- Las cúpulas permiten bloquear al rival.
- Construir bajo tus propios trabajadores puede ser arriesgado.
- Juego de **información perfecta** y **sin azar**.

---

## 🧩 Variante con poderes (opcional)

En la versión avanzada, cada jugador recibe una **carta de dios** que modifica las reglas básicas.

> Toda la información de los dioses se encuentra en el archivo [santorini-gods.md](santorini-gods.md).

---

## 📐 Datos rápidos

| Característica | Valor |
|---------------|------|
| Jugadores | 2 |
| Duración | 15–20 minutos |
| Azar | Ninguno |
| Tipo | Abstracto estratégico |