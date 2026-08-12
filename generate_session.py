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

    print()
    print("  Starting Telegram client — you will receive an OTP...")
    print()

    async with Client(":memory:", api_id=api_id, api_hash=api_hash) as app:
        session = await app.export_session_string()

        print()
        print("╔══════════════════════════════════════════════════╗")
        print("║  ✅  SESSION STRING GENERATED                    ║")
        print("╚══════════════════════════════════════════════════╝")
        print()
        print(session)
        print()
        print("  ↑ Copy the string above and paste it as SESSION= in your .env")
        print()

        # Also save to a file for convenience
        with open("generated_session.txt", "w") as f:
            f.write(f"SESSION={session}\n")
        print("  📄 Also saved to: generated_session.txt")
        print()


asyncio.run(generate())
