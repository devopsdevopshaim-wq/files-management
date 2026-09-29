#!/bin/bash

# צבעים
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}התקנת מערכת אירוח HTML...${NC}"

# בדיקת Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python3 לא מותקן. מתקין...${NC}"
    sudo apt update && sudo apt install -y python3 python3-pip
fi

# בדיקת Docker
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}Docker לא מותקן. רוצה להתקין? (y/n)${NC}"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh
        sudo usermod -aG docker $USER
        rm get-docker.sh
    fi
fi

# יצירת סביבה וירטואלית
echo -e "${GREEN}יוצר סביבה וירטואלית...${NC}"
python3 -m venv venv
source venv/bin/activate

# התקנת תלויות
echo -e "${GREEN}מתקין תלויות Python...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# יצירת תיקיות
mkdir -p uploads static config logs

# מתן הרשאות
chmod +x server.py
chmod +x start.sh

echo -e "${GREEN}✅ ההתקנה הושלמה!${NC}"
echo ""
echo -e "${YELLOW}📖 הוראות שימוש:${NC}"
echo "1. להפעלת השרת: ${GREEN}./start.sh${NC}"
echo "2. לפתוח בדפדפן: ${GREEN}http://localhost:5000${NC}"
echo "3. להפעלת עם Docker: ${GREEN}docker-compose up -d${NC}"
echo ""
echo -e "${YELLOW}🔧 אפשרויות נוספות:${NC}"
echo "- שנה הגדרות ב-${GREEN}config.json${NC}"
echo "- העלה קבצים לתיקייה ${GREEN}uploads/${NC}"
echo "- צפה בלוגים: ${GREEN}tail -f logs/server.log${NC}"