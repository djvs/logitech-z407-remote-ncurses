import asyncio
from bleak import BleakScanner

SERVICE_UUID = "0000fdc2-0000-1000-8000-00805f9b34fb"

async def main():
    scanner = BleakScanner(service_uuids=[SERVICE_UUID])

    print("Starting scanner...")
    try:
        await scanner.start()
        print("START SUCCEEDED")
    except Exception as e:
        print(f"START FAILED: {e}")
        return

    for i in range(10):
        await asyncio.sleep(1)

        print(f"\n--- {i + 1}s ---")
        print(f"Found: {len(scanner.discovered_devices)} devices")

        for device in scanner.discovered_devices:
            print(
                f"  {device.address} "
                f"name={device.name!r}"
            )

    print("\nStopping scanner...")
    try:
        await scanner.stop()
        print("STOP SUCCEEDED")
    except Exception as e:
        print(f"STOP FAILED: {e}")


asyncio.run(main())
