import requests
import sys

BASE_URL = "http://localhost:8000"

def run_verification():
    print("Starting Chess Verification...")
    
    # 1. Login/Get Token (assuming we can use a test user or just anonymous if auth disabled for dev, but routes say Depends(get_current_player))
    # Let's assume we can register/login.
    # Actually, let's hardcode a token if we know one, or register a temp user.
    # To keep it simple, I'll try to register a new user:
    # Register a dedicated user for verification to avoid credential issues
    username = "verify_user"
    password = "password123"
    try:
        requests.post(f"{BASE_URL}/signup", json={"name": username, "password": password})
    except:
        pass

    login_res = requests.post(f"{BASE_URL}/login", json={"name": username, "password": password})
    if login_res.status_code != 200:
        print(f"Login failed for '{username}'. Response:", login_res.text)
        return

    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("Login successful.")

    # 2. List Games
    print("Listing games...")
    res = requests.get(f"{BASE_URL}/chess/", headers=headers)
    assert res.status_code == 200
    print(f"Found {len(res.json())} active chess games.")

    # 3. Create Game
    print("Creating new game...")
    # Get self ID
    me = requests.get(f"{BASE_URL}/me", headers=headers).json()
    my_id = me["id"]
    
    payload = {
        "game_name": "Verification Game",
        "white_player_id": my_id,
        "black_player_id": my_id, # Playing against self for test
        "opponent_type": "human"
    }
    res = requests.post(f"{BASE_URL}/chess/", json=payload, headers=headers)
    if res.status_code != 200:
        print("Create game failed:", res.text)
        return
        
    game = res.json()
    game_id = game["id"]
    print(f"Game created: ID {game_id}, FEN: {game['board_fen']}")
    
    # 4. Make Move (White: e2e4)
    print("Making move e2e4...")
    move_payload = {"move_uci": "e2e4"}
    res = requests.post(f"{BASE_URL}/chess/{game_id}/move", json=move_payload, headers=headers)
    if res.status_code != 200:
        print("Move failed:", res.text)
        return
    
    game_state = res.json()
    print(f"Move successful. New FEN: {game_state['board_fen']}")
    assert "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR" in game_state['board_fen']
    assert game_state['current_turn'] == 'black'
    
    # 5. Make Move (Black: e7e5)
    print("Making move e7e5...")
    move_payload = {"move_uci": "e7e5"}
    res = requests.post(f"{BASE_URL}/chess/{game_id}/move", json=move_payload, headers=headers)
    assert res.status_code == 200
    print("Black move successful.")
    
    # 6. Test Illegal Move
    print("Testing illegal move (e2e5)...")
    move_payload = {"move_uci": "e2e5"} # Pawn already at e4, cannot jump to e5 or move again from e2
    res = requests.post(f"{BASE_URL}/chess/{game_id}/move", json=move_payload, headers=headers)
    assert res.status_code == 400
    print("Illegal move correctly rejected.")

    print("Verification passed!")

if __name__ == "__main__":
    run_verification()
