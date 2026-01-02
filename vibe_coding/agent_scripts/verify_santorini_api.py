import requests
import sys
import uuid

BASE_URL = "http://localhost:8000"

def login():
    # Login as a test user or create one
    unique_name = f"test_{str(uuid.uuid4())[:8]}"
    try:
        # Try register
        print(f"Registering user {unique_name}...")
        r = requests.post(f"{BASE_URL}/auth/signup", json={"name": unique_name, "password": "password"})
        if r.status_code != 201:
             print(f"Signup failed: {r.text}")
             return None, None
             
        # Try login
        r = requests.post(f"{BASE_URL}/auth/login", json={"name": unique_name, "password": "password"})
        
        if r.status_code == 200:
            token = r.json()["access_token"]
            
            # Fetch Me
            headers = {"Authorization": f"Bearer {token}"}
            me = requests.get(f"{BASE_URL}/auth/me", headers=headers)
            if me.status_code == 200:
                uid = me.json()["id"]
                return token, uid

            
        else:
            print(f"Login/Signup failed. Status: {r.status_code}")
            print(r.text)
    except Exception as e:
        print(f"Login failed: {e}")
        return None, None
    return None, None

def check_santorini(token, user_id):
    if not token:
        print("No token, skipping")
        return

    headers = {"Authorization": f"Bearer {token}"}
    
    print("1. Creating Game...")
    payload = {
        "game_name": "Test Santorini",
        "playerP1Type": "human",
        "playerP1Id": user_id,
        "playerP2Type": "human",
        "playerP2Id": user_id
    }
    
    try:
        r = requests.post(f"{BASE_URL}/santorini/", json=payload, headers=headers)
        print(f"Create Response: {r.status_code}")
        if r.status_code != 200:
            print(r.text)
            return

        game = r.json()
        print(f"Game Created: ID {game['id']}")
        
        print("\n2. Fetching Game...")
        r = requests.get(f"{BASE_URL}/santorini/{game['id']}", headers=headers)
        print(f"Get Response: {r.status_code}")
        print(r.json())
        
    except Exception as e:
        print(f"API Request Failed: {e}")

if __name__ == "__main__":
    token, uid = login()
    if token:
        print(f"Logged in as user {uid}")
        check_santorini(token, uid)
    else:
        print("Could not login. Is backend running?")
