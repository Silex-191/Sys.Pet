#!/bin/bash

# Цвета для красоты
GREEN='\033[0;32m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${CYAN}=========================================${NC}"
echo -e "${CYAN}   👾 SYSPET: INSTALLATION PROTOCOL 👾   ${NC}"
echo -e "${CYAN}=========================================${NC}"

# 1. Проверка Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[ERROR] Python3 не найден! Установи его: sudo apt install python3${NC}"
    exit 1
fi

# 2. Создание виртуального окружения
echo -e "${GREEN}[+] Создаем изолированную капсулу (venv)...${NC}"
python3 -m venv venv

# 3. Активация и установка
echo -e "${GREEN}[+] Активация нейроинтерфейса...${NC}"
source venv/bin/activate

echo -e "${GREEN}[+] Инъекция зависимостей (pip install)...${NC}"
pip install --upgrade pip
pip install fastapi "uvicorn[standard]" psutil jinja2 pydantic requests

# 4. Создание структуры папок (если нет)
echo -e "${GREEN}[+] Проверка файловой системы...${NC}"
mkdir -p templates
mkdir -p static

# 5. Создание requirements.txt (для напарника)
pip freeze > requirements.txt
echo -e "${GREEN}[+] Список зависимостей сохранен в requirements.txt${NC}"

echo -e "${CYAN}=========================================${NC}"
echo -e "${CYAN}   💀 SYSTEM READY. DAEMON IS WAITING.   ${NC}"
echo -e "${CYAN}=========================================${NC}"
echo ""
echo -e "Чтобы запустить сервер, введи:"
echo -e "${GREEN}./run.sh${NC}"
