from app.core.redis import publish_stream_event

async def publish_azul_update(game_id: int, state: dict):
    await publish_stream_event(f"azul:{game_id}", {
        "type": "update",
        "state": state
    })
