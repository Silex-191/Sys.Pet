#!/bin/bash

# Цвета
GREEN='\033[0;32m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${CYAN}=========================================${NC}"
echo -e "${CYAN}   👾 SYSPET: SETUP PROTOCOL 👾        ${NC}"
echo -e "${CYAN}=========================================${NC}\n"

# Установка системных зависимостей
echo -e "${GREEN}[1/7] Проверка системных зависимостей...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 не найден! Устанавливаю...${NC}"
    sudo apt update && sudo apt install -y python3 python3-pip python3-venv
fi
echo -e "${GREEN}✅ Python3 найден: $(python3 --version)${NC}"

# Установка stress-ng для стресс-тестов CPU
if ! command -v stress-ng &> /dev/null; then
    echo -e "${GREEN}Устанавливаю stress-ng для стресс-тестов CPU...${NC}"
    sudo apt install -y stress-ng
fi
echo -e "${GREEN}✅ stress-ng установлен${NC}\n"

# Создание venv
echo -e "${GREEN}[2/7] Создание виртуального окружения...${NC}"
python3 -m venv venv

# Активация
echo -e "${GREEN}[3/7] Активация окружения...${NC}"
source venv/bin/activate

# Обновление pip
echo -e "${GREEN}[4/7] Обновление pip...${NC}"
pip install --upgrade pip setuptools wheel > /dev/null 2>&1

# Установка зависимостей
echo -e "${GREEN}[5/7] Установка зависимостей...${NC}"
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo -e "${RED}❌ requirements.txt не найден!${NC}"
    exit 1
fi

# Создание структуры (если нужна)
echo -e "${GREEN}[6/7] Создание необходимой структуры папок...${NC}"
mkdir -p backend frontend/templates frontend/static frontend/static/emotions

# Настройка прав доступа
echo -e "${GREEN}[7/7] Настройка прав доступа для run.sh...${NC}"
chmod +x run.sh

echo -e "\n${CYAN}=========================================${NC}"
echo -e "${CYAN}   ✅ SETUP COMPLETE                   ${NC}"
echo -e "${CYAN}=========================================${NC}\n"
echo -e "Запусти сервер командой:"
echo -e "${GREEN}./run.sh${NC}\n"