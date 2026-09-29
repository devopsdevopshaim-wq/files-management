#!/bin/bash

# צבעים
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}"
echo "╔══════════════════════════════════════════╗"
echo "║     מערכת אירוח HTML - מתחילה...        ║"
echo "╚══════════════════════════════════════════╝"
echo -e "${NC}"

# בדיקה אם השרת כבר רץ
if lsof -Pi :5000 -sTCP:LISTEN -t >/dev/null ; then
    echo -e "${BLUE}⚠️  השרת כבר רץ על פורט 5000${NC}"
    echo "רוצה לעצור ולאתחל מחדש? (y/n)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        echo "עוצר שרת ישן..."
        pkill -f "python.*server.py"
        sleep 2
    else
        echo "ממשיך עם שרת קיים..."
        exit 0
    fi
fi

# הפעלת השרת
source venv/bin/activate
nohup python server.py > logs/server.log 2>&1 &
SERVER_PID=$!

echo -e "${GREEN}✅ שרת הופעל עם PID: $SERVER_PID${NC}"
echo -e "${BLUE}📊 לוגים: tail -f logs/server.log${NC}"
echo -e "${BLUE}🌐 כתובת: http://localhost:5000${NC}"
echo -e "${BLUE}📁 קבצים: http://localhost:5000/files${NC}"
echo ""
echo -e "${GREEN}לעצירה: ./stop.sh${NC}"

# שמירת ה-PID לקובץ
echo $SERVER_PID > server.pid