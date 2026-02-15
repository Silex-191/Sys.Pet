#!/bin/bash

# Цвета
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Проверка venv
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ venv не найдено!${NC}"
    echo -e "Запусти сначала: ${GREEN}./setup.sh${NC}"
    exit 1
fi

# Информация
echo -e "${CYAN}=========================================${NC}"
echo -e "${CYAN}   🎮 SysPet Server Starting 🎮        ${NC}"
echo -e "${CYAN}=========================================${NC}\n"

echo -e "${GREEN}✅ Virtual environment activated${NC}"
echo -e "${GREEN}✅ Backend: backend/main.py${NC}"
echo -e "${GREEN}✅ Frontend: frontend/templates/index.html${NC}"
echo -e "\n${YELLOW}🚀 Starting uvicorn on http://localhost:8000${NC}"
echo -e "${YELLOW}📝 API docs: http://localhost:8000/docs${NC}"
echo -e "${YELLOW}⚠️  Running with sudo for process management${NC}"
echo -e "${YELLOW}⛔ Stop: Ctrl+C\n${NC}"

# Запуск сервера с sudo для возможности убивать любые процессы
sudo venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload