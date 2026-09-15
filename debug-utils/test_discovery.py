import asyncio
from bleak import BleakScanner

SERVICE_UUID = "0000fdc2-0000-1000-8000-00805f9b34fb"


async def main():
    print("Scanning...")

    devices = await BleakScanner.discover(
        timeout=5,
        service_uuids=[SERVICE_UUID],
    )

    print()
    print("Results:")
    print()

    for device in devices:
        print(device)


asyncio.run(main())
