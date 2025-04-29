# backend/app/core/ai_base.py
from abc import ABC, abstractmethod
from typing import Any, Dict

class AIBase(ABC):
    @abstractmethod
    def select_move(self, state: Dict[str, Any]) -> int:
        """
        Dado el estado del juego (e.g. tablero, turno, config),
        devuelve la posición (0–8) donde jugar.
        """
        pass

# registro global
_strategies: dict[str, AIBase] = {}

def register_ai(name: str, impl: AIBase):
    _strategies[name] = impl

def get_ai(name: str) -> AIBase:
    return _strategies[name]