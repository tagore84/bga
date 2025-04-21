from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import redis.asyncio as redis
import uvicorn
from app.db.session import engine
from app.routes.auth import router as auth_router
from app.db.base.base import Base

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # durante desarrollo, allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)

redis_pool = None

@app.on_event("startup")
async def startup_event():
    global redis_pool
    redis_pool = redis.Redis(host="redis", port=6379, decode_responses=True)
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
        await redis_pool.xadd('bga:events', {"event": "hello", "client": client_id})
        while True:
            msg = await websocket.receive_text()
            await websocket.send_text(f"Eco: {msg}")
    except WebSocketDisconnect:
        print(f"Cliente {client_id} desconectado")

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
