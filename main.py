import uvicorn
import psutil
import time
import re
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

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
    fatigue: float = 0.0     # CPU
    happiness: float = 80.0
    
    # Физика
    weight: float = 50.0     # RAM (50 - норма, >80 - жирный)
    
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
    (r"%\s*2\s*==\s*0", 10),           # Классика
    (r"&\s*1\s*==\s*0", 20),           # Битовый сдвиг
    (r"not\s*\(.*\s*&\s*1\)", 30),     # Pythonic bitwise
    (r"str\(.*\)\[-1\]\s*in\s*['\"]02468['\"]", 50), # Строковое извращение
    (r"while\s*.*\s*>\s*0:.*-=2", 100) # Цикличное безумие
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
        pet.status_message = f"ВКУСНО! (+{total_xp_gain} XP)"
        check_level_up()
        return True
    else:
        # Питомец недоволен
        pet.hunger = max(0, pet.hunger - 5) # Чуть-чуть наелся
        pet.happiness = max(0, pet.happiness - 5)
        pet.status_message = "Код сухой... где проверки на четность?"
        return False

def check_level_up():
    """Проверка перехода на следующий курс"""
    if pet.xp >= XP_TO_NEXT_COURSE:
        pet.xp = 0
        pet.course += 1
        pet.happiness = 100
        pet.status_message = f"СЕССИЯ ЗАКРЫТА! Переход на {pet.course} курс! 🎉"
        update_skin()

def update_skin():
    """Меняет скин в зависимости от курса"""
    skins = {
        1: "👶", # 1 курс - младенец
        2: "🤓", # 2 курс - ботан
        3: "🍺", # 3 курс - пиво
        4: "🧟", # 4 курс - зомби
        5: "🧙‍♂️", # 5 курс - маг
        6: "🐉"  # 6 курс - дракон (сеньор)
    }
    # Берем скин по курсу, если курс > 6, то дракон
    pet.skin = skins.get(pet.course, "🐉")

# --- ФОНОВЫЙ ЦИКЛ (СЕРДЦЕБИЕНИЕ СИСТЕМЫ) ---
async def update_stats_loop():
    while True:
        try:
            # 1. Читаем реальные системные ресурсы
            cpu_percent = psutil.cpu_percent(interval=None)
            ram_percent = psutil.virtual_memory().percent
            
            # 2. Обновляем УСТАЛОСТЬ (CPU)
            # Питомец устает, если CPU > 30%
            if cpu_percent > 30:
                pet.fatigue = min(100, pet.fatigue + 5)
            else:
                pet.fatigue = max(0, pet.fatigue - 2)

            # 3. Обновляем ВЕС (RAM)
            # Прямая зависимость: 50% RAM = 50 ед. веса. 
            # На фронте > 50 он начнет толстеть.
            pet.weight = ram_percent

            # 4. Обновляем ГОЛОД (растет со временем)
            pet.hunger = min(100, pet.hunger + 0.5)
            
            # Если голод 100, падает HP
            if pet.hunger >= 100:
                pet.hp = max(0, pet.hp - 1)
                pet.status_message = "Я УМИРАЮ ОТ ГОЛОДА!"

            # 5. Счастье падает медленно
            pet.happiness = max(0, pet.happiness - 0.2)

            # Обновляем скин на всякий случай (вдруг курс сменился читом)
            update_skin()
            
        except Exception as e:
            print(f"Error in stats loop: {e}")

        await asyncio.sleep(1) # Обновление раз в секунду

@app.on_event("startup")
async def startup_event():
    # Запуск фоновой задачи при старте сервера
    asyncio.create_task(update_stats_loop())

# --- API ENDPOINTS ---

@app.get("/api/pet", response_model=SysPetState)
async def get_pet_state():
    return pet

@app.post("/api/feed")
async def feed_pet(feed_req: FeedRequest):
    """
    Принимает JSON: {"code": "..."}
    Возвращает: {"is_tasty": true/false}
    """
    is_tasty = process_code_feeding(feed_req.code)
    return {
        "is_tasty": is_tasty, 
        "current_state": pet
    }

if __name__ == "__main__":
    # Запуск: python main.py
    print("🚀 SYS.PET Backend started on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
