import asyncio
from pyrogram import Client
from os import getenv
from dotenv import load_dotenv

load_dotenv()

async def generate():
    print()
    print("╔══════════════════════════════════════════════════╗")
    print("║   Pyrogram Session String Generator              ║")
    print("║   Get API credentials: https://my.telegram.org   ║")
    print("╚══════════════════════════════════════════════════╝")
    print()

    api_id_val = getenv("API_ID")
    api_hash_val = getenv("API_HASH")
    if not api_id_val or not api_hash_val:
        api_id = int(input("  API_ID   : ").strip())
        api_hash = input("  API_HASH : ").strip()
    else:
        api_id = int(api_id_val)
        api_hash = api_hash_val
        print(f"  Using API_ID: {api_id}")
        print(f"  Using API_HASH: {api_hash}")

    print("\n  Starting Telegram client — you will receive an OTP...\n")
    async with Client(":memory:", api_id=api_id, api_hash=api_hash) as app:
        session_str = await app.export_session_string()
        print()
        print("╔══════════════════════════════════════════════════╗")
        print("║  ✅  SESSION STRING GENERATED                    ║")
        print("╚══════════════════════════════════════════════════╝")
        print()
        print(session_str)
        print()
        print("  ↑ Copy the string above and paste it as SESSION= in your .env\n")
        with open("generated_session.txt", "w") as f:
            f.write(session_str)
        print("  📄 Also saved to: generated_session.txt\n")

if __name__ == "__main__":
    asyncio.run(generate())
