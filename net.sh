#!/usr/bin/env bash

tcp_conn() {
    exec 3<>/dev/tcp/$1/$2
}

tcp_close() {
    exec 3<&-
    exec 3>&-
}

tcp_send() {
    printf "$1" >&3
}

tcp_recv() {
    timeout ${1:-5} cat <&3
}

tcp_check_port() {
    tcp_conn $1 $2 2> /dev/null || return $?
    tcp_close
}

