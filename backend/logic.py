"""
SysPet Game Logic Module
Содержит всю игровую логику, отделенную от FastAPI
"""

import re
import psutil
import time
from dataclasses import dataclass, field, asdict
from typing import Tuple, List, Dict, Any
from enum import Enum

# ===== КОНСТАНТЫ ИГРЫ =====
XP_TO_NEXT_COURSE = 100
MAX_WEIGHT_RAM = 1024 * 1024 * 1024 * 4
UPDATE_INTERVAL = 1.0  # Обновление каждую секунду

# ===== ПАТТЕРНЫ КОДА =====
PARITY_REGEXES: List[Tuple[str, int]] = [
    (r"%\s*2\s*==\s*0", 10),  # Классика: num % 2 == 0
    (r"&\s*1\s*==\s*0", 20),  # Битовый сдвиг: num & 1 == 0
    (r"not\s*\(.*\s*&\s*1\)", 30),  # Pythonic: not (num & 1)
    (r"str\(.*\)\[-1\]\s*in\s*['\"]02468['\"]", 50),  # Строковое: str(num)[-1] in '02468'
    (r"while\s*.*\s*>\s*0:.*-=2", 100),  # Цикличное: while n > 0: n -= 2
]


class PetStatus(Enum):
    """Статусы питомца"""
    HAPPY = "happy"  # Счастлив
    HUNGRY = "hungry"  # Голоден
    TIRED = "tired"  # Устал
    DEAD = "dead"  # Мертв
    EVOLVING = "evolving"  # Эволюционирует


class SysPet:
    """Класс питомца с полной игровой логикой"""

    def __init__(self, name: str = "sys.pet"):
        self.name = name

        # === СТАТЫ (0-100) ===
        self.hp = 100.0
        self.hunger = 20.0  # 0 = голодный, 100 = сытый
        self.fatigue = 0.0  # 0 = бодрый, 100 = очень устал
        self.happiness = 80.0  # 0 = грустный, 100 = счастлив

        # === ФИЗИЧЕСКИЕ ХАРАКТЕРИСТИКИ ===
        self.weight = 50.0  # RAM-зависимо (50 - норма, >80 - жирный)

        # === ПРОГРЕСС ===
        self.course = 1  # Уровень
        self.xp = 0  # Опыт текущего уровня

        # === ВИЗУАЛ ===
        self.skin = "👶"  # Эмодзи питомца (меняется с уровнем)
        self.status_message = "Жду код..."

        # === ВНУТРЕННЕЕ СОСТОЯНИЕ ===
        self._total_xp = 0  # Всего XP за игру
        self._code_fed_count = 0  # Сколько кода съедено
        self._last_update = time.time()

    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь для JSON"""
        return {
            "name": self.name,
            "hp": round(self.hp, 1),
            "hunger": round(self.hunger, 1),
            "fatigue": round(self.fatigue, 1),
            "happiness": round(self.happiness, 1),
            "weight": round(self.weight, 1),
            "course": self.course,
            "xp": self.xp,
            "xp_to_next": XP_TO_NEXT_COURSE,
            "skin": self.skin,
            "status_message": self.status_message,
            "status": self.get_status(),
            "total_xp": self._total_xp,
            "code_fed": self._code_fed_count,
        }

    def get_status(self) -> str:
        """Определить статус питомца"""
        if self.hp <= 0:
            return PetStatus.DEAD.value
        elif self.xp >= XP_TO_NEXT_COURSE:
            return PetStatus.EVOLVING.value
        elif self.hunger < 20:
            return PetStatus.HUNGRY.value
        elif self.fatigue > 80:
            return PetStatus.TIRED.value
        else:
            return PetStatus.HAPPY.value

    def analyze_code(self, code: str) -> Tuple[bool, int]:
        """
        Анализирует код через regex паттерны.
        Возвращает (найден_ли_паттерн, xp_награда)
        """
        total_xp = 0
        found_pattern = False

        for pattern, xp_reward in PARITY_REGEXES:
            if re.search(pattern, code):
                total_xp += xp_reward
                found_pattern = True

        return found_pattern, total_xp

    def feed(self, code: str) -> Dict[str, Any]:
        """
        Кормит питомца кодом.
        Возвращает информацию о результате.
        """
        found, xp_gained = self.analyze_code(code)

        if found:
            # Код вкусный!
            self.hunger = max(0, self.hunger - 30)
            self.happiness = min(100, self.happiness + 15)
            self.xp += xp_gained
            self._total_xp += xp_gained
            self._code_fed_count += 1
            self.status_message = "Мм, вкусненько! 😋"

            # Проверка на эволюцию
            if self.xp >= XP_TO_NEXT_COURSE:
                self.evolve()

            return {
                "success": True,
                "message": f"Питомец съел код! +{xp_gained} XP",
                "xp_gained": xp_gained,
                "pet": self.to_dict()
            }
        else:
            # Код не вкусный
            self.hunger = min(100, self.hunger + 5)
            self.happiness = max(0, self.happiness - 10)
            self.status_message = "Фу, это не то... 😢"

            return {
                "success": False,
                "message": "Питомец не понял этот код...",
                "xp_gained": 0,
                "pet": self.to_dict()
            }

    def evolve(self):
        """Эволюция питомца при достижении XP"""
        self.course += 1
        self.xp = 0

        # Улучшение статов
        self.hp = min(100, self.hp + 10)
        self.happiness = min(100, self.happiness + 20)

        # Смена скина
        skins = {
            1: "👶",
            2: "🧒",
            3: "👦",
            4: "👨",
            5: "💻",
            6: "🤖",
        }
        self.skin = skins.get(self.course, "🌟")
        self.status_message = f"Эволюция! Теперь уровень {self.course}! ✨"

    def update_from_system(self):
        """
        Обновить состояние питомца на основе системных метрик.
        Вызывается периодически (каждую секунду).
        """
        now = time.time()
        delta = now - self._last_update

        if delta < UPDATE_INTERVAL:
            return

        # Получить системные метрики
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            ram_info = psutil.virtual_memory()

            # === Влияние CPU на усталость ===
            # Высокая CPU → питомец устает
            fatigue_increase = (cpu_percent / 100.0) * 5
            self.fatigue = min(100, self.fatigue + fatigue_increase)

            # === Влияние RAM ��а вес ===
            # Больше RAM → питомец толстеет
            self.weight = (ram_info.percent / 100.0) * 100

            # === Общее здоровье ===
            # Усталость ↔ голод и счастье
            if self.fatigue > 80:
                self.happiness = max(0, self.happiness - 1)
                self.hunger = min(100, self.hunger + 1)

            # Голод → HP
            if self.hunger < 10:
                self.hp = max(0, self.hp - 2)

            # Счастье → HP (если счастлив, здоровее)
            if self.happiness > 70:
                self.hp = min(100, self.hp + 0.5)

        except Exception as e:
            self.status_message = f"Ошибка системы: {str(e)[:20]}"

        self._last_update = now

    def rest(self):
        """Питомец отдыхает"""
        self.fatigue = max(0, self.fatigue - 30)
        self.hunger = min(100, self.hunger + 10)
        self.status_message = "Zzz... отдыхаю 😴"

    def pet(self):
        """Пожалеть питомца"""
        self.happiness = min(100, self.happiness + 5)
        self.status_message = "Мур-мур! 💕"

    def debug_reset(self):
        """Сброс питомца (для тестирования)"""
        self.__init__(self.name)


# ===== ГЛОБАЛЬНЫЙ ЭКЗЕМПЛЯР =====
pet = SysPet()