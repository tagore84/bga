import sys
import os
import asyncio
import socket

# Add backend to path to reuse auth logic
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

try:
    from app.utils.auth import hash_password
except ImportError:
    print("Error: Could not import backend modules.")
    print("Make sure you are running this from the project root (e.g., python3 scripts/reset_remote_password.py)")
    sys.exit(1)

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def reset_password(host, port, username, new_password):
    print(f"\n--- Resetting Password for '{username}' on {host}:{port} ---")
    
    # 1. Database Connection URL
    # Assuming default credentials from docker-compose: user=bga, pass=secret, db=bga
    # If these were changed, this script needs to be updated.
    database_url = f"postgresql+asyncpg://bga:secret@{host}:{port}/bga"
    
    print(f"Connecting to database...")
    try:
        engine = create_async_engine(database_url, echo=False)
        async with engine.begin() as conn:
            # 2. Check if user exists
            result = await conn.execute(text("SELECT id, name FROM players WHERE name = :name"), {"name": username})
            user = result.fetchone()
            
            if not user:
                print(f"❌ User '{username}' not found in database.")
                return

            print(f"User found: ID {user.id}")

            # 3. Hash new password
            print("Hashing new password...")
            hashed_pwd = hash_password(new_password)

            # 4. Update password
            print("Updating database...")
            await conn.execute(
                text("UPDATE players SET hashed_password = :pwd WHERE name = :name"),
                {"pwd": hashed_pwd, "name": username}
            )
            print(f"✅ Password for '{username}' has been successfully updated.")

    except Exception as e:
        print(f"❌ Error: {e}")
        print("Tip: Ensure you have a valid connection to the NAS database port (usually 5432 or 5433).")
        print("Tip: Ensure you have dependencies installed: pip install sqlalchemy asyncpg passlib bcrypt")

if __name__ == "__main__":
    # Defaults
    DEFAULT_HOST = "100.92.153.101"
    
    # Interactive Prompts
    host = input(f"Enter NAS IP (default: {DEFAULT_HOST}): ").strip() or DEFAULT_HOST
    
    port_str = input("Enter DB Port (default: 5432): ").strip() or "5432"
    try:
        port = int(port_str)
    except ValueError:
        print("Invalid port")
        sys.exit(1)

    username = input("Enter Username to reset: ").strip()
    if not username:
        print("Username is required")
        sys.exit(1)
        
    new_password = input("Enter New Password: ").strip()
    if not new_password:
        print("Password is required")
        sys.exit(1)

    # Run Async
    asyncio.run(reset_password(host, port, username, new_password))
