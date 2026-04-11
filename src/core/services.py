from __future__ import annotations

"""Переходный service-locator для старых use-site'ов.

Новый composition root должен жить в `app_context.py`. Этот модуль пока нужен
как совместимый мост для тех мест, которые ещё не переведены на `AppContext`.
Правило переходного этапа такое:
1. если установлен `AppContext`, брать сервисы только из него;
2. runtime/UI/core сервисы должны требовать установленный `AppContext`;
3. новые архитектурные изменения не должны расширять этот модуль без нужды.
"""

from typing import TYPE_CHECKING, Any

from .direct_flow import DirectFlowCoordinator
from .paths import AppPaths
from .presets.repository import PresetRepository
from .presets.selection_service import PresetSelectionService

if TYPE_CHECKING:
    from app_context import AppContext


_APP_CONTEXT: "AppContext | None" = None


def install_app_context(app_context: "AppContext | None") -> None:
    global _APP_CONTEXT
    _APP_CONTEXT = app_context


def get_installed_app_context() -> "AppContext | None":
    return _APP_CONTEXT


def _context_attr(name: str) -> Any | None:
    context = _APP_CONTEXT
    if context is None:
        return None
    return getattr(context, name, None)


def _require_context_attr(name: str) -> Any:
    value = _context_attr(name)
    if value is None:
        raise RuntimeError(f"AppContext is required for service '{name}'")
    return value


def get_app_paths() -> AppPaths:
    value = _require_context_attr("app_paths")
    if isinstance(value, AppPaths):
        return value
    raise RuntimeError("AppContext service 'app_paths' has unexpected type")


def get_preset_repository() -> PresetRepository:
    value = _require_context_attr("preset_repository")
    if isinstance(value, PresetRepository):
        return value
    raise RuntimeError("AppContext service 'preset_repository' has unexpected type")


def get_selection_service() -> PresetSelectionService:
    value = _require_context_attr("preset_selection_service")
    if isinstance(value, PresetSelectionService):
        return value
    raise RuntimeError("AppContext service 'preset_selection_service' has unexpected type")


def get_direct_flow_coordinator() -> DirectFlowCoordinator:
    value = _require_context_attr("direct_flow_coordinator")
    if isinstance(value, DirectFlowCoordinator):
        return value
    raise RuntimeError("AppContext service 'direct_flow_coordinator' has unexpected type")


def get_preset_store():
    return _require_context_attr("preset_store")


def get_preset_store_v1():
    return _require_context_attr("preset_store_v1")


def get_strategy_marks_store():
    return _require_context_attr("strategy_marks_store")


def get_strategy_favorites_store():
    return _require_context_attr("strategy_favorites_store")


def get_direct_ui_snapshot_service():
    return _require_context_attr("direct_ui_snapshot_service")


def get_orchestra_whitelist_runtime_service():
    return _require_context_attr("orchestra_whitelist_runtime_service")


def get_program_settings_runtime_service():
    return _require_context_attr("program_settings_runtime_service")


def get_user_presets_runtime_service(scope_key: str):
    factory = _context_attr("user_presets_runtime_service_factory")
    if callable(factory):
        return factory(scope_key)
    raise RuntimeError("AppContext is required for service 'user_presets_runtime_service_factory'")


def reset_cached_services() -> None:
    install_app_context(None)
