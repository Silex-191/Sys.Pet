#!/bin/bash

# Цвета для вывода
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Проверка наличия venv
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Виртуальное окружение не найдено!${NC}"
    echo -e "Запусти ${GREEN}./setup.sh${NC} для инициализации проекта"
    exit 1
fi

# Активируем виртуальное окружение
echo -e "${CYAN}[*] Активирую виртуальное окружение...${NC}"
source venv/bin/activate

# Запускаем FastAPI сервер через uvicorn в фоне
echo -e "${GREEN}🚀 Запускаю SysPet на http://localhost:8000${NC}"
echo -e "${YELLOW}[*] Нажми Ctrl+C чтобы остановить сервер${NC}"
echo ""

# Запускаем uvicorn в фоновом режиме
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload &
SERVER_PID=$!

# Даем серверу время на запуск (2 секунды)
sleep 2

# Автоматически открываем браузер
if command -v xdg-open &> /dev/null; then
    # Linux
    xdg-open http://localhost:8000
elif command -v open &> /dev/null; then
    # macOS
    open http://localhost:8000
elif command -v start &> /dev/null; then
    # Windows
    start http://localhost:8000
else
    echo -e "${YELLOW}⚠️  Не удалось автоматически открыть браузер${NC}"
    echo -e "Открой вручную: ${GREEN}http://localhost:8000${NC}"
fi

# Ждем, пока пользователь нажмет Ctrl+C
wait $SERVER_PID
