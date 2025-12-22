import asyncio
import websockets
import json
import requests
import sys

API_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws/azul"

async def test_socket():
    # 1. Create a game
    print("Creating game...")
    try:
        res = requests.post(f"{API_URL}/azul/", json={
            "game_name": "test_socket_game",
            "jugadores": [{"id": "p1", "type": "human", "name": "HumanPlayer"}, {"id": "p2", "type": "ai", "name": "RandomAzul"}]
        })
        res.raise_for_status()
        game_data = res.json()
        game_id = game_data["azul_id"]
        print(f"Game created with ID: {game_id}")
    except Exception as e:
        print(f"Error creating game: {e}")
        return

    # 2. Connect to WebSocket
    uri = f"{WS_URL}/{game_id}"
    print(f"Connecting to {uri}...")
    async with websockets.connect(uri) as websocket:
        print("Connected to WebSocket")

        # 3. Make a move (simulate human move)
        # We need to find a valid move first.
        state = game_data["state"]
        # Just pick the first available move from factory 0
        factory_idx = 0
        color = None
        if state["expositores"] and state["expositores"][0]:
            color = state["expositores"][0][0]
        
        if color is None:
            print("No valid move found in factory 0")
            return

        print(f"Making move: factory={factory_idx}, color={color}, row=0")
        
        # Send move via API
        # We need to run this in a separate thread or just make the request async?
        # Requests is blocking, but that's fine for this test script if we do it before waiting for message?
        # No, we want to be listening when the event comes.
        
        # So we'll use asyncio.to_thread for the request
        
        async def make_move_request():
            await asyncio.sleep(1) # Wait a bit to ensure socket is ready
            print("Sending move request...")
            try:
                res = requests.post(f"{API_URL}/azul/{game_id}/move", json={
                    "factory": factory_idx,
                    "color": color,
                    "row": 1 # 1-based index in API? Let's check frontend. Frontend sends selectedRow.value.
                             # In frontend: targetX = ... selectedRow.value ...
                             # backend expects 0-based or 1-based?
                             # backend/app/models/azul/azul.py: AzulMove has row: int
                             # backend/app/routes/azul/azul.py: aplicar_movimiento(state, ..., move)
                             # Let's assume 1-based for now as frontend uses 1-5 for rows in UI logic?
                             # Frontend: selectedRow.value - 1 is used for array index. So selectedRow is 1-based.
                             # Let's send 1.
                })
                print(f"Move response: {res.status_code}")
                if res.status_code == 200:
                    move_data = res.json()
                    if "state" in move_data:
                        print("Move response contains state")
                    else:
                        print("Move response MISSING state")
                else:
                    print(res.text)
            except Exception as e:
                print(f"Error sending move: {e}")

        asyncio.create_task(make_move_request())

        # 4. Listen for messages
        print("Waiting for messages...")
        try:
            while True:
                message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                data = json.loads(message)
                print(f"Received message: {data.keys()}")
                if "type" in data and data["type"] == "update":
                    print("Received update event!")
                    # Check if state is present
                    if "state" in data:
                        print("State is present in update event")
                        # We can break if we received the update
                        # We might receive multiple updates (human + AI)
                        # Let's wait for 2 updates if AI plays
                        # But for now, just confirming we get at least one is enough.
                        # break 
                
        except asyncio.TimeoutError:
            print("Timeout waiting for message")

if __name__ == "__main__":
    asyncio.run(test_socket())
