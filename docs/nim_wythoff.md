# ♟️ Wythoff Nim (Reglamento)

## 1. Objetivo del juego
El objetivo del juego es **ser el jugador que realiza el último movimiento válido**.

---

## 2. Preparación
- Se colocan **dos montones** de objetos idénticos  
  (palillos, fichas, piedras, etc.).
- Cada montón puede tener un número distinto de objetos.
- Dos jugadores participan en la partida.
- Se decide al azar quién comienza.

---

## 3. Desarrollo del juego
Los jugadores juegan por turnos.

En su turno, un jugador debe realizar **una y solo una** de las siguientes acciones:

### Opción A — Movimiento estándar
- Elegir **un solo montón**.
- Retirar **uno o más objetos** de ese montón.

### Opción B — Movimiento diagonal
- Retirar el **mismo número de objetos de ambos montones** al mismo tiempo.
- El número retirado debe ser **al menos 1** y no mayor que el tamaño del montón más pequeño.

⚠️ No está permitido combinar ambas opciones en un mismo turno.

---

## 4. Restricciones
- No se pueden retirar objetos de más de dos montones (solo existen dos).
- No se pueden retirar cantidades distintas de cada montón en la opción diagonal.
- No se permiten movimientos que dejen un montón con número negativo de objetos.

---

## 5. Condición de victoria
- **Gana el jugador que retira el último objeto**, dejando ambos montones vacíos.

---

## 6. Fin de la partida
La partida termina cuando ambos montones están vacíos.  
El jugador que realizó el último movimiento es declarado **ganador**.

---

## 7. Ejemplo de movimientos válidos
Si los montones son (5, 3):

- Movimiento estándar:
  - (5, 3) → (2, 3)
  - (5, 3) → (5, 1)

- Movimiento diagonal:
  - (5, 3) → (4, 2)
  - (5, 3) → (3, 1)
  - (5, 3) → (2, 0)

---

## 8. Estrategia básica (opcional)
- Wythoff Nim es un juego imparcial y determinista con **estrategia óptima conocida**.
- Las posiciones perdedoras siguen una estructura matemática relacionada con la
  **razón áurea (φ)**.
- A diferencia del Nim clásico, **no basta con calcular el XOR** de los montones.

> Nota: la estrategia exacta suele omitirse en partidas casuales para mantener
> el interés del juego.

---

## 9. Notas finales
- Wythoff Nim es más profundo y menos predecible que Nim clásico.
- Mantiene el interés hasta el final incluso entre jugadores expertos.
- Es un ejemplo clásico en la teoría de juegos combinatoria.

---