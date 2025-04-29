# BGA – Board Game Arena (Hola Mundo)

Plataforma de demostración para juegos de mesa online y bots.

Proyecto base para una plataforma de juegos de mesa online por turnos con arquitectura moderna, soporte para jugadores humanos y bots, y comunicación en tiempo real.

---

## 🧱 Arquitectura actual

| Componente       | Tecnología                          | Descripción |
|------------------|-------------------------------------|-------------|
| **Frontend**     | Vue 3 + Vite + Konva.js             | Interfaz gráfica, canvas interactivo, conexión WebSocket |
| **Backend**      | FastAPI (Python)                    | Lógica de juego, API REST, WebSockets |
| **Mensajería**   | Redis Streams                       | Coordinación de eventos internos (turnos, notificaciones) |
| **Base de datos**| PostgreSQL                          | Almacenamiento de usuarios, partidas y estado del juego |
| **Orquestación** | Docker Compose                      | Contenerización y despliegue local |

---

## 🚀 Cómo iniciar el proyecto

1. Clona el repositorio:

   ```bash
   git clone https://github.com/tuusuario/bga.git
   cd bga
   ```

2. Arranca los servicios:

   ```bash
   docker-compose up --build -d
   ```

   ```bash
   # Ver logs del backend
   docker-compose logs -f backend
   ```

3. Accede a:

   - Frontend: [http://localhost:3000](http://localhost:3000)
   - Backend API: [http://localhost:8000](http://localhost:8000)
   - WebSocket: `ws://localhost:8000/ws/cliente1`

## 🧪 Prueba rápida del WebSocket

Puedes usar un cliente como [WebSocket King](https://websocketking.com/) o simplemente el frontend ya conectado.

## 📁 Estructura del proyecto

```
bga/
├── .env
├── backend/
│   ├── .env
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── core/
│       │   ├── ai_base.py
│       │   ├── ai_tictactoe_random.py
│       │   ├── redis.py
│       │   └── seed.py
│       ├── db/
│       │   ├── base.py
│       │   ├── deps.py
│       │   └── session.py
│       ├── models/
│       │   ├── __init__.py
│       │   ├── game.py
│       │   ├── player.py
│       │   └── tictactoe.py
│       ├── routes/
│       │   ├── __init__.py
│       │   ├── auth.py
│       │   ├── games.py
│       │   ├── players.py
│       │   └── tictactoe.py
│       ├── utils/
│       │   └── __init__.py
│       └── main.py
├── frontend/
│   ├── Dockerfile
│   └── src/
│       ├── components/
│       │   ├── azul/
│       │   └── tictactoe/
│       │       ├── TicTacToe.vue
│       │       ├── TicTacToeActiveGames.vue
│       │       └── TicTacToeConfig.vue
│       ├── App.vue
│       ├── GamesList.vue
│       ├── LoginForm.vue
│       ├── main.js
│       └── router.js
├── docker-compose.yml
└── README.md
```

### Juegos implementados

- **TicTacToe**: juego de tres en raya con:
  - Configuración de jugadores (humanos o IA aleatoria).
  - Estado persistido en PostgreSQL.
  - Comunicación en tiempo real vía WebSockets y Redis Streams.

## 📄 Licencia

Este proyecto está licenciado bajo **CC BY-NC 4.0**.  
Puedes usarlo, modificarlo y compartirlo **sin fines comerciales** y **dando atribución**.  
[Ver licencia completa](https://creativecommons.org/licenses/by-nc/4.0/)