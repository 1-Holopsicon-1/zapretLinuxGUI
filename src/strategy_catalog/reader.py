from __future__ import annotations

import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Optional

from config import INDEXJSON_FOLDER
from log import log


STRATEGIES_DIR = Path(INDEXJSON_FOLDER) / "strategies"
_LOCAL_STRATEGIES_DIR = Path(__file__).resolve().parent
_DEV_ZAPRET_DIR = Path(__file__).resolve().parent.parent.parent / "zapret" / "json" / "strategies"

_EXTERNAL_STRATEGY_BASENAME_MAP: Dict[str, Dict[str, str]] = {
    "basic": {
        "tcp": "tcp_zapret2_basic",
        "udp": "udp_zapret_basic",
        "http80": "http80_zapret2_basic",
        "discord_voice": "discord_voice_zapret2_basic",
    },
    "advanced": {
        "tcp": "tcp_zapret2_advanced",
        "tcp_fake": "tcp_fake_zapret2_advanced",
        "udp": "udp_zapret2_advanced",
        "http80": "http80_zapret2_advanced",
        "discord_voice": "discord_voice_zapret2_advanced",
    },
}

_CACHE_MAX_ENTRIES = 128
_JSON_FILE_CACHE: Dict[str, tuple[int, int, Any]] = {}
_TEXT_FILE_CACHE: Dict[str, tuple[int, int, Any]] = {}

_LABEL_MAP = {
    "recommended": "recommended",
    "game": "game",
    "caution": "caution",
    "experimental": "experimental",
    "stable": "stable",
    None: None,
    "null": None,
}


def _to_cache_key(filepath: Path) -> str:
    try:
        return str(filepath.resolve())
    except Exception:
        return str(filepath)


def _file_signature(filepath: Path) -> tuple[int, int]:
    stat = filepath.stat()
    mtime_ns = int(getattr(stat, "st_mtime_ns", int(stat.st_mtime * 1_000_000_000)))
    return mtime_ns, int(stat.st_size)


def _get_cached_data(cache: Dict[str, tuple[int, int, Any]], filepath: Path) -> Optional[Any]:
    key = _to_cache_key(filepath)
    cached = cache.get(key)
    if not cached:
        return None

    try:
        current_signature = _file_signature(filepath)
    except Exception:
        return None

    if (cached[0], cached[1]) != current_signature:
        return None

    return deepcopy(cached[2])


def _set_cached_data(
    cache: Dict[str, tuple[int, int, Any]],
    filepath: Path,
    signature: tuple[int, int],
    data: Any,
) -> None:
    key = _to_cache_key(filepath)
    cache[key] = (signature[0], signature[1], deepcopy(data))
    if len(cache) > _CACHE_MAX_ENTRIES:
        cache.pop(next(iter(cache)), None)


def _has_any_strategy_files(directory: Path) -> bool:
    try:
        return any(directory.glob("*.txt")) or any(directory.glob("*.json"))
    except Exception:
        return False


def _get_builtin_dir() -> Path:
    global_builtin = STRATEGIES_DIR / "builtin"
    local_builtin = _LOCAL_STRATEGIES_DIR / "builtin"
    dev_builtin = _DEV_ZAPRET_DIR / "builtin"

    if global_builtin.exists() and _has_any_strategy_files(global_builtin):
        return global_builtin
    if dev_builtin.exists() and _has_any_strategy_files(dev_builtin):
        return dev_builtin
    if local_builtin.exists() and _has_any_strategy_files(local_builtin):
        return local_builtin
    return global_builtin


def _get_user_dir() -> Path:
    global_user = STRATEGIES_DIR / "user"
    local_user = _LOCAL_STRATEGIES_DIR / "user"
    dev_user = _DEV_ZAPRET_DIR / "user"

    builtin_dir = _get_builtin_dir()
    if builtin_dir == _DEV_ZAPRET_DIR / "builtin":
        return dev_user
    if builtin_dir == _LOCAL_STRATEGIES_DIR / "builtin":
        return local_user
    return global_user


def _load_json_file(filepath: Path) -> Optional[Dict[str, Any]]:
    try:
        if not filepath.exists():
            return None

        cached = _get_cached_data(_JSON_FILE_CACHE, filepath)
        if cached is not None:
            return cached

        signature = _file_signature(filepath)
        with open(filepath, "r", encoding="utf-8") as file:
            data = json.load(file)

        _set_cached_data(_JSON_FILE_CACHE, filepath, signature, data)
        return deepcopy(data)
    except json.JSONDecodeError as exc:
        log(f"Ошибка парсинга JSON {filepath}: {exc}", "ERROR")
        return None
    except Exception as exc:
        log(f"Ошибка чтения {filepath}: {exc}", "ERROR")
        return None


def _load_text_file(filepath: Path) -> Optional[Dict[str, Any]]:
    try:
        if not filepath.exists():
            return None

        cached = _get_cached_data(_TEXT_FILE_CACHE, filepath)
        if cached is not None:
            return cached

        signature = _file_signature(filepath)
        with open(filepath, "r", encoding="utf-8") as file:
            content = file.read()

        strategies = []
        current_strategy: Optional[Dict[str, Any]] = None
        current_args: list[str] = []

        for raw_line in content.splitlines():
            line = raw_line.rstrip()

            if not line or line.startswith("#"):
                continue

            if line.startswith("[") and line.endswith("]"):
                if current_strategy is not None:
                    current_strategy["args"] = "\n".join(current_args)
                    strategies.append(current_strategy)

                strategy_id = line[1:-1].strip()
                current_strategy = {
                    "id": strategy_id,
                    "name": strategy_id,
                    "description": "",
                    "author": "unknown",
                    "label": None,
                    "blobs": [],
                    "args": "",
                }
                current_args = []
                continue

            if current_strategy is None:
                continue

            if line.startswith("--"):
                current_args.append(line)
                continue

            if "=" not in line:
                continue

            key, _, value = line.partition("=")
            key = key.strip().lower()
            value = value.strip()

            if key == "name":
                current_strategy["name"] = value
            elif key == "author":
                current_strategy["author"] = value
            elif key == "label":
                current_strategy["label"] = value if value else None
            elif key == "description":
                current_strategy["description"] = value
            elif key == "blobs":
                current_strategy["blobs"] = [blob.strip() for blob in value.split(",") if blob.strip()]

        if current_strategy is not None:
            current_strategy["args"] = "\n".join(current_args)
            strategies.append(current_strategy)

        result = {"strategies": strategies}
        _set_cached_data(_TEXT_FILE_CACHE, filepath, signature, result)
        log(f"Загружено {len(strategies)} стратегий из TXT: {filepath.name}", "DEBUG")
        return deepcopy(result)
    except Exception as exc:
        log(f"Ошибка чтения TXT {filepath}: {exc}", "ERROR")
        return None


def _validate_strategy(strategy: Dict[str, Any], strategy_id: Optional[str] = None) -> tuple[bool, str]:
    if strategy_id:
        strategy["id"] = strategy_id

    if "id" not in strategy or not strategy["id"]:
        return False, "Отсутствует id стратегии"
    if "name" not in strategy or not strategy["name"]:
        return False, "Отсутствует name стратегии"
    if "args" not in strategy:
        return False, "Отсутствует args стратегии"

    current_id = strategy["id"]
    if not all(char.isalnum() or char == "_" for char in current_id):
        return False, f"id '{current_id}' содержит недопустимые символы (разрешены: a-z, 0-9, _)"

    label = strategy.get("label")
    if label is not None and label not in _LABEL_MAP:
        return False, f"Неизвестный label: {label}"

    blobs = strategy.get("blobs", [])
    if not isinstance(blobs, list):
        return False, "blobs должен быть списком"

    return True, ""


def _process_args(args: Any) -> str:
    if not args:
        return ""

    if isinstance(args, list):
        raw = " ".join(str(part) for part in args)
    else:
        raw = str(args)

    return re.sub(r":strategy=\d+", "", raw)


def _normalize_strategy(strategy: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": strategy.get("id", ""),
        "name": strategy.get("name", "Без названия"),
        "description": strategy.get("description", ""),
        "author": strategy.get("author", "unknown"),
        "version": strategy.get("version", "1.0"),
        "label": _LABEL_MAP.get(strategy.get("label"), None),
        "blobs": strategy.get("blobs", []),
        "args": _process_args(strategy.get("args", "")),
        "enabled": strategy.get("enabled", True),
        "user_created": strategy.get("user_created", False),
    }


def _load_strategy_file(directory: Path, basename: str) -> Optional[Dict[str, Any]]:
    text_file = directory / f"{basename}.txt"
    if text_file.exists():
        return _load_text_file(text_file)

    json_file = directory / f"{basename}.json"
    if json_file.exists():
        return _load_json_file(json_file)

    return None


def _external_strategy_basenames(category: str, strategy_set_key: str) -> list[str]:
    target_key = str(category or "").strip().lower()
    set_key = str(strategy_set_key or "").strip().lower()
    mapped = _EXTERNAL_STRATEGY_BASENAME_MAP.get(set_key, {}).get(target_key)
    return [mapped] if mapped else []


def _load_external_strategy_set(category: str, strategy_set_key: str) -> Dict[str, Dict[str, Any]]:
    strategies: Dict[str, Dict[str, Any]] = {}

    try:
        from config import get_zapret_userdata_dir

        base_dir = str(get_zapret_userdata_dir() or "").strip()
    except Exception:
        base_dir = ""

    mode_dir = Path(base_dir) / "direct_zapret2" / f"{strategy_set_key}_strategies" if base_dir else None
    if mode_dir is None:
        return strategies

    try:
        mode_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

    loaded_basename = None
    mode_data = None
    for basename in _external_strategy_basenames(category, strategy_set_key):
        text_path = mode_dir / f"{basename}.txt"
        json_path = mode_dir / f"{basename}.json"
        if not text_path.exists() and not json_path.exists():
            continue
        loaded_basename = basename
        mode_data = _load_strategy_file(mode_dir, basename)
        break

    if mode_data and "strategies" in mode_data:
        for strategy in mode_data["strategies"]:
            is_valid, error = _validate_strategy(strategy)
            if not is_valid:
                log(f"Пропущена невалидная {strategy_set_key} стратегия: {error}", "WARNING")
                continue

            normalized = _normalize_strategy(strategy)
            normalized["_source"] = strategy_set_key
            strategies[normalized["id"]] = normalized

    log(
        f"Загружено {len(strategies)} {strategy_set_key} стратегий для категории "
        f"'{category}' ({mode_dir}, file={loaded_basename or 'missing'})",
        "DEBUG",
    )
    return strategies


def _merge_strategies(
    strategies: Dict[str, Dict[str, Any]],
    raw_data: Optional[Dict[str, Any]],
    *,
    source_name: str,
    user_created: bool = False,
) -> None:
    if not raw_data or "strategies" not in raw_data:
        return

    for strategy in raw_data["strategies"]:
        is_valid, error = _validate_strategy(strategy)
        if not is_valid:
            log(f"Пропущена невалидная {source_name} стратегия: {error}", "WARNING")
            continue

        normalized = _normalize_strategy(strategy)
        normalized["_source"] = source_name
        if user_created:
            normalized["user_created"] = True
        strategies[normalized["id"]] = normalized


def load_strategy_catalog(category: str, strategy_set: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
    """Read strategy catalog entries from builtin/user files without legacy builder dependencies."""
    category_key = str(category or "").strip().lower()
    strategy_set_key = str(strategy_set or "").strip().lower()

    if strategy_set_key in {"basic", "advanced"}:
        return _load_external_strategy_set(category_key, strategy_set_key)

    strategies: Dict[str, Dict[str, Any]] = {}
    builtin_dir = _get_builtin_dir()
    user_dir = _get_user_dir()

    basename = f"{category_key}_{strategy_set_key}" if strategy_set_key else category_key
    builtin_data = _load_strategy_file(builtin_dir, basename)

    if builtin_data is None and strategy_set_key:
        log(f"Файл {basename}.txt/.json не найден, используем стандартный {category_key}", "DEBUG")
        builtin_data = _load_strategy_file(builtin_dir, category_key)

    _merge_strategies(strategies, builtin_data, source_name="builtin")
    _merge_strategies(
        strategies,
        _load_strategy_file(user_dir, category_key),
        source_name="user",
        user_created=True,
    )

    log(f"Загружено {len(strategies)} стратегий для категории '{category_key}'", "DEBUG")
    return strategies
