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
from .analyzer import analyzer

# ===== КОНСТАНТЫ ИГРЫ =====
XP_TO_NEXT_COURSE = 100
MAX_WEIGHT_RAM = 1024 * 1024 * 1024 * 4
UPDATE_INTERVAL = 1.0  # Обновление каждую секунду
HUNGER_DECAY_INTERVAL = 10.0  # Голод уменьшается каждые 10 секунд
HAPPINESS_DECAY_INTERVAL = 15.0  # Счастье уменьшается каждые 15 секунд
FATIGUE_XP_INTERVAL = 5.0  # XP от усталости каждые 5 секунд


class PetStatus(Enum):
    """Статусы питомца"""
    HAPPY = "happy"
    HUNGRY = "hungry"
    TIRED = "tired"
    DEAD = "dead"
    EVOLVING = "evolving"


class SysPet:
    """Класс питомца с полной игровой логикой"""

    def __init__(self, name: str = "sys.pet"):
        self.name = name

        # === СТАТЫ (0-100) ===
        self.sanity = 100.0  # Renamed from hp - рассудок
        self.hunger = 100.0  # 100 = сытый, 0 = голодный (reversed!)
        self.fatigue = 0.0  # 0 = бодрый, 100 = очень устал
        self.happiness = 80.0  # 0 = грустный, 100 = счастлив

        # === ФИЗИЧЕСКИЕ ХАРАКТЕРИСТИКИ ===
        self.weight = 50.0  # RAM-зависимо

        # === ПРОГРЕСС ===
        self.course = 1
        self.xp = 0

        # === ВИЗУАЛ ===
        self.skin = "👶"
        self.status_message = "Жду код..."

        # === ВНУТРЕННЕЕ СОСТОЯНИЕ ===
        self._total_xp = 0
        self._code_fed_count = 0
        self._last_update = time.time()
        self._last_hunger_decay = time.time()
        self._last_happiness_decay = time.time()
        self._last_fatigue_xp = time.time()

    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь для JSON"""
        return {
            "name": self.name,
            "sanity": round(self.sanity, 1),
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
        if self.sanity <= 0:
            return PetStatus.DEAD.value
        elif self.xp >= XP_TO_NEXT_COURSE:
            return PetStatus.EVOLVING.value
        elif self.hunger < 20:
            return PetStatus.HUNGRY.value
        elif self.fatigue > 80:
            return PetStatus.TIRED.value
        else:
            return PetStatus.HAPPY.value

    def analyze_code(self, code: str) -> Tuple[bool, int, Dict[str, Any]]:
        """
        Анализирует код через enhanced analyzer.
        Возвращает (найден_ли_паттерн, количество_паттернов, метаданные)
        """
        found, pattern_count, metadata = analyzer.analyze(code)
        return found, pattern_count, metadata

    def feed(self, code: str) -> Dict[str, Any]:
        """
        Кормит питомца кодом.
        Каждая уникальная конструкция чётности = +20 hunger
        Код без конструкций = -10 sanity
        """
        found, pattern_count, metadata = self.analyze_code(code)

        if found:
            # Код содержит проверки чётности!
            hunger_restore = pattern_count * 20  # Каждый паттерн = +20 hunger
            self.hunger = min(100, self.hunger + hunger_restore)
            self.happiness = min(100, self.happiness + 15)
            # XP не даётся при кормлении, только hunger восстанавливается
            self._code_fed_count += 1
            self.status_message = f"Мм, вкусненько! +{hunger_restore} hunger 😋"

            return {
                "success": True,
                "message": f"Питомец съел код! +{hunger_restore} hunger ({pattern_count} паттернов)",
                "hunger_restored": hunger_restore,
                "patterns_found": pattern_count,
                "analysis": metadata,
                "pet": self.to_dict()
            }
        else:
            # Код БЕЗ проверок чётности - это плохо!
            self.sanity = max(0, self.sanity - 10)
            self.happiness = max(0, self.happiness - 10)
            self.status_message = "Фу, это не то... -10 sanity 😢"

            return {
                "success": False,
                "message": "Питомец не понял этот код... -10 sanity",
                "hunger_restored": 0,
                "patterns_found": 0,
                "analysis": metadata,
                "pet": self.to_dict()
            }

    def evolve(self):
        """Эволюция питомца при достижении XP"""
        self.course += 1
        self.xp = 0

        # Улучшение статов
        self.sanity = min(100, self.sanity + 10)
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
            fatigue_increase = (cpu_percent / 100.0) * 5
            self.fatigue = min(100, self.fatigue + fatigue_increase)

            # === Влияние RAM на вес ===
            self.weight = (ram_info.percent / 100.0) * 100

            # === Общее здоровье ===
            if self.fatigue > 80:
                self.happiness = max(0, self.happiness - 1)
                self.hunger = max(0, self.hunger - 1)

            # Голод → sanity
            if self.hunger < 10:
                self.sanity = max(0, self.sanity - 2)

            # Счастье → sanity
            if self.happiness > 70:
                self.sanity = min(100, self.sanity + 0.5)

        except Exception as e:
            self.status_message = f"Ошибка системы: {str(e)[:20]}"

        # === АВТОМАТИЧЕСКОЕ УМЕНЬШЕНИЕ ГОЛОДА ===
        # Голод уменьшается на 1 каждые 10 секунд
        if now - self._last_hunger_decay >= HUNGER_DECAY_INTERVAL:
            self.hunger = max(0, self.hunger - 1)
            self._last_hunger_decay = now

        # === АВТОМАТИЧЕСКОЕ УМЕНЬШЕНИЕ СЧАСТЬЯ ===
        # Счастье уменьшается на 1 каждые 15 секунд
        if now - self._last_happiness_decay >= HAPPINESS_DECAY_INTERVAL:
            self.happiness = max(0, self.happiness - 1)
            self._last_happiness_decay = now

        # === XP ОТ УСТАЛОСТИ ===
        # Когда fatigue >= 100, даём +1 XP каждые 5 секунд
        if self.fatigue >= 100:
            if now - self._last_fatigue_xp >= FATIGUE_XP_INTERVAL:
                self.xp += 1
                self._total_xp += 1
                self._last_fatigue_xp = now
                if self.xp >= XP_TO_NEXT_COURSE:
                    self.evolve()

        self._last_update = now

    def rest(self):
        """Питомец отдыхает"""
        self.fatigue = max(0, self.fatigue - 30)
        self.hunger = max(0, self.hunger - 10)
        self.status_message = "Zzz... отдыхаю 😴"

    def pet(self):
        """Пожалеть питомца"""
        self.happiness = min(100, self.happiness + 5)
        self.status_message = "Мур-мур! 💕"

    def process_killed(self):
        """Вызывается при успешном убийстве процесса - восстанавливает sanity"""
        self.sanity = min(100, self.sanity + 2)
        self.status_message = "Процесс убит! +2 sanity 🔪"

    def debug_reset(self):
        """Сброс питомца (для тестирования)"""
        self.__init__(self.name)


# ===== ГЛОБАЛЬНЫЙ ЭКЗЕМПЛЯР =====
pet = SysPet()
