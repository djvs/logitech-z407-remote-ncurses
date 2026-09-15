# Logitech Z407 Remote - ncurses version

Based on https://github.com/androrama/Logitech-Z407-Remote-Control-Web-App---Linux but slimmed down to run in console without a web interface & removing pyautogui dependency and need for special permissions.  

Requires bluez (bluetoothd) to be running, and bleak python package.  

I only tested this for myself - currently it relies on a hardcoded MAC address for the device.  Run `python find-mac-address.py` and change `Z407_ADDRESS` in `z407-cli.py` if the value is different.
