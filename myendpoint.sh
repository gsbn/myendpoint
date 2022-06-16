# Script version
version="1.002"

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

# Get Monitor or Screen Status
if [ $distro = "ras" ]; then
    screenraw=`tvservice -s | awk '{ print $2 }'` 2>/dev/null
    if [ $screenraw = "0xa" ]; then
        screen="1" # On
    elif [ $screenraw = "0x2" ]; then
        screen="0" # Off
    else
        screen="-1" # None
    fi
elif [ $distro = "ubu" ] || [ $distro = "pop" ]; then
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
else
    screen=-2
fi

# Get Temp
if [ $distro = "ras" ]; then
    temp=`cat /sys/class/thermal/thermal_zone0/temp | awk '{ print $1/1000 }'` 2>/dev/null
elif [ $hard = "lenovo" ]; then
    temp=`cat /sys/class/thermal/thermal_zone2/temp | awk '{ print $1/1000 }'` 2>/dev/null
else
    temp=`cat /sys/class/thermal/thermal_zone0/temp | awk '{ print $1/1000 }'` 2>/dev/null
fi

# Return JSON
printf '{"hostname":"%s","ip":"%s","distro":"%s","hw":"%s","model":"%s","uptime":"%s","screen":"%s","temp":"%0.1f°C","version":"%s"}\n' "$hostname" "$ip" "$distro" "$hard" "$model" "$uptime" "$screen" "$temp" "$version"
