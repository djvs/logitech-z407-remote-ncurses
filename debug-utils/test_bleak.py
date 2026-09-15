import asyncio
from bleak import BleakScanner


async def main():
    scanner = BleakScanner()

    print("Starting scanner...")
    await scanner.start()
    print("START SUCCEEDED")

    for i in range(10):
        await asyncio.sleep(1)

        print(f"\n--- {i + 1}s ---")
        print(f"Found: {len(scanner.discovered_devices)} devices")

        for device in scanner.discovered_devices:
            print(f"  {device.address}  {device.name!r}")

    print("\nStopping scanner...")
    try:
        await scanner.stop()
        print("STOP SUCCEEDED")
    except Exception as e:
        print(f"STOP FAILED: {e}")


asyncio.run(main())
