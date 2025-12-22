import requests
import time

API_URL = "http://localhost:8000"

def test_ai_start():
    print("Creating game with AI as first player...")
    res = requests.post(f"{API_URL}/azul/", json={
        "game_name": "test_ai_start_forced",
        "jugadores": [{"id": "p2", "type": "ai", "name": "RandomAzul"}, {"id": "p1", "type": "human", "name": "Human"}]
    })
    
    if res.status_code != 200:
        print(f"Error creating game: {res.text}")
        return

    data = res.json()
    state = data["state"]
    game_id = data["azul_id"]
    
    print(f"Game created. ID: {game_id}. Initial Turn: {state['turno_actual']}")
    
    p2_state = state["jugadores"]["p2"]
    if has_played(p2_state):
        print("AI (p2) has played! SUCCESS.")
    else:
        print("AI (p2) has NOT played.")
        if state["turno_actual"] == "p2":
             print("It is AI's turn but it hasn't played. FAIL.")
        else:
             print("It is NOT AI's turn. AI didn't start (unexpected).")

def has_played(player_state):
    # Check pattern lines or floor
    for row in player_state["patrones"]:
        if any(c is not None for c in row):
            return True
    if player_state["suelo"]:
        return True
    return False

if __name__ == "__main__":
    test_ai_start()
