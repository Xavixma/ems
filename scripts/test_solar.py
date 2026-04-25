#!/usr/bin/env python3
"""Standalone script to test direct communication with the Hoymiles DTU.
Usage: python scripts/test_solar.py
Requires HOYMILES_DTU_IP in .env
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from hoymiles_wifi.dtu import DTU

async def main():
    ip = os.environ["HOYMILES_DTU_IP"]
    print(f"Connecting to DTU at {ip}...")
    dtu = DTU(host=ip)

    response = await dtu.async_get_real_data_new()
    if response is None:
        print("No response from DTU")
        return

    print("\n--- Raw response ---")
    print(response)

    print("\n--- Parsed ---")
    print(f"DC power:         {response.dtu_power} W")
    print(f"Today production: {response.dtu_daily_energy / 1000:.3f} kWh")
    for i, pv in enumerate(response.pv_data):
        print(f"PV {i} total:      {pv.energy_total / 1000:.1f} kWh")
    total = sum(pv.energy_total for pv in response.pv_data) / 1000.0
    print(f"Total production: {total:.1f} kWh")

asyncio.run(main())
