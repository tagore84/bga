from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import aioredis
import uvicorn

app = FastAPI()
redis = None

@app.on_event("startup")
async def startup_event():
    global redis
    redis = await aioredis.create_redis_pool("redis://redis:6379")

@app.get("/")
async def read_root():
    return {"message": "Hola Mundo desde FastAPI!"}

@app.websocket('/ws/{client_id}')
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    try:
        # Enviar saludo inicial
        await websocket.send_text("Hola Mundo desde WebSocket, cliente %s!" % client_id)
        # Publicar evento en Redis Stream
        await redis.xadd('bga:events', {b'event': b'hello', b'client': client_id.encode()})
        while True:
            msg = await websocket.receive_text()
            await websocket.send_text(f"Eco: {msg}")
    except WebSocketDisconnect:
        print(f"Cliente {client_id} desconectado")

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)