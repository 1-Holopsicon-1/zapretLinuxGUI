from __future__ import annotations

import json
import os
from pathlib import Path

from config import get_zapret_userdata_dir
from log import log

_DIRECT_ZAPRET2_UI_MODE_DEFAULT = "basic"


def _ui_prefs_path() -> Path:
    base = ""
    try:
        base = (get_zapret_userdata_dir() or "").strip()
    except Exception:
        base = ""

    if not base:
        appdata = (os.environ.get("APPDATA") or "").strip()
        if appdata:
            base = os.path.join(appdata, "zapret")

    if not base:
        raise RuntimeError("APPDATA is required for strategy_menu UI preferences")

    return Path(base) / "strategy_menu" / "ui_prefs.json"


def _load_state() -> dict:
    path = _ui_prefs_path()
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception as e:
        log(f"Ошибка чтения strategy_menu UI prefs из {path}: {e}", "DEBUG")
        return {}


def _save_state(state: dict) -> bool:
    path = _ui_prefs_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return True
    except Exception as e:
        log(f"Ошибка сохранения strategy_menu UI prefs в {path}: {e}", "ERROR")
        return False


def get_direct_zapret2_ui_mode() -> str:
    state = _load_state()
    value = str(state.get("direct_zapret2_ui_mode") or "").strip().lower()
    if value in ("basic", "advanced"):
        return value
    try:
        set_direct_zapret2_ui_mode(_DIRECT_ZAPRET2_UI_MODE_DEFAULT)
    except Exception:
        pass
    return _DIRECT_ZAPRET2_UI_MODE_DEFAULT


def set_direct_zapret2_ui_mode(mode: str) -> bool:
    value = str(mode or "").strip().lower()
    if value not in ("basic", "advanced"):
        value = _DIRECT_ZAPRET2_UI_MODE_DEFAULT
    state = _load_state()
    state["direct_zapret2_ui_mode"] = value
    ok = _save_state(state)
    if ok:
        log(f"DirectZapret2 UI mode set to: {value}", "DEBUG")
    return ok


def get_tabs_pinned() -> bool:
    state = _load_state()
    return bool(state.get("tabs_pinned", True))


def set_tabs_pinned(pinned: bool) -> bool:
    state = _load_state()
    state["tabs_pinned"] = bool(pinned)
    ok = _save_state(state)
    if ok:
        log(f"Настройка закрепления табов: {'закреплено' if pinned else 'не закреплено'}", "DEBUG")
    return ok


def get_keep_dialog_open() -> bool:
    state = _load_state()
    return bool(state.get("keep_dialog_open", False))


def set_keep_dialog_open(enabled: bool) -> bool:
    state = _load_state()
    state["keep_dialog_open"] = bool(enabled)
    ok = _save_state(state)
    if ok:
        log(f"Настройка 'не закрывать окно': {'вкл' if enabled else 'выкл'}", "DEBUG")
    return ok
