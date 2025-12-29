import requests
import sys
import json

def debug_auth(base_url, username, password):
    print(f"--- Debugging Auth for {base_url} ---")
    print(f"Username: {username}")
    print(f"Password: {password}")

    # 1. Test Signup
    print("\n1. Testing Signup...")
    signup_url = f"{base_url}/auth/signup"
    try:
        r = requests.post(signup_url, json={"name": username, "password": password})
        print(f"Status: {r.status_code}")
        try:
            print(f"Response: {r.json()}")
        except:
            print(f"Response (text): {r.text}")
    except Exception as e:
        print(f"Request Failed: {e}")

    # 2. Test Login
    print("\n2. Testing Login...")
    login_url = f"{base_url}/auth/login"
    try:
        r = requests.post(login_url, json={"name": username, "password": password})
        print(f"Status: {r.status_code}")
        try:
            print(f"Response: {r.json()}")
        except:
            print(f"Response (text): {r.text}")
    except Exception as e:
        print(f"Request Failed: {e}")

if __name__ == "__main__":
    url = input("Enter API URL (default: http://100.92.153.101:8000): ").strip()
    if not url:
        url = "http://100.92.153.101:8000"
    
    user = input("Enter Username to test: ").strip()
    pwd = input("Enter Password: ").strip()
    
    debug_auth(url, user, pwd)
