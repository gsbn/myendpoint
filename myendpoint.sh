# Script version
version="1.005"

# Get hostname
hostname=`hostname` 2>/dev/null

# Get IP
ip=`ip route get 1.1.1.1 | sed -n '/src/{s/.*src *\([^ ]*\).*/\1/p;q}'` 2>/dev/null

# Get Distro (Tested on ras,ubu,pop)
distro=`awk -F= '$1=="ID" { print $2 ;}' /etc/os-release` 2>/dev/null
if [ $distro = "raspbian" ]; then
    distro="ras"
elif [ $distro = "ubuntu" ]; then
    distro="ubu"
fi

# Get Uptime
uptime=`uptime -p | cut -c 4-` 2>/dev/null

# Get Hardware
if [ $distro = "ras" ]; then
    hard="rpi"
    model=`cat /proc/device-tree/model | sed 's/Raspberry //' | tr -d '\0'` 2>/dev/null
else
    hard=`sudo dmidecode | grep -A3 '^System Information' | grep 'Manufacturer:' | awk '{print tolower($2)}'` 2>/dev/null
    model=""
fi

# Get UI
if [ $distro = "ras" ]; then
    ui="none"
elif [ $distro = "ubu" ]; then
    uiraw=`loginctl show-session 1 -p Type | sed 's/Type=//'` 2>/dev/null
    if [ -z $uiraw ]; then
        ui="none" # None or Error
    elif [ $uiraw = "x11" ]; then
        ui="x11" # x11
    elif [ $uiraw = "wayland" ]; then
        ui="wayland" # Wayland
    else
        ui="none" # Error with string
    fi
elif [ $distro = "pop" ]; then
    uiraw=`loginctl show-session 2 -p Type | sed 's/Type=//'` 2>/dev/null
    if [ -z $uiraw ]; then
        ui="none" # None or Error
    elif [ $uiraw = "x11" ]; then
        ui="x11" # x11
    elif [ $uiraw = "wayland" ]; then
        ui="wayland" # Wayland
    else
        ui="none" # Error with string
    fi
fi

# Get Monitor or Screen Status
if [ $distro = "ras" ]; then
    # Raspberry Pi Screen status
    screenraw=`tvservice -s | awk '{ print $2 }'` 2>/dev/null
    if [ -z $screenraw ]; then
        screen="-1" # None or Error
    elif [ $screenraw = "0xa" ]; then
        screen="1" # On
    elif [ $screenraw = "0x2" ]; then
        screen="0" # Off
    else
        screen="-2" # Error with string
    fi
elif [ $distro = "ubu" ] && [ $ui = "wayland" ]; then
    # Ubuntu running Wayland screen status
    screenraw=`busctl --user get-property org.gnome.Mutter.DisplayConfig /org/gnome/Mutter/DisplayConfig org.gnome.Mutter.DisplayConfig PowerSaveMode | awk '{ print $2 }'` 2>/dev/null
    if [ -z $screenraw ]; then
        screen="-1" # None or Error
    elif [ $screenraw = "0" ]; then
        screen="1" # On
    elif [ $screenraw = "1" ]; then
        screen="0" # Off
    fi
elif [ $distro = "ubu" ] && [ $ui = "x11" ]; then
    # Ubuntu running x11 screen status
    screenraw=`xset -display :0.0 q | grep -Po 'Monitor is \s*\K.*'` 2>/dev/null
    if [ -z $screenraw ]; then
        screen="-1" # None or Error
    elif [ $screenraw = "On" ]; then
        screen="1" # On
    elif [ $screenraw = "Off" ]; then
        screen="0" # Off
    else
        screen="-2" # Error with string
    fi
elif [ $distro = "pop" ]; then
    # Pop screen status
    screenraw=`xset -display :1.0 q | grep -Po 'Monitor is \s*\K.*'` 2>/dev/null
    if [ -z $screenraw ]; then
        screen="-1" # None or Error
    elif [ $screenraw = "On" ]; then
        screen="1" # On
    elif [ $screenraw = "Off" ]; then
        screen="0" # Off
    else
        screen="-2" # Error with string
    fi

else
    screen=-2
fi

# Get Temp
if [ $distro = "ras" ]; then
    temp=`cat /sys/class/thermal/thermal_zone0/temp | awk '{ print $1/1000 }'` 2>/dev/null
elif [ $hard = "lenovo" ] && [ $ui = "x11" ]; then
    temp=`cat /sys/class/thermal/thermal_zone2/temp | awk '{ print $1/1000 }'` 2>/dev/null
else
    temp=`cat /sys/class/thermal/thermal_zone0/temp | awk '{ print $1/1000 }'` 2>/dev/null
fi

# Check systemctl service is running
service=`systemctl is-active ruuvi.service` 2>/dev/null
if [ $service = "active" ]; then
    service="1"
else
    service="0"
fi

# Return JSON
printf '{"hostname":"%s","ip":"%s","distro":"%s","hw":"%s","model":"%s","ui":"%s","uptime":"%s","screen":"%s","temp":"%0.1f°C","blestatus":"%s","version":"%s"}\n' "$hostname" "$ip" "$distro" "$hard" "$model" "$ui" "$uptime" "$screen" "$temp" "$service" "$version"
