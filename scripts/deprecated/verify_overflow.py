import requests
import json

API_URL = "http://localhost:8000"

def test_overflow():
    print("Creating game for overflow test...")
    res = requests.post(f"{API_URL}/azul/", json={
        "game_name": "test_overflow",
        "jugadores": [{"id": "p1", "type": "human", "name": "Tester"}]
    })
    
    if res.status_code != 200:
        print(f"Error creating game: {res.text}")
        return

    data = res.json()
    state = data["state"]
    game_id = data["azul_id"]
    
    # Find a factory with >= 2 tiles of same color
    target_factory = -1
    target_color = -1
    
    for i, factory in enumerate(state["expositores"]):
        counts = {}
        for color in factory:
            counts[color] = counts.get(color, 0) + 1
        
        for color, count in counts.items():
            if count >= 2:
                target_factory = i
                target_color = color
                break
        if target_factory != -1:
            break
            
    if target_factory == -1:
        print("Could not find a factory with >= 2 tiles of same color. Retrying might be needed.")
        return

    print(f"Found target: Factory {target_factory}, Color {target_color} (Count >= 2)")
    
    # Move to Row 1 (index 0), which has capacity 1
    print("Making move to Row 1 (capacity 1)...")
    res = requests.post(f"{API_URL}/azul/{game_id}/move", json={
        "factory": target_factory,
        "color": target_color,
        "row": 1 # 1-based index for API
    })
    
    if res.status_code != 200:
        print(f"Error making move: {res.text}")
        return
        
    move_data = res.json()
    new_state = move_data["state"]
    p1_patrones = new_state["jugadores"]["p1"]["patrones"]
    p1_suelo = new_state["jugadores"]["p1"]["suelo"]
    
    row0 = p1_patrones[0]
    print(f"Row 0 content: {row0}")
    print(f"Floor content: {p1_suelo}")
    
    if len(row0) > 1:
        print("FAIL: Row 0 has more than 1 tile!")
    else:
        print("SUCCESS: Row 0 has correct number of tiles.")
        if len(p1_suelo) > 0:
             print("And excess went to floor.")
        else:
             print("But floor is empty? (Maybe exact fit?)")

if __name__ == "__main__":
    test_overflow()
