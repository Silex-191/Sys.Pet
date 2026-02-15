#!/bin/bash

# Цвета
GREEN='\033[0;32m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${CYAN}=========================================${NC}"
echo -e "${CYAN}   👾 SYSPET: SETUP PROTOCOL 👾        ${NC}"
echo -e "${CYAN}=========================================${NC}\n"

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 не найден!${NC}"
    echo "Установи: sudo apt install python3 python3-pip python3-venv"
    exit 1
fi

echo -e "${GREEN}✅ Python3 найден: $(python3 --version)${NC}\n"

# Создание venv
echo -e "${GREEN}[1/4] Создание виртуального окружения...${NC}"
python3 -m venv venv

# Активация
echo -e "${GREEN}[2/4] Активация окружения...${NC}"
source venv/bin/activate

# Обновление pip
echo -e "${GREEN}[3/4] Обновление pip...${NC}"
pip install --upgrade pip setuptools wheel > /dev/null 2>&1

# Установка зависимостей
echo -e "${GREEN}[4/4] Установка зависимостей...${NC}"
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo -e "${RED}❌ requirements.txt не найден!${NC}"
    exit 1
fi

# Создание структуры (если нужна)
mkdir -p backend frontend/templates frontend/static

echo -e "\n${CYAN}=========================================${NC}"
echo -e "${CYAN}   ✅ SETUP COMPLETE                   ${NC}"
echo -e "${CYAN}=========================================${NC}\n"
echo -e "Запусти сервер командой:"
echo -e "${GREEN}./run.sh${NC}\n"