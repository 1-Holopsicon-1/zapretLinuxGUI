from __future__ import annotations

import configparser
import os

from config import APPDATA_DIR
from log import log
from safe_construct import safe_construct

_LAUNCH_METHOD_FILE = os.path.join(APPDATA_DIR, "strategy_Launch_method.ini")
_LAUNCH_METHOD_SECTION = "Settings"
_LAUNCH_METHOD_KEY = "StrategyLaunchMethod"
_LAUNCH_METHOD_DEFAULT = "direct_zapret2"
_SUPPORTED_LAUNCH_METHODS = {
    "direct_zapret2",
    "direct_zapret1",
    "orchestra",
}


def get_strategy_launch_method() -> str:
    try:
        if os.path.isfile(_LAUNCH_METHOD_FILE):
            cfg = safe_construct(configparser.ConfigParser)
            cfg.read(_LAUNCH_METHOD_FILE, encoding="utf-8")
            value = cfg.get(_LAUNCH_METHOD_SECTION, _LAUNCH_METHOD_KEY, fallback="")
            if value:
                normalized = str(value or "").strip().lower()
                if normalized in _SUPPORTED_LAUNCH_METHODS:
                    return normalized
                log(
                    f"Обнаружен неподдерживаемый сохранённый метод запуска: {normalized}. "
                    f"Восстанавливаем значение по умолчанию: {_LAUNCH_METHOD_DEFAULT}",
                    "WARNING",
                )
    except Exception as e:
        log(f"Ошибка чтения метода запуска из {_LAUNCH_METHOD_FILE}: {e}", "ERROR")

    set_strategy_launch_method(_LAUNCH_METHOD_DEFAULT)
    log(f"Установлен метод запуска по умолчанию: {_LAUNCH_METHOD_DEFAULT}", "INFO")
    return _LAUNCH_METHOD_DEFAULT


def set_strategy_launch_method(method: str) -> bool:
    try:
        normalized = str(method or "").strip().lower()
        if normalized not in _SUPPORTED_LAUNCH_METHODS:
            log(
                f"Попытка сохранить неподдерживаемый метод запуска: {normalized or 'empty'}. "
                f"Используем {_LAUNCH_METHOD_DEFAULT}",
                "WARNING",
            )
            normalized = _LAUNCH_METHOD_DEFAULT

        os.makedirs(APPDATA_DIR, exist_ok=True)
        cfg = safe_construct(configparser.ConfigParser)
        cfg[_LAUNCH_METHOD_SECTION] = {_LAUNCH_METHOD_KEY: normalized}
        with open(_LAUNCH_METHOD_FILE, "w", encoding="utf-8") as f:
            cfg.write(f)
        log(f"Метод запуска стратегий изменен на: {normalized}", "INFO")
        return True
    except Exception as e:
        log(f"Ошибка сохранения метода запуска: {e}", "ERROR")
        return False
