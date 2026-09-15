import asyncio
from bleak import BleakClient

ADDRESS = "D3:81:93:E9:DA:7A"


async def main():
    print(f"Connecting to {ADDRESS}...")

    async with BleakClient(ADDRESS) as client:
        print("CONNECTED")
        print(f"Services: {len(client.services.services)}")

        for service in client.services:
            print(f"\nSERVICE {service.uuid}")

            for char in service.characteristics:
                print(
                    f"  CHAR {char.uuid} "
                    f"properties={char.properties}"
                )


asyncio.run(main())
