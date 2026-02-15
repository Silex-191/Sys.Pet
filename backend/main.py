"""
SysPet FastAPI Backend
API для управления питомцем и игровой логикой
"""

import asyncio
import os
import signal
import subprocess
from pathlib import Path
from fastapi import FastAPI, HTTPException, Form, Body, UploadFile, File, Request
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
        "pet_alive": pet.sanity > 0,
    }


# ===== API ROUTES =====

@app.get("/api/state")
async def get_state():
    """Краткое состояние питомца для фронтенда"""
    state = pet.to_dict()
    return {
        "sanity": state["sanity"],
        "happiness": state["happiness"],
        "hunger": state["hunger"],
        "fatigue": state["fatigue"],
        "xp": state["xp"],
        "course": state["course"],
        "status": state["status"],
        "avatar_emotion": state["status"],  # Для динамической эмоции
        "last_action": pet.status_message,
    }


@app.get("/api/pet")
async def get_pet_state():
    """Получить текущее состояние питомца"""
    return pet.to_dict()


@app.post("/api/feed")
async def feed_pet(request: Request, code: str | None = Form(None)):
    """
    Покормить питомца кодом.
    Form param: code (строка с кодом)
    """
    if code is None:
        try:
            payload = await request.json()
            if isinstance(payload, dict):
                code = payload.get("code")
        except Exception:
            code = None

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
async def pet_action(action: str = Form(...)):
    """
    Действие над питомцем.
    Form param: action ('pet', 'rest', 'reset')
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
@app.post("/api/upload_avatar")
async def upload_avatar(file: UploadFile = File(...)):
    """Загрузка аватара; сохраняется в static/avatar.png"""
    static_dir = Path(__file__).parent.parent / "frontend" / "static"
    static_dir.mkdir(parents=True, exist_ok=True)
    avatar_path = static_dir / "avatar.png"

    with avatar_path.open("wb") as f:
        f.write(await file.read())

    return {"status": "success", "url": "/static/avatar.png"}


@app.get("/api/processes")
async def list_processes():
    """Список ВСЕХ процессов (запущено от sudo)"""
    import psutil

    processes = []
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            processes.append({"pid": proc.info["pid"], "name": proc.info.get("name") or "unknown"})
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return processes[:50]  # Увеличили лимит


@app.post("/api/kill_process")
async def kill_process(payload: dict = Body(...)):
    """Убить процесс по PID с помощью SIGKILL (запущено от sudo)"""
    import psutil
    import signal

    pid = payload.get("pid")
    if pid is None:
        raise HTTPException(status_code=400, detail="pid is required")

    try:
        pid_int = int(pid)
        if pid_int <= 0:
            return {"success": False, "message": "Invalid pid"}
        
        # Защита своего процесса
        if pid_int == os.getpid():
            return {"success": False, "message": "Cannot terminate server process"}
        
        # Используем SIGKILL для надёжного убийства
        os.kill(pid_int, signal.SIGKILL)
        
        # Успешное убийство - добавляем +2 sanity питомцу
        pet.process_killed()
        
        return {"success": True, "pid": pid, "message": "Process killed! +2 sanity"}
    except ProcessLookupError:
        return {"success": False, "message": "Process not found"}
    except PermissionError:
        return {"success": False, "message": "Permission denied"}
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}


@app.get("/api/debug/info")
async def debug_info():
    """Отладочная информация"""
    return {
        "app_name": "SysPet",
        "version": "1.0.0",
        "game_task_running": game_task is not None and not game_task.done(),
        "pet": pet.to_dict(),
    }


@app.post("/api/stress_test")
async def stress_test():
    """
    Запустить стресс-тест CPU.
    Использует stress-ng если доступен, иначе Python-based fallback.
    """
    import shutil
    
    # Проверяем наличие stress-ng
    if shutil.which("stress-ng"):
        try:
            # Запускаем stress-ng в фоне на 30 секунд
            import multiprocessing
            cpu_count = multiprocessing.cpu_count()
            subprocess.Popen(
                ["stress-ng", "--cpu", str(cpu_count), "--timeout", "30s"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return {
                "success": True,
                "message": f"Stress test started! Loading {cpu_count} CPU cores for 30s",
                "method": "stress-ng"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to start stress-ng: {str(e)}"
            }
    else:
        # Fallback: Python-based stress test
        try:
            # Запускаем Python процесс для нагрузки CPU
            python_stress = """
import time
import multiprocessing

def cpu_stress():
    end_time = time.time() + 30
    while time.time() < end_time:
        x = 0
        for i in range(1000000):
            x += i ** 2

if __name__ == '__main__':
    processes = []
    for _ in range(multiprocessing.cpu_count()):
        p = multiprocessing.Process(target=cpu_stress)
        p.start()
        processes.append(p)
    for p in processes:
        p.join()
"""
            subprocess.Popen(
                ["python3", "-c", python_stress],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return {
                "success": True,
                "message": "Stress test started! Python fallback mode for 30s",
                "method": "python-fallback"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to start stress test: {str(e)}"
            }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
