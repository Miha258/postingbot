#!/bin/bash

dir="root/postingbot"

for p in /proc/[0-9]*; do
    cwd=$(cat "$p/cmdline" 2>/dev/null | tr '\0' ' ')
    echo $cwd
    if [[ "$dir" == "$cwd" ]]; then
        pid="${p#/proc/}"
        echo "Killing process with PID $pid"
        kill "$pid"
    fi
done
nohup python3 main.py &