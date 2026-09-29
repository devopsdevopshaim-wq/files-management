#!/bin/bash

RED='\033[0;31m'
NC='\033[0m'

if [ -f "server.pid" ]; then
    PID=$(cat server.pid)
    echo -e "${RED}עוצר שרת עם PID: $PID${NC}"
    kill $PID
    rm server.pid
    echo "✅ שרת נעצר"
else
    echo "לא נמצא קובץ PID. מנסה למצוא ולעצור..."
    pkill -f "python.*server.py"
    echo "✅ כל תהליכי השרת נעצרו"
fi