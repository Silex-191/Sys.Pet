import uvicorn
import psutil
import time
import re
import random
import os
import shutil
import ctypes
import sys
from fastapi import FastAPI, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path

# --- CONFIG ---
app = FastAPI()

# !!! DANGER ZONE !!!
# False = Actually kill processes. True = Simulation only.
SAFE_MODE = False 
AVATAR_PATH = Path("static/avatar.png")

# Ensure directories exist
Path("static").mkdir(parents=True, exist_ok=True)
Path("templates").mkdir(parents=True, exist_ok=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- STATE MODELS ---
class SysPetState(BaseModel):
    sanity: float = 100.0
    happiness: float = 50.0
    hunger: float = 50.0
    xp: int = 0
    course: int = 1  # Changed from Level to Course
    last_action: str = "Idle"

class FeedRequest(BaseModel):
    code: str

class KillRequest(BaseModel):
    pid: int
    name: str

# Global State
pet = SysPetState()

# --- ADMIN CHECK ---
def is_admin():
    try:
        return os.getuid() == 0
    except AttributeError:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0

if not is_admin():
    print("\n" + "!"*50)
    print("WARNING: SCRIPT IS NOT RUNNING AS ADMINISTRATOR.")
    print("You will not be able to kill system processes.")
    print("Please run as Admin/Root for full functionality.")
    print("!"*50 + "\n")

# --- LOGIC ---

def course_up_check():
    required_xp = pet.course * 100
    if pet.xp >= required_xp:
        pet.course += 1
        pet.sanity = 100
        pet.happiness = 100
        pet.last_action = f"PASSED EXAM! Welcome to Course {pet.course}"

# --- API ROUTES ---

@app.get("/")
async def get_home():
    template_path = Path("templates/index.html")
    if template_path.exists():
        return FileResponse(template_path)
    return {"error": "index.html not found in /templates folder"}

@app.get("/api/state")
async def get_state():
    # Natural decay
    pet.hunger = min(100, pet.hunger + 0.2) 
    pet.happiness = max(0, pet.happiness - 0.1)
    return pet

@app.post("/api/upload_avatar")
async def upload_avatar(file: UploadFile = File(...)):
    try:
        with open(AVATAR_PATH, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return {"status": "success", "url": "/static/avatar.png"}
    except Exception as e:
        return {"error": str(e)}

# --- GAME 1: PROCESS SLOTS ---

@app.get("/api/processes")
async def get_processes():
    """Returns a list of running processes"""
    procs = []
    # Fetching all processes can be slow, limiting to ones we can actually see
    try:
        for proc in psutil.process_iter(['pid', 'name', 'username']):
            try:
                # Filter out empty names
                if proc.info['name']:
                    procs.append({
                        "pid": proc.info['pid'], 
                        "name": proc.info['name'],
                        "user": proc.info.get('username', 'System')
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
    except Exception:
        pass
    
    # Shuffle and return a subset to keep frontend fast
    random.shuffle(procs)
    return procs[:50]

@app.post("/api/kill_process")
async def kill_process(req: KillRequest):
    try:
        if SAFE_MODE:
            msg = f"Simulated Kill: {req.name} (PID: {req.pid})"
            success = True
        else:
            if psutil.pid_exists(req.pid):
                p = psutil.Process(req.pid)
                p.terminate() 
                # Wait a tiny bit to see if it died
                try:
                    p.wait(timeout=0.1)
                except:
                    pass
                msg = f"KILLED: {req.name} (PID: {req.pid})"
                success = True
            else:
                msg = f"Process {req.name} already dead."
                success = False

        # Rewards
        if success:
            pet.sanity = min(100, pet.sanity + 20)
            pet.happiness = min(100, pet.happiness + 15)
            pet.xp += 25
            pet.last_action = msg
            course_up_check()
        
        return {"success": success, "pet": pet}

    except psutil.AccessDenied:
        pet.last_action = f"FAILED: Access Denied for {req.name}"
        pet.sanity -= 5
        return {"success": False, "error": "Access Denied"}
    except Exception as e:
        pet.last_action = f"Error: {str(e)}"
        return {"success": False, "error": str(e)}

# --- GAME 2: CODE FEEDER ---

@app.post("/api/feed")
async def feed_pet(req: FeedRequest):
    # Regex for parity checks
    parity_patterns = [
        r"%\s*2\s*==\s*0",
        r"&\s*1\s*==\s*0",
        r"is_even",
        r"not\s*\(.*\s*&\s*1\)"
    ]
    
    is_tasty = any(re.search(p, req.code) for p in parity_patterns)

    if is_tasty:
        pet.hunger = max(0, pet.hunger - 30)
        pet.happiness = min(100, pet.happiness + 15)
        pet.xp += 50
        pet.last_action = "Yummy! Valid Parity Check."
    else:
        pet.hunger = max(0, pet.hunger - 5)
        pet.sanity = max(0, pet.sanity - 10)
        pet.last_action = "Gross! No parity logic found."
    
    course_up_check()
    return {"success": is_tasty, "pet": pet}

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    # Host 0.0.0.0 allows access from other devices on the network
    uvicorn.run(app, host="0.0.0.0", port=8000)
