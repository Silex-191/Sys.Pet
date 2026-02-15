import uvicorn
import psutil
import time
import re
import asyncio
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
from pathlib import Path

# --- Инициализация приложения ---
app = FastAPI()

# !!! ВАЖНО: Разрешаем CORS, чтобы фронтенд (HTML файл) мог стучаться к бэкенду
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешить всем (для хакатона ок)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- КОНФИГ ИГРЫ ---
XP_TO_NEXT_COURSE = 100
MAX_WEIGHT_RAM = 1024 * 1024 * 1024 * 4


# --- МОДЕЛИ ДАННЫХ ---

class SysPetState(BaseModel):
    name: str = "sys.pet"

    # Статы (0-100)
    hp: float = 100.0
    hunger: float = 20.0
    fatigue: float = 0.0  # CPU
    happiness: float = 80.0

    # Физика
    weight: float = 50.0  # RAM (50 - норма, >80 - жирный)

    # Прогресс
    course: int = 1
    xp: int = 0

    # Визуал
    skin: str = "👶"
    status_message: str = "Жду код..."


class FeedRequest(BaseModel):
    code: str


# Глобальное состояние
pet = SysPetState()
start_time = time.time()

# --- ЛОГИКА "ЧЕТНОСТИ" (KILLER FEATURE) ---
PARITY_REGEXES = [
    (r"%\s*2\s*==\s*0", 10),  # Классика
    (r"&\s*1\s*==\s*0", 20),  # Битовый сдвиг
    (r"not\s*\(.*\s*&\s*1\)", 30),  # Pythonic bitwise
    (r"str\(.*\)\[-1\]\s*in\s*['\"]02468['\"]", 50),  # Строковое извращение
    (r"while\s*.*\s*>\s*0:.*-=2", 100)  # Цикличное безумие
]


def process_code_feeding(code_snippet: str) -> bool:
    """Анализирует код. Возвращает True, если код 'вкусный'."""
    total_xp_gain = 0
    found_magic = False

    # Ищем паттерны
    for pattern, xp_reward in PARITY_REGEXES:
        if re.search(pattern, code_snippet):
            total_xp_gain += xp_reward
            found_magic = True

    if found_magic:
        # Питомец счастлив
        pet.hunger = max(0, pet.hunger - 30)
        pet.happiness = min(100, pet.happiness + 20)
        pet.xp += total_xp_gain
        return True
    return False


# --- API МАРШРУТЫ ---

@app.get("/")
async def get_home():
    """Подает главную HTML страницу"""
    # Ищем файл templates/index.html относительно проекта
    template_path = Path(__file__).parent.parent / "frontend" / "templates" / "index.html"

    if template_path.exists():
        return FileResponse(template_path, media_type="text/html")
    else:
        return {"error": f"Template not found at {template_path}"}


@app.get("/api/pet")
async def get_pet_state():
    """Возвращает текущее состояние питомца"""
    return pet


@app.post("/api/feed")
async def feed_pet(request: FeedRequest):
    """Кормит питомца кодом"""
    if process_code_feeding(request.code):
        return {
            "success": True,
            "message": "Питомец рад! 😋",
            "pet": pet
        }
    else:
        pet.hunger = min(100, pet.hunger + 5)
        pet.happiness = max(0, pet.happiness - 10)
        return {
            "success": False,
            "message": "Питомец не понимает этот код... 😢",
            "pet": pet
        }


@app.get("/api/stats")
async def get_system_stats():
    """Возвращает системные статистики"""
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        ram_info = psutil.virtual_memory()

        return {
            "cpu_percent": cpu_percent,
            "ram_percent": ram_info.percent,
            "ram_used_mb": ram_info.used / (1024 * 1024),
            "ram_total_mb": ram_info.total / (1024 * 1024),
        }
    except Exception as e:
        return {"error": str(e)}


# --- СТАТИЧЕСКИЕ ФАЙЛЫ ---
# Подключаем статические файлы (CSS, JS) из frontend/static
static_path = Path(__file__).parent.parent / "frontend" / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)