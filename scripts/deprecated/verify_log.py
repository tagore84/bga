import requests
import json

API_URL = "http://localhost:8000"

def test_log():
    print("Creating game for log test...")
    res = requests.post(f"{API_URL}/azul/", json={
        "game_name": "test_log",
        "jugadores": [{"id": "p1", "type": "human", "name": "Logger"}]
    })
    
    if res.status_code != 200:
        print(f"Error creating game: {res.text}")
        return

    data = res.json()
    state = data["state"]
    game_id = data["azul_id"]
    
    # Find a factory with tiles
    target_factory = 0
    target_color = state["expositores"][0][0]
    
    print(f"Making move: Factory {target_factory}, Color {target_color}")
    
    res = requests.post(f"{API_URL}/azul/{game_id}/move", json={
        "factory": target_factory,
        "color": target_color,
        "row": 1
    })
    
    if res.status_code != 200:
        print(f"Error making move: {res.text}")
        return
        
    move_data = res.json()
    new_state = move_data["state"]
    
    if "log" in new_state:
        print(f"Log field present. Content: {new_state['log']}")
        if len(new_state["log"]) > 0:
            print("SUCCESS: Log has entries.")
        else:
            print("FAIL: Log is empty.")
    else:
        print("FAIL: Log field missing from state.")

if __name__ == "__main__":
    test_log()
