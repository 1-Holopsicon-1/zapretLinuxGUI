from __future__ import annotations

from ui.main_window_state import AppUiState, MainWindowStateStore


class AppRuntimeState:
    """Единая точка записи и чтения runtime-состояния GUI."""

    def __init__(self, app_instance) -> None:
        self.app = app_instance

    def _store(self) -> MainWindowStateStore | None:
        store = getattr(self.app, "ui_state_store", None)
        if isinstance(store, MainWindowStateStore):
            return store
        return None

    def snapshot(self) -> AppUiState:
        store = self._store()
        if store is None:
            return AppUiState()
        try:
            return store.snapshot()
        except Exception:
            return AppUiState()

    def is_dpi_running(self) -> bool:
        return bool(self.snapshot().dpi_running)

    def is_autostart_enabled(self) -> bool:
        return bool(self.snapshot().autostart_enabled)

    def current_launch_method(self) -> str:
        return str(self.snapshot().launch_method or "")

    def apply_runtime_state(
        self,
        *,
        dpi_running: bool | None = None,
        autostart_enabled: bool | None = None,
        autostart_type: str | None = None,
        launch_method: str | None = None,
    ) -> bool:
        store = self._store()
        if store is None:
            return False

        changes: dict[str, object] = {}

        if launch_method is not None:
            changes["launch_method"] = str(launch_method or "").strip().lower()

        if dpi_running is not None:
            changes["dpi_running"] = bool(dpi_running)

        if autostart_enabled is not None:
            enabled = bool(autostart_enabled)
            changes["autostart_enabled"] = enabled
            changes["autostart_type"] = str(autostart_type or "") if enabled else ""

        if not changes:
            return False

        return bool(store.update(**changes))

    def set_dpi_running(self, running: bool) -> bool:
        return self.apply_runtime_state(dpi_running=running)

    def set_autostart(self, enabled: bool, autostart_type: str | None = None) -> bool:
        return self.apply_runtime_state(
            autostart_enabled=enabled,
            autostart_type=autostart_type,
        )

    def set_launch_method(self, method: str | None) -> bool:
        normalized = str(method or "").strip().lower()
        if not normalized:
            normalized = self.detect_launch_method()
        return self.apply_runtime_state(launch_method=normalized)

    def sync_autostart_from_registry(self) -> bool:
        return self.set_autostart(self.detect_autostart_enabled())

    @staticmethod
    def detect_launch_method() -> str:
        try:
            from strategy_menu import get_strategy_launch_method

            return str(get_strategy_launch_method() or "").strip().lower()
        except Exception:
            return ""

    @staticmethod
    def detect_autostart_enabled() -> bool:
        try:
            from autostart.registry_check import is_autostart_enabled

            return bool(is_autostart_enabled())
        except Exception:
            return False
