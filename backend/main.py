"""
SysPet FastAPI Backend
API для управления питомцем и игровой логикой
"""

import asyncio
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager

from .logic import pet, SysPet

# ===== АСИНХРОННЫЙ GAME LOOP =====
game_task = None


async def game_loop():
    """Фоновый цикл обновления состояния питомца"""
    while True:
        pet.update_from_system()
        await asyncio.sleep(1)  # Обновлять каждую секунду


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Управление жизненным циклом приложения.
    Запускает game loop при старте, останавливает при закрытии.
    """
    global game_task

    # Startup: запустить game loop
    game_task = asyncio.create_task(game_loop())
    print("🎮 Game loop запущен!")

    yield

    # Shutdown: остановить game loop
    if game_task:
        game_task.cancel()
        try:
            await game_task
        except asyncio.CancelledError:
            pass
    print("⛔ Game loop остановлен!")


# ===== ИНИЦИАЛИЗАЦИЯ FASTAPI =====
app = FastAPI(
    title="SysPet API",
    description="Тамагочи, завязанный на системных показателях",
    version="1.0.0",
    lifespan=lifespan,
)

# ===== MIDDLEWARE =====
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===== СТАТИЧЕСКИЕ ФАЙЛЫ И ШАБЛОНЫ =====
def setup_static_files():
    """Подключить статические файлы и шаблоны"""
    # Пути относительно корня проекта
    base_path = Path(__file__).parent.parent  # Выходим из backend/ в корень

    # Frontend
    frontend_path = base_path / "frontend"
    static_path = frontend_path / "static"

    # Подключить статику
    if static_path.exists():
        app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
        print(f"✅ Static files mounted: {static_path}")
    else:
        print(f"⚠️  Static folder not found: {static_path}")


setup_static_files()


# ===== HTTP ROUTES =====

@app.get("/")
async def get_home():
    """Главная страница (index.html)"""
    template_path = Path(__file__).parent.parent / "frontend" / "templates" / "index.html"

    if template_path.exists():
        return FileResponse(template_path, media_type="text/html")
    else:
        raise HTTPException(
            status_code=404,
            detail=f"Template not found: {template_path}"
        )


@app.get("/health")
async def health_check():
    """Проверка здоровья сервера"""
    return {
        "status": "ok",
        "pet_alive": pet.hp > 0,
    }


# ===== API ROUTES =====

@app.get("/api/pet")
async def get_pet_state():
    """Получить текущее состояние питомца"""
    return pet.to_dict()


@app.post("/api/feed")
async def feed_pet(code: str):
    """
    Покормить питомца кодом.
    Query param: code (строка с кодом)
    """
    if not code or len(code) == 0:
        raise HTTPException(status_code=400, detail="Code cannot be empty")

    result = pet.feed(code)
    return result


@app.post("/api/rest")
async def pet_rest():
    """Питомец отдыхает"""
    pet.rest()
    return {
        "message": "Питомец отдыхает...",
        "pet": pet.to_dict()
    }


@app.post("/api/pet-action")
async def pet_action(action: str):
    """
    Действие над питомцем.
    Query param: action ('pet', 'rest', 'reset')
    """
    if action == "pet":
        pet.pet()
        return {"message": "Вы пожалели питомца", "pet": pet.to_dict()}

    elif action == "rest":
        pet.rest()
        return {"message": "Питомец отдыхает", "pet": pet.to_dict()}

    elif action == "reset":
        pet.debug_reset()
        return {"message": "Питомец перезагружен!", "pet": pet.to_dict()}

    else:
        raise HTTPException(status_code=400, detail=f"Unknown action: {action}")


@app.get("/api/stats")
async def get_system_stats():
    """Получить системные статистики"""
    try:
        import psutil
        cpu = psutil.cpu_percent(interval=0.1)
        ram = psutil.virtual_memory()

        return {
            "cpu_percent": cpu,
            "ram_percent": ram.percent,
            "ram_used_mb": round(ram.used / (1024 ** 2), 2),
            "ram_total_mb": round(ram.total / (1024 ** 2), 2),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== ОТЛАДКА =====
@app.get("/api/debug/info")
async def debug_info():
    """Отладочная информация"""
    return {
        "app_name": "SysPet",
        "version": "1.0.0",
        "game_task_running": game_task is not None and not game_task.done(),
        "pet": pet.to_dict(),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )