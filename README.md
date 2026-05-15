# Logitech Z407 Remote - ncurses version

Based on https://github.com/androrama/Logitech-Z407-Remote-Control-Web-App---Linux but slimmed down to run in console without a web interface & removing pyautogui dependency.  

Requires bluez (bluetoothd) to be running, and bleak python package.  You can run the python script with sudo (`python app.py`), run the dist/app version as sudo, or more properly, copy the dist/app version where you want, and then grant it permissions for bluetooth access with setcap, e.g.:

```
sudo setcap cap_net_raw,cap_net_admin+eip z407-cli
```
