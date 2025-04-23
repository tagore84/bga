from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import redis.asyncio as redis_client
import uvicorn
from app.db.session import engine
from app.routes.auth import router as auth_router
from app.db.base import Base
from app.routes.tictactoe import router as ttt_router
from app.routes.users import router as users_router
import json
from app.routes.auth import router as auth_router
from app.routes.tictactoe import router as ttt_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # durante desarrollo, allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Ahora monta tus routers (auth y tictactoe)
app.include_router(auth_router)
app.include_router(ttt_router)
app.include_router(users_router)



@app.on_event("startup")
async def startup_event():
    # Inicializa el pool en nuestro módulo core.redis
    from app.core.redis import redis_pool as pool_ref
    pool_ref = redis_client.Redis(host="redis", port=6379, decode_responses=True)
    # Asignamos al atributo del módulo
    import app.core.redis as core_redis
    core_redis.redis_pool = pool_ref
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.get("/")
async def read_root():
    return {"message": "Hola Mundo desde FastAPI!"}

@app.websocket('/ws/{client_id}')
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    try:
        await websocket.send_text(f"Hola Mundo desde WebSocket, cliente {client_id}!")
        await core_redis.redis_pool.xadd('bga:events', {"event": "hello", "client": client_id})
        while True:
            msg = await websocket.receive_text()
            await websocket.send_text(f"Eco: {msg}")
    except WebSocketDisconnect:
        print(f"Cliente {client_id} desconectado")


@app.websocket("/ws/tictactoe/{game_id}")
async def websocket_tictactoe(websocket: WebSocket, game_id: int):
    """
    Cada vez que haya un nuevo movimiento en Redis Stream 'tictactoe:{game_id}',
    lo reenviamos a los clientes conectados.
    """
    await websocket.accept()
    import app.core.redis as core_redis
    # Leer desde el último ID ($ = nuevos mensajes)
    last_id = "$"
    try:
        while True:
            # XREAD BLOCK espera hasta 30s por nuevos eventos
            entries = await core_redis.redis_pool.xread(
                streams={f"tictactoe:{game_id}": last_id},
                block=30000,
                count=10
            )
            if not entries:
                continue
            # entries = [(stream_key, [(id, {field: value, ...}), ...])]
            for _, msgs in entries:
                for msg_id, payload in msgs:
                    last_id = msg_id
                    # reenviamos al cliente como JSON
                    await websocket.send_text(json.dumps(payload))
    except WebSocketDisconnect:
        return
    
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
