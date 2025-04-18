# BGA – Board Game Arena (Hola Mundo)

Proyecto base para una plataforma de juegos de mesa online con arquitectura moderna.

## 🧱 Stack Tecnológico

- **Backend**: Python + FastAPI + WebSockets
- **Frontend**: Vue 3 + Composition API + Konva.js
- **Comunicación en tiempo real**: WebSockets nativos
- **Mensajería**: Redis Streams
- **Base de datos**: PostgreSQL + Redis
- **Orquestación**: Docker Compose

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