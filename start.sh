#!/bin/bash

directory_path=$(dirname "$0")
pids=$(pgrep -f "python3 bot/main.py")

for pid in $pids; do
    cmd=$(ps -o cmd -p $pid --no-headers)

    if [[ "$cmd" == *"$directory_path"* ]]; then
        kill $pid
    fi
done