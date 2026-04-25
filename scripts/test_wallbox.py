#!/usr/bin/env python3
"""Standalone script to test Wallbox API authentication and status.
Usage: python scripts/test_wallbox.py
Requires WALLBOX_EMAIL, WALLBOX_PASSWORD, WALLBOX_CHARGER_ID in .env
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from integrations.wallbox.pulsar import WallboxClient

async def main():
    charger_id = os.environ["WALLBOX_CHARGER_ID"]
    email = os.environ["WALLBOX_EMAIL"]
    password = os.environ["WALLBOX_PASSWORD"]

    print(f"Authenticating as {email}...")
    client = WallboxClient(charger_id=charger_id, email=email, password=password)

    try:
        token = await client._authenticate()
        print(f"Token obtained: {token[:20]}...")

        print(f"\nFetching status for charger {charger_id}...")
        status = await client.get_status()

        print("\n--- Charger status ---")
        for key, value in status.items():
            print(f"  {key}: {value}")
    finally:
        await client.close()

asyncio.run(main())
