# BGA – Board Game Arena (Hola Mundo)

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
   docker-compose up --build
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
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       └── main.py
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   └── src/
│       ├── App.vue
│       └── main.js
├── docker-compose.yml
└── README.md
```

## 📄 Licencia

Este proyecto está licenciado bajo **CC BY-NC 4.0**.  
Puedes usarlo, modificarlo y compartirlo **sin fines comerciales** y **dando atribución**.  
[Ver licencia completa](https://creativecommons.org/licenses/by-nc/4.0/)