#!/usr/bin/env python3

import asyncio
from bleak import BleakScanner

Z407_SERVICE_UUID = "0000fdc2-0000-1000-8000-00805f9b34fb"

async def main():
    print("Scanning for Z407...")
    print("Scanning for 10 seconds...\n")

    scanner = BleakScanner()

    await scanner.start()

    try:
        await asyncio.sleep(10)
    finally:
        try:
            await scanner.stop()
        except Exception as e:
            print(f"Scanner cleanup: {e}")

    matches = []

    for device in scanner.discovered_devices:
        # get the advertisement data for the device
        adv = scanner.discovered_devices_and_advertisement_data.get(
            device.address
        )

        if not adv:
            continue

        advertisement = adv[1]

        uuids = [
            uuid.lower()
            for uuid in advertisement.service_uuids
        ]

        if Z407_SERVICE_UUID in uuids:
            matches.append(device)

    if not matches:
        print("No Z407 found.")
        print("\nDevices seen:")

        for device in scanner.discovered_devices:
            print(f"  {device.address}  {device.name!r}")

        return

    print("Z407 found:\n")

    for device in matches:
        print(f"MAC:  {device.address}")
        print(f"Name: {device.name!r}")
        print(f"UUID: {Z407_SERVICE_UUID}")
        print()


if __name__ == "__main__":
    asyncio.run(main())
