import os
import socket
import subprocess
import json
from datetime import datetime

# Script version
version = "1.200"

### Main
def main():

    # Get Hostname
    hostname = socket.gethostname()

    # Get IP
    ip = subprocess.check_output(["ip", "route", "get", "1.1.1.1"]).decode().split(" ")[6]

    # Get Uptime
    uptime = subprocess.check_output(["uptime", "-p"]).decode().strip()[3:]

    # Get Distro (Tested on ras,ubu,pop)
    distro = os.popen('grep "^ID=" /etc/os-release | cut -d "=" -f 2').read().strip()[0:3]

    # Get Hardware
    if distro == "ras":
        hard = "rpi"
        model = os.popen('cat /proc/device-tree/model | sed "s/Raspberry //"').read().strip().rstrip('\x00')
    else:
        hard = os.popen('sudo dmidecode | grep -A3 "^System Information" | grep "Manufacturer:" | awk \'{print tolower($2)}\'').read().strip()
        model = ""

    # Get UI
    if distro == "ras":
        ui = "none"
    elif distro == "ubu":
        uiraw = os.popen('loginctl show-session 1 -p Type | sed \'s/Type=//\' 2>/dev/null').read().strip()
        if not uiraw:
            ui = "none" # None or Error
        elif uiraw == "x11":
            ui = "x11" # x11
        elif uiraw == "wayland":
            ui = "wayland" # Wayland
        else:
            ui = "none" # Error with string
    elif distro == "pop":
        uiraw = os.popen('loginctl show-session 2 -p Type | sed \'s/Type=//\' 2>/dev/null').read().strip()
        if not uiraw:
            ui = "none" # None or Error
        elif uiraw == "x11":
            ui = "x11" # x11
        elif uiraw == "wayland":
            ui = "wayland" # Wayland
        else:
            ui = "none" # Error with string

    # Get Monitor or Screen Status
    if distro == "ras":
        # Raspberry Pi Screen status
        screenraw = os.popen('tvservice -s | awk \'{ print $2 }\' 2>/dev/null').read().strip()
        if not screenraw:
            screen = "-1" # None or Error
        elif screenraw == "0xa":
            screen = "1" # On
        elif screenraw == "0x2":
            screen = "0" # Off
        else:
            screen = "-2" # Error with string
    elif distro == "ubu" and ui == "wayland":
        # Ubuntu running Wayland screen status
        screenraw = os.popen('busctl --user get-property org.gnome.Mutter.DisplayConfig /org/gnome/Mutter/DisplayConfig org.gnome.Mutter.DisplayConfig PowerSaveMode | awk \'{ print $2 }\' 2>/dev/null').read().strip()
        if not screenraw:
            screen = "-1" # None or Error
        elif screenraw == "0":
            screen = "1" # On
        elif screenraw == "1":
            screen = "0" # Off
        else:
            screen = "-2" # Error with string
    elif distro == "ubu" and ui == "x11":
        # Ubuntu running x11 screen status
        screenraw = os.popen('xset -display :0.0 q | grep -Po \'Monitor is \s*\K.*\' 2>/dev/null').read().strip()
        if not screenraw:
            screen = "-1" # None or Error
        elif screenraw == "On":
            screen = "1" # On
        elif screenraw == "Off":
            screen = "0" # Off
        else:
            screen = "-2" # Error with string
    elif distro == "pop":
        # Pop screen status
        screenraw = os.popen('xset -display :1.0 q | grep -Po \'Monitor is \s*\K.*\' 2>/dev/null').read().strip()
        if not screenraw:
            screen = "-1" # None or Error
        elif screenraw == "On":
            screen = "1" # On
        elif screenraw == "Off":
            screen = "0" # Off
        else:
            screen = "-2" # Error with string
    else:
        screen = "-2"

    # Get Temp
    if distro == "ras":
        temp = float(os.popen('cat /sys/class/thermal/thermal_zone0/temp | awk \'{ print $1/1000 }\'').read().strip())
    elif hard == "lenovo" and ui == "x11":
        temp = float(os.popen('cat /sys/class/thermal/thermal_zone2/temp | awk \'{ print $1/1000 }\'').read().strip())
    elif hard == "lenovo" and ui == "wayland":
        temp = float(os.popen('cat /sys/class/thermal/thermal_zone0/temp | awk \'{ print $1/1000 }\'').read().strip())
    else:
        temp = float(0)

    # Check systemctl service is running
    service = os.popen('systemctl is-active ruuvi.service').read().strip()
    if service == "active":
        service = "1"
    else:
        service = "0"

    # Return JSON
    data = {
        "hostname": hostname,
        "ip": ip,
        "distro": distro,
        "hw": hard,
        "model": model,
        "ui": ui,
        "uptime": uptime,
        "screen": screen,
        "temp": f"{temp:.1f}°C",
        "blestatus": service,
        "timestamp": int((datetime.utcnow() - datetime(1970, 1, 1)).total_seconds()),
        "version": version
    }
    json_data = json.dumps(data, ensure_ascii=False)
    return(json_data)

if __name__ == "__main__":
    print(main())
