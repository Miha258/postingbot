#!/bin/bash

dir=$(pwd | sed 's/^\///')

for p in /proc/[0-9]*; do
    cmdline=$(cat "$p/cmdline" 2>/dev/null | tr '\0' ' ')
    if [[ "$dir" == "/$cmdline" ]]; then
        pid="${p#/proc/}"
        echo "Killing process with PID $pid"
        kill "$pid"
    fi
done

nohup python3 main.py &