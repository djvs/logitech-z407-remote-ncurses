# Logitech Z407 Remote - ncurses version

Based on https://github.com/androrama/Logitech-Z407-Remote-Control-Web-App---Linux but slimmed down to run in console without a web interface & removing pyautogui dependency.  

Requires bluez (bluetoothd) to be running, and bleak python package.  Should be either run as root or python permissions for bluetooth access set appropriately with setcap, e.g.:

```
sudo setcap cap_net_raw+eip $(readlink -f dist/app)
```
