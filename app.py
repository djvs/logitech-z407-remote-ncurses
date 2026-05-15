#!/usr/bin/env python3

# based on https://github.com/androrama/Logitech-Z407-Remote-Control-Web-App---Linux 

import os
import asyncio
import curses
import traceback

from bleak import (
    BleakClient,
    BleakScanner,
    BleakGATTCharacteristic,
)

debug_val = os.getenv("DEBUG")

# z407 uuids
SERVICE_UUID = "0000fdc2-0000-1000-8000-00805f9b34fb"
COMMAND_UUID = "c2e758b9-0e78-41e0-b0cb-98a593193fc5"
RESPONSE_UUID = "b84ac9c6-29c5-46d4-bba1-9d534784330f"

# commands
COMMANDS = {

    # speaker volume
    "volume_up": "8002",
    "volume_down": "8003",

    # bass
    "bass_up": "8000",
    "bass_down": "8001",

    # speaker playback
    "play_pause": "8004",
    "next_track_speaker": "8005",
    "prev_track_speaker": "8006",

    # inputs
    "input_bluetooth": "8101",
    "input_aux": "8102",
    "input_usb": "8103",

    # pairing/reset
    "bluetooth_pair": "8200",
    "factory_reset": "8300",

    # protocol
    "hello": "8405",
    "keepalive_ack": "8400",
}

# keybinds
KEYBINDS = {
    # volume
    ord("+"): "volume_up",
    ord("="): "volume_up",

    ord("-"): "volume_down",
    ord("_"): "volume_down",

    # bass
    ord("["): "bass_down",
    ord("]"): "bass_up",

    # speaker transport
    ord(" "): "play_pause",

    ord("n"): "next_track_speaker",
    ord("p"): "prev_track_speaker",

    # inputs
    ord("b"): "input_bluetooth",
    ord("a"): "input_aux",
    ord("u"): "input_usb",

    # pairing/reset
    ord("P"): "bluetooth_pair",
    ord("R"): "factory_reset",
}

# main app
class Z407App:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.client = None
        self.device = None
        self.connected = False
        self.logs = []
        self.lock = asyncio.Lock()

    def log(self, msg):
        self.logs.append(msg)
        if len(self.logs) > 500:
            self.logs = self.logs[-500:]
        self.redraw()

    def redraw(self):
        self.stdscr.erase()
        h, w = self.stdscr.getmaxyx()

        status = "CONNECTED" if self.connected else "DISCONNECTED"

        header = f"Z407 remote curses | {status}"
        
        self.stdscr.addstr(
            0,
            0,
            header[:w - 1]
        )

        help_line = (
            "+/- vol  | "
            "[] bass  | "
            "space play  | "
            "n/p next prev  | "
            "b/a/u input  | "
            "P pair  | "
            "R reset  | "
            "q quit"
        )

        self.stdscr.addstr(
            1,
            0,
            help_line[:w - 1]
        )

        start = max( 0, len(self.logs) - (h - 3))

        visible = self.logs[start:]

        for idx, line in enumerate(visible):
            y = idx + 3
            if y >= h:
                break
            self.stdscr.addstr(
                y,
                0,
                line[:w - 1]
            )

        self.stdscr.refresh()

    async def discover(self):
        self.log("Scanning for Z407...")

        devices = await BleakScanner.discover(
            service_uuids=[SERVICE_UUID],
            timeout=5.0,
        )

        for d in devices:

            self.log(
                f"FOUND "
                f"{d.address} "
                f"{d.name}"
            )

            return d

        return None

    async def notification_handler(
        self,
        sender: BleakGATTCharacteristic,
        data: bytearray,
    ):
        hexdata = data.hex()

        if debug_val:
            self.log(f"RX {hexdata}")

        # keepalive request
        if data == b"\xd4\x05\x01":
            self.log("Keepalive requested")

            await self.send_raw(
                COMMANDS[
                    "keepalive_ack"
                ]
            )

        elif data == b"\xd4\x00\x01":
            self.connected = True

            self.log("Handshake complete")

    async def connect(self):
        async with self.lock:
            if self.connected:
                return True

            try:
                self.device = (
                    await self.discover()
                )

                if not self.device:
                    self.log("Device not found")

                    return False

                self.log(
                    f"Connecting "
                    f"{self.device.address}"
                )

                self.client = BleakClient(
                    self.device.address
                )

                await self.client.connect()

                self.log("BLE connected")

                # notifications required
                await self.client.start_notify(
                    RESPONSE_UUID,
                    self.notification_handler,
                )

                self.log("Notify enabled")

                # handshake required
                await self.send_raw(
                    COMMANDS["hello"]
                )

                # wait for handshake
                await asyncio.sleep(1.0)

                self.connected = True

                self.log("Protocol ready")

                return True

            except Exception as e:
                self.connected = False

                self.log(f"CONNECT ERROR: {e}")

                self.log(traceback.format_exc())

                return False

    async def send_raw(self, hexcmd):
        if not self.client:
            return

        payload = bytes.fromhex(
            hexcmd
        )

        if debug_val:
            self.log(f"TX {hexcmd}")

        await self.client.write_gatt_char(
            COMMAND_UUID,
            payload,
            response=False,
        )

    async def send(self, command):
        if not self.connected:
            ok = await self.connect()
            if not ok:
                return

        try:
            await self.send_raw(COMMANDS[command])

        except Exception as e:
            self.connected = False

            self.log(f"SEND ERROR: {e}")

    async def reconnect_loop(self):
        while True:
            try:
                if (
                    self.client
                    and
                    not self.client.is_connected
                ):
                    self.connected = False

                if not self.connected:
                    await self.connect()

            except Exception as e:
                self.connected = False
                self.log(f"Reconnect: {e}")

            await asyncio.sleep(5)

    async def loop(self):
        curses.curs_set(0)

        self.stdscr.nodelay(True)
        self.stdscr.keypad(True)

        self.redraw()

        asyncio.create_task(
            self.reconnect_loop()
        )

        while True:
            key = self.stdscr.getch()
            if key != -1:
                if key == ord("q"):
                    break
                cmd = KEYBINDS.get(key)
                if cmd:
                    self.log(cmd)

                    await self.send(cmd)
            await asyncio.sleep(0.01)

        if self.client:
            try:
                await self.client.disconnect()
            except:
                pass

# main
async def async_main(stdscr):
    app = Z407App(stdscr)

    await app.loop()

def main(stdscr):
    asyncio.run(async_main(stdscr))

if __name__ == "__main__":
    curses.wrapper(main)
