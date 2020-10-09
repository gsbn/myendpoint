# Get hostname
hostname=`hostname` 2>/dev/null

# Get IP
ip=`ip route get 1.1.1.1 | sed -n '/src/{s/.*src *\([^ ]*\).*/\1/p;q}'` 2>/dev/null

# Get Distro
distro=`awk -F= '$1=="ID" { print $2 ;}' /etc/os-release` 2>/dev/null

# Get Uptime
uptime=`uptime -p | cut -c 4-` 2>/dev/null

# Get Monitor or Screen Status
if [ $distro = "raspbian" ]; then
    screenraw=`tvservice -s | awk '{ print $2 }'` 2>/dev/null
    if [ $screenraw = "0xa" ]; then
        screen="ON"
    elif [ $screenraw = "0x2" ]; then
        screen="OFF"
    fi
elif [ $distro = "pop" ]; then
    screen=-2
else
    screen=-1
fi

# Get Temp
if [ $distro = "raspbian" ]; then
    temp=`cat /sys/class/thermal/thermal_zone0/temp | awk '{ print $1/1000 }'` 2>/dev/null
else
    temp=0
fi

# Return JSON
printf '{"hostname":"%s","ip":"%s","distro":"%s","uptime":"%s","screen":"%s","temp":"%0.1f°C"}\n' "$hostname" "$ip" "$distro" "$uptime" "$screen" "$temp"
