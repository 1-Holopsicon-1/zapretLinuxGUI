from __future__ import annotations

from ui.navigation_targets import (
    resolve_control_page_for_method,
    resolve_zapret1_navigation_pages,
    resolve_zapret2_navigation_pages,
)
from ui.page_contracts import PageMethodName, get_page_method
from ui.page_names import PageName
from ui.window_adapter import ensure_window_adapter


class WindowUiWorkflows:
    """UI-side сценарии переходов между страницами.

    Здесь живёт именно orchestration пользовательских переходов:
    detail/open/back/root/preset flow. Это не schema и не page lifecycle.
    """

    def __init__(self, window):
        self._window = window

    def refresh_page_if_possible(self, page_name: PageName) -> None:
        page = ensure_window_adapter(self._window).ensure_page(page_name)
        if page is None:
            return
        self._call_page_method(page, PageMethodName.REFRESH_PRESETS_VIEW)

    def _call_page_method(self, page, method_name: str, *args) -> bool:
        if page is None:
            return False
        handler = get_page_method(page, method_name)
        if handler is None:
            return False
        try:
            handler(*args)
            return True
        except Exception:
            return False

    def _refresh_or_show_page_after_refresh_if_possible(
        self,
        page_name: PageName,
        *,
        show_page: bool,
    ) -> None:
        self.refresh_page_if_possible(page_name)
        if show_page:
            ensure_window_adapter(self._window).show_page(page_name)

    @staticmethod
    def _get_current_launch_method(*, default: str = "") -> str:
        try:
            from strategy_menu import get_strategy_launch_method

            return str(get_strategy_launch_method() or "").strip().lower()
        except Exception:
            return str(default or "").strip().lower()

    def _resolve_zapret2_user_presets_page(self, method: str | None) -> PageName:
        return resolve_zapret2_navigation_pages(method).user_presets_page

    def _resolve_zapret2_preset_detail_page(self, method: str | None) -> PageName:
        return resolve_zapret2_navigation_pages(method).preset_detail_page

    def _show_static_page(self, page_name: PageName) -> None:
        ensure_window_adapter(self._window).show_page(page_name)

    def _get_strategies_context_pages(self) -> set:
        strategies_context_pages = set()
        z2_direct = resolve_zapret2_navigation_pages("direct_zapret2")
        for page_name in (
            PageName.DPI_SETTINGS,
            z2_direct.user_presets_page,
            z2_direct.strategies_page,
            PageName.ZAPRET1_DIRECT_CONTROL,
            PageName.ZAPRET1_DIRECT,
            PageName.ZAPRET1_USER_PRESETS,
            z2_direct.strategy_detail_page,
        ):
            page = ensure_window_adapter(self._window).get_loaded_page(page_name)
            if page is not None:
                strategies_context_pages.add(page)
        return strategies_context_pages

    def _get_remembered_z2_detail_target(self) -> tuple[str | None, bool]:
        last_key = getattr(self._window, "_direct_zapret2_last_opened_target_key", None)
        want_restore = bool(getattr(self._window, "_direct_zapret2_restore_detail_on_open", False))
        normalized_key = str(last_key or "").strip() or None
        return normalized_key, want_restore

    def _remember_z2_detail_target(self, target_key: str) -> None:
        try:
            self._window._direct_zapret2_last_opened_target_key = str(target_key or "").strip() or None
            self._window._direct_zapret2_restore_detail_on_open = True
        except Exception:
            pass

    def _clear_remembered_z2_detail_target(self) -> None:
        try:
            self._window._direct_zapret2_last_opened_target_key = None
            self._window._direct_zapret2_restore_detail_on_open = False
        except Exception:
            pass

    def _resolve_navigation_target_for_strategies(
        self,
        method: str | None,
        *,
        allow_restore_z2_detail: bool,
    ) -> PageName:
        normalized = str(method or "").strip().lower()
        target_page = resolve_control_page_for_method(normalized)

        if normalized != "direct_zapret2" or not allow_restore_z2_detail:
            return target_page

        z2_direct = resolve_zapret2_navigation_pages("direct_zapret2")
        last_key, want_restore = self._get_remembered_z2_detail_target()
        if not (want_restore and last_key):
            return target_page

        try:
            from core.presets.direct_facade import DirectPresetFacade

            facade = DirectPresetFacade.from_launch_method("direct_zapret2", app_context=self._window.app_context)
            if facade.get_target_ui_item(last_key) and self.open_zapret2_strategy_detail(
                last_key,
                remember=False,
                show_page=False,
            ):
                return z2_direct.strategy_detail_page
        except Exception:
            pass

        self._clear_remembered_z2_detail_target()
        return z2_direct.control_page

    def _open_preset_detail_page(self, page_name: PageName, preset_name: str) -> None:
        page = ensure_window_adapter(self._window).ensure_page(page_name)
        if page is None:
            return
        self._call_page_method(page, PageMethodName.SET_PRESET_FILE_NAME, preset_name)
        ensure_window_adapter(self._window).show_page(page_name)

    def open_zapret2_strategy_detail(
        self,
        target_key: str,
        *,
        remember: bool = True,
        show_page: bool = True,
    ) -> bool:
        detail_page = ensure_window_adapter(self._window).ensure_page(PageName.ZAPRET2_STRATEGY_DETAIL)
        if detail_page is None:
            return False

        if not self._call_page_method(detail_page, PageMethodName.SHOW_TARGET, target_key):
            return False

        if show_page:
            ensure_window_adapter(self._window).show_page(PageName.ZAPRET2_STRATEGY_DETAIL)

        if remember:
            self._remember_z2_detail_target(target_key)

        return True

    def open_zapret1_strategy_detail(self, target_key: str) -> bool:
        detail_page = ensure_window_adapter(self._window).ensure_page(PageName.ZAPRET1_STRATEGY_DETAIL)
        if detail_page is None:
            return False

        try:
            from core.presets.direct_facade import DirectPresetFacade

            def _reload_dpi() -> None:
                try:
                    from direct_launch.flow.apply_policy import request_direct_runtime_content_apply

                    request_direct_runtime_content_apply(
                        self._window,
                        launch_method="direct_zapret1",
                        reason="target_settings_changed",
                        target_key=target_key,
                    )
                except Exception:
                    pass

            manager = DirectPresetFacade.from_launch_method(
                "direct_zapret1",
                app_context=self._window.app_context,
                on_dpi_reload_needed=_reload_dpi,
            )
        except Exception:
            return False

        if not self._call_page_method(detail_page, PageMethodName.SHOW_TARGET, target_key, manager):
            return False

        ensure_window_adapter(self._window).show_page(PageName.ZAPRET1_STRATEGY_DETAIL)
        return True

    def show_active_zapret2_user_presets_page(self) -> None:
        method = self._get_current_launch_method()
        self._refresh_or_show_page_after_refresh_if_possible(
            self._resolve_zapret2_user_presets_page(method),
            show_page=True,
        )

    def show_zapret1_user_presets_page(self) -> None:
        self._refresh_or_show_page_after_refresh_if_possible(
            resolve_zapret1_navigation_pages().user_presets_page,
            show_page=True,
        )

    def refresh_active_zapret2_user_presets_page(self) -> None:
        method = self._get_current_launch_method()
        self._refresh_or_show_page_after_refresh_if_possible(
            self._resolve_zapret2_user_presets_page(method),
            show_page=False,
        )

    def refresh_zapret1_user_presets_page(self) -> None:
        self._refresh_or_show_page_after_refresh_if_possible(
            resolve_zapret1_navigation_pages().user_presets_page,
            show_page=False,
        )

    def open_zapret2_preset_detail(self, preset_name: str) -> None:
        method = self._get_current_launch_method()
        self._open_preset_detail_page(self._resolve_zapret2_preset_detail_page(method), preset_name)

    def open_zapret1_preset_detail(self, preset_name: str) -> None:
        self._open_preset_detail_page(resolve_zapret1_navigation_pages().preset_detail_page, preset_name)

    def redirect_to_strategies_page_for_method(self, method: str) -> None:
        current = None
        try:
            current = self._window.stackedWidget.currentWidget() if hasattr(self._window, "stackedWidget") else None
        except Exception:
            current = None

        strategies_context_pages = self._get_strategies_context_pages()

        if current is not None and current not in strategies_context_pages:
            return

        ensure_window_adapter(self._window).show_page(
            self._resolve_navigation_target_for_strategies(
                method,
                allow_restore_z2_detail=False,
            )
        )

    def show_autostart_page(self) -> None:
        self._show_static_page(PageName.AUTOSTART)

    def show_hosts_page(self) -> None:
        self._show_static_page(PageName.HOSTS)

    def show_servers_page(self) -> None:
        self._show_static_page(PageName.SERVERS)

    def show_active_zapret2_control_page(self) -> None:
        method = self._get_current_launch_method(default="direct_zapret2")
        ensure_window_adapter(self._window).show_page(resolve_zapret2_navigation_pages(method).control_page)

    def navigate_to_control(self) -> None:
        method = self._get_current_launch_method()
        ensure_window_adapter(self._window).show_page(resolve_control_page_for_method(method))

    def navigate_to_strategies(self) -> None:
        method = self._get_current_launch_method(default="direct_zapret2")
        target_page = self._resolve_navigation_target_for_strategies(
            method,
            allow_restore_z2_detail=True,
        )
        ensure_window_adapter(self._window).show_page(target_page)


def ensure_ui_workflows(window) -> WindowUiWorkflows:
    workflows = getattr(window, "_ui_workflows", None)
    if workflows is None:
        workflows = WindowUiWorkflows(window)
        window._ui_workflows = workflows
    return workflows


__all__ = ["WindowUiWorkflows", "ensure_ui_workflows"]
