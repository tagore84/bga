# 🎋 Nim — Versión Misère (Reglamento)

## 1. Objetivo del juego
El objetivo del juego es **forzar al oponente a retirar el último objeto**.  
En la versión **misère**, **pierde** el jugador que toma el **último objeto** del juego.

---

## 2. Preparación
- Se colocan varios montones (o filas) de objetos idénticos  
  (palillos, piedras, fichas, etc.).
- Cada montón puede tener un número distinto de objetos.
- Dos jugadores se sientan frente al tablero.
- Se decide al azar quién comienza.

### Ejemplo de disposición inicial
![Ejemplo de montones de Nim](https://upload.wikimedia.org/wikipedia/commons/7/7c/Nim-piles.svg)

---

## 3. Desarrollo del juego
Los jugadores juegan por turnos.

En su turno, un jugador debe:
1. Elegir **un único montón**.
2. Retirar **uno o más objetos** de ese montón.

⚠️ No está permitido retirar objetos de más de un montón en el mismo turno.

### Ejemplo de turno válido
![Ejemplo de retirar objetos de una sola fila](https://upload.wikimedia.org/wikipedia/commons/3/33/Nim_game_example.svg)

---

## 4. Condición de derrota
- El jugador que **retira el último objeto del tablero pierde la partida**.

---

## 5. Fin de la partida
La partida termina cuando no quedan objetos en ningún montón.  
El jugador que realizó el último movimiento es declarado **perdedor**.

### Ejemplo de final de partida
![Final de partida en Nim](https://upload.wikimedia.org/wikipedia/commons/5/5c/Nim_endgame.svg)

---

## 6. Estrategia básica (opcional)
- Mientras exista **al menos un montón con más de un objeto**, el juego se
  comporta como el Nim clásico.
- Cuando todos los montones tienen **exactamente un objeto**:
  - Si hay un **número impar** de montones → la posición es **perdedora**
    para el jugador al que le toca.
  - Si hay un **número par** → la posición es **ganadora**.

### Ejemplo de situación crítica (solo montones de tamaño 1)
![Ejemplo de Nim Misère con montones de 1](https://upload.wikimedia.org/wikipedia/commons/2/2f/Nim_misere_example.svg)

---

## 7. Variante común: disposición en pirámide
Una forma habitual de jugar es colocar los objetos en filas formando una pirámide:

![Nim en disposición de pirámide](https://upload.wikimedia.org/wikipedia/commons/8/8a/Nim_pyramid.jpg)

Las reglas se mantienen:
- Solo se puede retirar objetos de **una fila por turno**.
- Pierde quien retire el **último objeto**.

---

## 8. Notas finales
- Nim Misère es un **juego imparcial**, sin azar y de información perfecta.
- Existe una **estrategia ganadora óptima**.
- Es una variante clásica en la teoría matemática de juegos.

---