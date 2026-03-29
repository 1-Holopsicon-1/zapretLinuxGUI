from __future__ import annotations

from log import log
from .launch_method_store import get_strategy_launch_method

_direct_selections_cache = None
_direct_selections_cache_time = 0
_direct_selections_cache_method = None
_direct_selections_cache_preset_mtime = None
DIRECT_SELECTIONS_CACHE_TTL = 5.0


def invalidate_direct_selections_cache():
    """Сбрасывает кэш выборов стратегий."""
    global _direct_selections_cache_time, _direct_selections_cache_method, _direct_selections_cache_preset_mtime
    _direct_selections_cache_time = 0
    _direct_selections_cache_method = None
    _direct_selections_cache_preset_mtime = None


def get_direct_strategy_selections() -> dict:
    """
    Возвращает сохраненные выборы стратегий для прямого запуска.
    """
    import time
    global _direct_selections_cache, _direct_selections_cache_time, _direct_selections_cache_preset_mtime, _direct_selections_cache_method

    method = get_strategy_launch_method()

    cache_mtime = None
    if method == "direct_zapret1":
        try:
            from core.services import get_direct_flow_coordinator

            preset_path = get_direct_flow_coordinator().get_selected_source_path("direct_zapret1")
            cache_mtime = preset_path.stat().st_mtime if preset_path.exists() else None
        except Exception:
            cache_mtime = None
    elif method == "direct_zapret2":
        try:
            from core.services import get_direct_flow_coordinator

            preset_path = get_direct_flow_coordinator().get_selected_source_path("direct_zapret2")
            cache_mtime = preset_path.stat().st_mtime if preset_path.exists() else None
        except Exception:
            cache_mtime = None

    current_time = time.time()
    if (
        _direct_selections_cache is not None
        and current_time - _direct_selections_cache_time < DIRECT_SELECTIONS_CACHE_TTL
        and _direct_selections_cache_method == method
        and _direct_selections_cache_preset_mtime == cache_mtime
    ):
        return _direct_selections_cache.copy()

    from .strategies_registry import registry

    try:
        selections: dict[str, str] = {}
        default_selections = registry.get_default_selections()

        if method == "direct_zapret2":
            try:
                from core.services import get_direct_flow_coordinator
                from preset_zapret2.preset_manager import PresetManager

                coordinator = get_direct_flow_coordinator()
                selected_file_name = (coordinator.get_selected_source_file_name("direct_zapret2") or "").strip()
                selections = {k: "none" for k in registry.get_all_category_keys()}
                if selected_file_name:
                    preset_path = coordinator.get_selected_source_path("direct_zapret2")
                    if preset_path.exists():
                        preset = PresetManager().get_selected_source_preset()
                        if preset is not None:
                            selections.update(
                                {
                                    k: (getattr(v, "strategy_id", "") or "none")
                                    for k, v in (preset.categories or {}).items()
                                }
                            )
            except Exception as e:
                log(f"Ошибка чтения selected source preset для выбора стратегий direct_zapret2: {e}", "DEBUG")
                selections = {k: "none" for k in registry.get_all_category_keys()}
        elif method == "direct_zapret1":
            try:
                from core.services import get_direct_flow_coordinator
                from preset_zapret1.preset_manager import PresetManagerV1

                coordinator = get_direct_flow_coordinator()
                selected_file_name = (coordinator.get_selected_source_file_name("direct_zapret1") or "").strip()
                selections = {k: "none" for k in registry.get_all_category_keys()}
                if selected_file_name:
                    preset_path = coordinator.get_selected_source_path("direct_zapret1")
                    if preset_path.exists():
                        preset = PresetManagerV1().get_selected_source_preset()
                        if preset is not None:
                            selections.update(
                                {
                                    k: (getattr(v, "strategy_id", "") or "none")
                                    for k, v in (preset.categories or {}).items()
                                }
                            )
            except Exception as e:
                log(f"Ошибка чтения selected source preset для выбора стратегий direct_zapret1: {e}", "DEBUG")
                selections = {k: "none" for k in registry.get_all_category_keys()}
        elif method == "direct_zapret2_orchestra":
            try:
                from preset_orchestra_zapret2 import PresetManager, ensure_default_preset_exists

                ensure_default_preset_exists()
                preset_manager = PresetManager()
                preset_selections = preset_manager.get_strategy_selections() or {}
                selections = {k: "none" for k in registry.get_all_category_keys()}
                selections.update({k: (v or "none") for k, v in preset_selections.items()})
            except Exception as e:
                log(f"Ошибка чтения preset-zapret2-orchestra.txt для выбора стратегий: {e}", "DEBUG")
                selections = {k: "none" for k in registry.get_all_category_keys()}
        else:
            selections = dict(default_selections)

        for key, default_value in default_selections.items():
            if key not in selections:
                if method == "direct_zapret2_orchestra":
                    selections[key] = "none"
                elif method == "direct_zapret1":
                    selections[key] = "none"
                else:
                    selections[key] = default_value

        _direct_selections_cache = selections
        _direct_selections_cache_time = current_time
        _direct_selections_cache_method = method
        _direct_selections_cache_preset_mtime = cache_mtime
        return selections
    except Exception as e:
        log(f"Ошибка загрузки выборов стратегий: {e}", "❌ ERROR")
        import traceback
        log(traceback.format_exc(), "DEBUG")
        from .strategies_registry import registry
        return registry.get_default_selections()


def set_direct_strategy_selections(selections: dict) -> bool:
    """Сохраняет выборы стратегий для прямого запуска."""
    from .strategies_registry import registry

    try:
        method = get_strategy_launch_method()
        if method == "direct_zapret2":
            from core.presets.direct_facade import DirectPresetFacade

            facade = DirectPresetFacade.from_launch_method("direct_zapret2")
            payload = {
                category_key: strategy_id
                for category_key, strategy_id in (selections or {}).items()
                if category_key in registry.get_all_category_keys()
            }
            facade.set_strategy_selections(payload, save_and_sync=True)
            invalidate_direct_selections_cache()
            log("Выборы стратегий сохранены (selected source preset direct_zapret2)", "DEBUG")
            return True

        if method == "direct_zapret1":
            from core.presets.direct_facade import DirectPresetFacade

            facade = DirectPresetFacade.from_launch_method("direct_zapret1")
            payload = {
                category_key: strategy_id
                for category_key, strategy_id in (selections or {}).items()
                if category_key in registry.get_all_category_keys()
            }
            success = bool(facade.set_strategy_selections(payload, save_and_sync=True))
            invalidate_direct_selections_cache()
            log("Выборы стратегий сохранены (selected source preset direct_zapret1)", "DEBUG")
            return success

        if method == "direct_zapret2_orchestra":
            from preset_orchestra_zapret2 import PresetManager, ensure_default_preset_exists

            if not ensure_default_preset_exists():
                return False

            preset_manager = PresetManager()
            payload = {
                category_key: (str((selections or {}).get(category_key) or "none").strip() or "none")
                for category_key in registry.get_all_category_keys()
            }
            preset_manager.set_strategy_selections(payload, save_and_sync=True)
            invalidate_direct_selections_cache()
            log("Выборы стратегий сохранены (preset-zapret2-orchestra.txt)", "DEBUG")
            return True

        return False
    except Exception as e:
        log(f"Ошибка сохранения выборов: {e}", "❌ ERROR")
        return False


def get_direct_strategy_for_category(category_key: str) -> str:
    """Получает выбранную стратегию для конкретной категории."""
    from .strategies_registry import registry

    method = get_strategy_launch_method()
    if method in ("direct_zapret2", "direct_zapret1", "direct_zapret2_orchestra"):
        selections = get_direct_strategy_selections()
        return selections.get(category_key, "none") or "none"

    category_info = registry.get_category_info(category_key)
    if category_info:
        return category_info.default_strategy
    return "none"


def set_direct_strategy_for_category(category_key: str, strategy_id: str) -> bool:
    """Сохраняет выбранную стратегию для категории."""
    method = get_strategy_launch_method()

    if method == "direct_zapret2":
        try:
            from core.presets.direct_facade import DirectPresetFacade

            DirectPresetFacade.from_launch_method("direct_zapret2").set_strategy_selection(
                category_key,
                strategy_id,
                save_and_sync=True,
            )
            invalidate_direct_selections_cache()
            return True
        except Exception as e:
            log(f"Ошибка сохранения стратегии в selected source preset direct_zapret2: {e}", "DEBUG")
            return False

    if method == "direct_zapret1":
        try:
            from core.presets.direct_facade import DirectPresetFacade

            DirectPresetFacade.from_launch_method("direct_zapret1").set_strategy_selection(
                category_key,
                strategy_id,
                save_and_sync=True,
            )
            invalidate_direct_selections_cache()
            return True
        except Exception as e:
            log(f"Ошибка сохранения стратегии в selected source preset direct_zapret1: {e}", "DEBUG")
            return False

    if method == "direct_zapret2_orchestra":
        try:
            from preset_orchestra_zapret2 import PresetManager, ensure_default_preset_exists

            if not ensure_default_preset_exists():
                return False

            preset_manager = PresetManager()
            preset_manager.set_strategy_selection(category_key, strategy_id or "none", save_and_sync=True)
            invalidate_direct_selections_cache()
            return True
        except Exception as e:
            log(f"Ошибка сохранения стратегии в preset-zapret2-orchestra.txt: {e}", "DEBUG")
            return False

    return False
