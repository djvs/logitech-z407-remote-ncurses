import asyncio
from bleak import BleakScanner


def detection_callback(device, adv):
    print(
        f"{device.address} "
        f"name={device.name!r} "
        f"local_name={adv.local_name!r} "
        f"uuids={adv.service_uuids} "
        f"service_data={adv.service_data}"
    )


async def main():
    scanner = BleakScanner(detection_callback=detection_callback)

    print("Starting scanner...")
    await scanner.start()
    print("START SUCCEEDED")

    await asyncio.sleep(10)

    print("Stopping scanner...")
    try:
        await scanner.stop()
        print("STOP SUCCEEDED")
    except Exception as e:
        print(f"STOP FAILED: {e}")


asyncio.run(main())
