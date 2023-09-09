#!/bin/bash

TARGET_PROCESS="python3.*bot/main.py"
PIDS=$(ps aux | grep "$TARGET_PROCESS" | grep -v 'grep' | awk '{print $2}')

if [ -z "$PIDS" ]; then
  echo "No processes found matching the criteria."
else
  MAIN_P=$(ps -o ppid= -p ${PIDS[0]})
  echo $MAIN_P
  kill "$MAIN_P"
  for PID in $PIDS; do
    echo "Killing process with PID: $PID"
    kill "$PID"
  done
  echo "Processes have been killed."
fi

nohup python3 main.py &