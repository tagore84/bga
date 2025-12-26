# Plan de Acción: Ajedrez

Este documento detalla los pasos para implementar el juego de Ajedrez en la plataforma existente.

## 1. Base de Datos

### Modelo `ChessGame`
Crearemos un nuevo modelo en `backend/app/models/chess/chess.py` que herede de `Base`.

**Campos:**
- `id`: Integer, Primary Key.
- `board_fen`: String (FEN format), representa el estado del tablero. Default: Start Position.
- `current_turn`: String ('white', 'black').
- `status`: String ('in_progress', 'checkmate', 'stalemate', 'draw', 'resign').
- `config`: JSON (tiempo, variantes, etc.).
- `white_player_id`: FK `players.id`.
- `black_player_id`: FK `players.id`.
- `game_id`: FK `games.id` (referencia a la tabla maestra de juegos).
- `created_at`: DateTime.

### Seed Data
- Actualizar `backend/app/core/seed.py` para asegurar que el juego "chess" exista en la tabla `games`.

## 2. Backend

### Dependencias
- Agregar `chess` (python-chess) a `backend/requirements.txt`. Esta librería manejará toda la lógica de validación de movimientos, estado del tablero y detección de jaque mate/tablas.

### Rutas (`backend/app/routes/chess/chess.py`)
Implementar los siguientes endpoints:

1.  `GET /chess/`
    - Lista partidas activas (`status == 'in_progress'`).
    - Devuelve detalles de los jugadores y estado básico.

2.  `POST /chess/`
    - Crea una nueva partida.
    - Recibe: opponent ID, color preference (optional).
    - Inicializa el tablero estándar.
    - Publica evento `create` en Redis.

3.  `GET /chess/{game_id}`
    - Devuelve el estado completo de la partida (FEN, turno actual, jugadores).

4.  `POST /chess/{game_id}/move`
    - Recibe: movimiento en formato UCI (e.g., "e2e4") o SAN.
    - Valida el movimiento usando `python-chess`.
    - Actualiza el FEN y el turno en la DB.
    - Detecta fin de juego (Jaque mate, tablas).
    - Publica evento `move` en Redis para actualizaciones en tiempo real.

## 3. Frontend

### Componentes (`frontend/src/components/chess/`)

1.  **`ChessConfig.vue`**
    - Formulario para iniciar nueva partida.
    - Selección de oponente (lista de usuarios).
    - Selección de color (aleatorio, blanco, negro).

2.  **`ChessActiveGames.vue`**
    - Lista de partidas en curso con botón para unirse/observar.

3.  **`ChessGame.vue`**
    - Componente principal del juego.
    - **Visualización**: Renderizar el tablero de 64 casillas.
    - **Piezas**: Usar imágenes SVG o caracteres Unicode estilizados.
    - **Interacción**: Drag & drop o Click-Click para mover.
    - **Integración**:
        - Polling o WebSocket (vía Redis events si ya hay infraestructura en frontend) para actualizaciones.
        - Enviar movimientos al backend.
    - **Feedback**: Mostrar jaque, jaque mate, turno actual.

### Router
- Actualizar `frontend/src/router.js` para incluir las rutas `/chess/config`, `/chess/alert`, `/chess/:id`.

### GamesList
- Actualizar `GamesList.vue` para mostrar la tarjeta de "Ajedrez" y vincular a la configuración.

## 4. Estética (Vibe Coding)
- Usar un diseño limpio y moderno para el tablero.
- Colores suaves para las casillas (e.g., madera clara/oscura o azul grisáceo/blanco).
- Animaciones suaves al mover piezas.

## 5. Jugador de IA

### Backend (`backend/app/core/chess/`)
Implementar una IA básica para permitir jugar contra la máquina.

1.  **`ai_chess_random.py`**
    - Implementación simple que selecciona un movimiento legal aleatorio.
    - Útil para pruebas y verificación inicial.

2.  **Integración**
    - Registrar la IA en `ai_base.py`.
    - Actualizar `routes/chess.py` para manejar el turno de la IA si el oponente está configurado como "AI".

## Pasos de Ejecución

1.  [ ] **Backend**: Instalar `chess` y crear modelo DB.
2.  [ ] **Backend**: Implementar rutas y lógica de juego.
3.  [ ] **Backend**: Implementar IA Básica (Random).
4.  [ ] **Frontend**: Crear componentes básicos y routing.
5.  [ ] **Frontend**: Implementar lógica de tablero e interacción.
6.  [ ] **Verificación**: Jugar una partida completa (Human vs Human y Human vs IA).
