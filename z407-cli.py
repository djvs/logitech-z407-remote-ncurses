#!/usr/bin/env python3

# based on https://github.com/androrama/Logitech-Z407-Remote-Control-Web-App---Linux

import os
import asyncio
import curses
import traceback

from bleak import BleakClient, BleakGATTCharacteristic


debug_val = os.getenv("DEBUG")


# Z407
Z407_ADDRESS = "D3:81:93:E9:DA:7A"
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


class Z407App:
    def __init__(self, stdscr):
        self.stdscr = stdscr

        self.client = None
        self.connected = False

        self.logs = []
        self.keycode_logs = []

        self.connect_lock = asyncio.Lock()
        self.reconnect_task = None

    def log(self, msg):
        self.logs.append(msg)

        if len(self.logs) > 500:
            self.logs = self.logs[-500:]

        self.redraw()

    def log_keycode(self, msg):
        self.keycode_logs.append(msg)

        if len(self.keycode_logs) > 500:
            self.keycode_logs = self.keycode_logs[-500:]

        self.redraw()

    def redraw(self):
        self.stdscr.erase()

        h, w = self.stdscr.getmaxyx()

        status = "CONNECTED" if self.connected else "DISCONNECTED"

        header = f"Z407 remote curses | {status}"

        self.stdscr.addstr(
            0,
            0,
            header[:w - 1],
            curses.color_pair(4),
        )

        help_line = (
            "+/- vol  |  "
            "[ ] bass  |  "
            "space play  |  "
            "n/p next prev  |  "
            "b bluetooth input  |  "
            "a aux input  |  "
            "u usb input  |  "
            "P pair  |  "
            "R reset  |  "
            "q quit"
        )

        self.stdscr.addstr(
            1,
            0,
            help_line[:w - 1],
            curses.color_pair(1),
        )

        split = int(w * 0.3)
        left_w = split
        right_w = w - split - 1

        # vertical divider
        for y in range(2, h):
            self.stdscr.addstr(
                y,
                split,
                "|",
                curses.color_pair(4),
            )

        # left column (logs)
        start_logs = max(0, len(self.logs) - (h - 3))
        visible_logs = self.logs[start_logs:]

        for idx, line in enumerate(visible_logs):
            y = idx + 3

            if y >= h:
                break

            self.stdscr.addstr(
                y,
                0,
                line[:left_w - 1],
            )

        # right column (command log)
        start_keys = max(0, len(self.keycode_logs) - (h - 3))
        visible_keys = self.keycode_logs[start_keys:]

        for idx, line in enumerate(visible_keys):
            y = idx + 3

            if y >= h:
                break

            self.stdscr.addstr(
                y,
                split + 2,
                line[:right_w - 1],
                curses.color_pair(3),
            )

        self.stdscr.refresh()

    async def notification_handler(
        self,
        sender: BleakGATTCharacteristic,
        data: bytearray,
    ):
        if debug_val:
            self.log(f"RX {data.hex()}")

        # keepalive request
        if data == b"\xd4\x05\x01":
            self.log("Keepalive requested")
            await self.send_raw(COMMANDS["keepalive_ack"])

        # protocol handshake complete
        elif data == b"\xd4\x00\x01":
            self.connected = True
            self.log("Handshake complete")

    async def connect(self):
        async with self.connect_lock:
            if self.client and self.client.is_connected:
                self.connected = True
                return True

            self.connected = False

            try:
                self.log(f"Connecting to {Z407_ADDRESS}...")

                # clean up an old client if one exists
                if self.client:
                    try:
                        if self.client.is_connected:
                            await self.client.disconnect()
                    except Exception:
                        pass

                self.client = BleakClient(Z407_ADDRESS)

                await self.client.connect()

                self.log("BLE connected")

                await self.client.start_notify(
                    RESPONSE_UUID,
                    self.notification_handler,
                )

                self.log("Notify enabled")

                # initiate protocol handshake
                await self.send_raw(COMMANDS["hello"])

                # give the speaker time to respond to "hello"
                await asyncio.sleep(1.0)

                self.connected = True

                self.log("Protocol ready")

                return True

            except Exception as e:
                self.connected = False

                self.log(f"CONNECT ERROR: {e}")

                if debug_val:
                    self.log(traceback.format_exc())

                return False

    async def send_raw(self, hexcmd):
        if not self.client or not self.client.is_connected:
            raise ConnectionError("BLE client is not connected")

        if debug_val:
            self.log(f"TX {hexcmd}")

        payload = bytes.fromhex(hexcmd)

        await self.client.write_gatt_char(
            COMMAND_UUID,
            payload,
            response=False,
        )

    async def send(self, command):
        if not self.client or not self.client.is_connected:
            self.connected = False

        if not self.connected:
            if not await self.connect():
                return

        try:
            await self.send_raw(COMMANDS[command])

        except Exception as e:
            self.connected = False
            self.log(f"SEND ERROR: {e}")

    async def reconnect_loop(self):
        try:
            while True:
                if self.client and not self.client.is_connected:
                    self.connected = False

                if not self.connected:
                    await self.connect()

                await asyncio.sleep(5)

        except asyncio.CancelledError:
            raise

    async def loop(self):
        curses.curs_set(0)

        self.stdscr.nodelay(True)
        self.stdscr.keypad(True)

        self.redraw()

        self.reconnect_task = asyncio.create_task(
            self.reconnect_loop()
        )

        try:
            while True:
                key = self.stdscr.getch()

                if key != -1:
                    if key == ord("q"):
                        break

                    cmd = KEYBINDS.get(key)

                    if cmd:
                        self.log_keycode(cmd)
                        await self.send(cmd)

                await asyncio.sleep(0.01)

        finally:
            if self.reconnect_task:
                self.reconnect_task.cancel()

                try:
                    await self.reconnect_task
                except asyncio.CancelledError:
                    pass

            if self.client:
                try:
                    if self.client.is_connected:
                        await self.client.disconnect()
                except Exception:
                    pass


async def async_main(stdscr):
    curses.start_color()
    curses.use_default_colors()

    curses.init_pair(1, curses.COLOR_RED, -1)
    curses.init_pair(2, curses.COLOR_GREEN, -1)
    curses.init_pair(3, curses.COLOR_WHITE, -1)
    curses.init_pair(4, curses.COLOR_BLUE, -1)

    stdscr.bkgd(" ", curses.color_pair(2))

    app = Z407App(stdscr)

    await app.loop()


def main(stdscr):
    asyncio.run(async_main(stdscr))


if __name__ == "__main__":
    curses.wrapper(main)
