# main.py
import uvicorn
import psutil
import time
import re
import os
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# --- КОНФИГ ИГРЫ ---
XP_TO_NEXT_COURSE = 100  # Сколько опыта нужно для перехода на след. курс
MAX_WEIGHT_RAM = 1024 * 1024 * 1024 * 4  # 4 ГБ RAM это макс вес (условно)


# --- МОДЕЛЬ ПИТОМЦА ---
class SysPetState(BaseModel):
    name: str = "sys.pet"

    # Основные статы (0-100)
    hp: float = 100.0  # Здоровье (зависит от ошибок и свободного места)
    hunger: float = 0.0  # Голод (растет со временем, падает от коммитов)
    sanity: float = 100.0  # Рассудок (зависит от кол-ва процессов)
    fatigue: float = 0.0  # Усталость (зависит от CPU)
    happiness: float = 50.0  # Счастье (растет от "побед")

    # Физика
    weight: float = 50.0  # Вес (зависит от RAM)

    # Прогресс
    age_seconds: float = 0.0
    course: int = 1  # Курс вуза (1-6)
    xp: int = 0  # Опыт для перехода на курс

    # Статус
    status_message: str = "Жду код..."
    skin: str = "🥚"  # Скин (меняется от курса)


# Глобальное состояние
pet = SysPetState()
start_time = time.time()

# --- ЛОГИКА "ЧЕТНОСТИ" (KILLER FEATURE) ---
PARITY_REGEXES = [
    (r"%\s*2\s*==\s*0", 10),  # Обычный (скучно) - 10 XP
    (r"&\s*1\s*==\s*0", 20),  # Битовый (неплохо) - 20 XP
    (r"not\s*\(.*\s*&\s*1\)", 30),  # Pythonic bitwise - 30 XP
    (r"str\(.*\)\[-1\]\s*in\s*['\"]02468['\"]", 50),  # Строковый маньяк - 50 XP
    (r"while\s*.*\s*>\s*0:.*-=2", 100)  # Цикличное безумие - 100 XP + MAX HAPPINESS
]


def scan_code_for_food(code_snippet: str):
    """Питомец 'ест' код. Если там есть проверка четности — он кайфует."""
    total_xp_gain = 0
    found_magic = False

    for pattern, xp_reward in PARITY_REGEXES:
        if re.search(pattern, code_snippet):
            total_xp_gain += xp_reward
            found_magic = True

    if total_xp_gain > 0:
        pet.hunger = max(0, pet.hunger - 30)
        pet.happiness = min(100, pet.happiness + 20)
        pet.xp += total_xp_gain
        pet.status_message = f"ВКУСНО! Нашел проверку четности! (+{total_xp_gain} XP)"
        check_level_up()
        return True

    # Если просто код без магии
    pet.hunger = max(0, pet.hunger - 5)
    pet.status_message = "Код сухой... добавь проверки на четность!"
    return False


def check_level_up():
    """Переход на следующий курс"""
    if pet.xp >= XP_TO_NEXT_COURSE:
        pet.xp = 0
        pet.course += 1
        pet.happiness = 100
        pet.status_message = f"СЕССИЯ ЗАКРЫТА! Переход на {pet.course} курс! 🎉"

        # Эволюция скина
        skins = {1: "👶", 2: "🤓", 3: "🍺", 4: "🧟", 5: "🧙‍♂️", 6: "🐉"}
        pet.skin = skins.get(pet.course, "👽")


# --- ФОНОВЫЙ ЦИКЛ ОБНОВЛЕНИЯ (СЕРДЦЕБИЕНИЕ) ---
async def update_stats_loop():
    """Обновляет статы на основе реальных данных системы"""
    while True:
        # 1. Читаем систему
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory()
        process_count = len(psutil.pids())

        # 2. Обновляем УСТАЛОСТЬ (от CPU)
        if cpu > 50:
            pet.fatigue = min(100, pet.fatigue + 5)
        else:
            pet.fatigue = max(0, pet.fatigue - 2)

        # 3. Обновляем ВЕС (от RAM)
        # Если занято > 80% RAM — он жирный (100 кг)
        pet.weight = (ram.percent / 100) * 100

        # 4. Обновляем РАССУДОК (от кол-ва процессов)
        # Если процессов > 300, крыша едет
        if process_count > 300:
            pet.sanity = max(0, pet.sanity - 1)
        else:
            pet.sanity = min(100, pet.sanity + 1)

        # 5. Обновляем ГОЛОД (просто растет со временем)
        pet.hunger = min(100, pet.hunger + 1)
        if pet.hunger > 80:
            pet.hp = max(0, pet.hp - 1)  # Умирает с голоду

        # 6. Обновляем ВОЗРАСТ (uptime скрипта)
        pet.age_seconds = int(time.time() - start_time)

        # Пассивная смерть счастья
        pet.happiness = max(0, pet.happiness - 0.5)

        await asyncio.sleep(2)  # Тик раз в 2 секунды


import asyncio


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(update_stats_loop())


# --- API ENDPOINTS ---

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/pet")
async def get_pet_state():
    return pet


@app.post("/api/feed")
async def feed_pet_code(request: Request):
    """Сюда фронт (или IDE плагин) шлет код"""
    body = await request.json()
    code = body.get("code", "")
    is_tasty = scan_code_for_food(code)
    return {"status": "fed", "is_tasty": is_tasty, "pet": pet}


@app.post("/api/action/{action_type}")
async def do_action(action_type: str):
    """Кнопки действий с фронта"""
    if action_type == "sleep":
        pet.fatigue = 0
        pet.status_message = "Поспал — можно и покодить."
    elif action_type == "clean_ram":
        # Эмуляция очистки
        pet.happiness += 10
        pet.status_message = "Мусор убран! Легкость в байтах."

    return pet


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)