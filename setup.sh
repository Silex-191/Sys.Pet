#!/bin/bash

set -e

GREEN='\033[0;32m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

echo -e "${CYAN}=========================================${NC}"
echo -e "${CYAN}   👾 SYSPET: SETUP PROTOCOL 👾        ${NC}"
echo -e "${CYAN}=========================================${NC}\n"

# 1. Python
echo -e "${GREEN}[1/5] Проверка Python...${NC}"
if ! command -v python3 &>/dev/null; then
    echo -e "${RED}Python3 не найден, устанавливаю...${NC}"
    sudo apt update && sudo apt install -y python3 python3-pip python3-venv
fi
echo -e "${GREEN}✅ $(python3 --version)${NC}"

# 2. stress-ng
echo -e "${GREEN}[2/5] Проверка stress-ng...${NC}"
if ! command -v stress-ng &>/dev/null; then
    sudo apt install -y stress-ng
fi
echo -e "${GREEN}✅ stress-ng OK${NC}"

# 3. Venv
echo -e "${GREEN}[3/5] Создание venv...${NC}"
rm -rf "$DIR/venv"
python3 -m venv "$DIR/venv" --clear
# Гарантируем наличие pip в venv
"$DIR/venv/bin/python3" -m ensurepip --upgrade 2>/dev/null || true
"$DIR/venv/bin/python3" -m pip install --upgrade pip setuptools wheel

# 4. Зависимости
echo -e "${GREEN}[4/5] Установка зависимостей...${NC}"
"$DIR/venv/bin/python3" -m pip install -r "$DIR/requirements.txt"

# Проверка uvicorn
if ! "$DIR/venv/bin/python3" -c "import uvicorn" 2>/dev/null; then
    echo -e "${RED}❌ uvicorn не установился, пробую отдельно...${NC}"
    "$DIR/venv/bin/python3" -m pip install uvicorn
fi
echo -e "${GREEN}✅ uvicorn OK${NC}"

# 5. Структура
echo -e "${GREEN}[5/5] Структура папок...${NC}"
mkdir -p backend frontend/templates frontend/static frontend/static/emotions
chmod +x run.sh

echo -e "\n${CYAN}=========================================${NC}"
echo -e "${CYAN}   ✅ SETUP COMPLETE                   ${NC}"
echo -e "${CYAN}=========================================${NC}"
echo -e "\nЗапусти сервер: ${GREEN}./run.sh${NC}\n"