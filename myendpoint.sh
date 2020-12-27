# Script version
version="1.001"

# Get hostname
hostname=`hostname` 2>/dev/null

# Get IP
ip=`ip route get 1.1.1.1 | sed -n '/src/{s/.*src *\([^ ]*\).*/\1/p;q}'` 2>/dev/null

# Get Distro
distro=`awk -F= '$1=="ID" { print $2 ;}' /etc/os-release` 2>/dev/null
if [ $distro = "raspbian" ]; then
    distro="ras"
elif [ $distro = "ubuntu" ]; then
    distro="ubu"
fi

# Get Uptime
uptime=`uptime -p | cut -c 4-` 2>/dev/null

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
elif [ $distro = "ubu" ]; then
    screenraw=`xset -display :0.0 q | grep -Po 'Monitor is \s*\K.*'` 2>/dev/null
    if [ $screenraw = "On" ]; then
        screen="1" # On
    elif [ $screenraw = "Off" ]; then
        screen="0" # Off
    else
        screen="-1" # None
    fi
else
    screen=-2
fi

# Get Temp
if [ $distro = "ras" ]; then
    temp=`cat /sys/class/thermal/thermal_zone0/temp | awk '{ print $1/1000 }'` 2>/dev/null
elif [ $distro = "ubu" ]; then
    temp=`cat /sys/class/thermal/thermal_zone2/temp | awk '{ print $1/1000 }'` 2>/dev/null
else
    temp=-1
fi

# Return JSON
printf '{"hostname":"%s","ip":"%s","distro":"%s","uptime":"%s","screen":"%s","temp":"%0.1f°C","version":"%s"}\n' "$hostname" "$ip" "$distro" "$uptime" "$screen" "$temp" "$version"
