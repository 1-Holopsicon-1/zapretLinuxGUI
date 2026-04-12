from __future__ import annotations

from PyQt6.QtWidgets import QWidget

from ui.page_contracts import PageSignalName, get_page_signal
from ui.window_display_state import (
    on_autostart_disabled,
    on_autostart_enabled,
    on_subscription_updated,
    open_subscription_dialog,
)
from ui.window_appearance_state import (
    on_animations_changed,
    on_background_preset_changed,
    on_background_refresh_needed,
    on_editor_smooth_scroll_changed,
    on_mica_changed,
    on_opacity_changed,
    on_smooth_scroll_changed,
)
from ui.mode_switch_workflow import handle_launch_method_changed
from ui.orchestra_runtime_actions import on_clear_learned_requested
from ui.window_state_refresh import on_direct_mode_changed
from ui.strategy_detail_workflow import (
    on_open_target_detail,
    on_strategy_detail_back,
    on_strategy_detail_filter_mode_changed,
    on_strategy_detail_selected,
    on_z1_strategy_detail_selected,
    open_zapret1_target_detail,
)
from ui.strategy_selection_workflow import on_strategy_selected_from_page
from ui.navigation.navigation_controller import ensure_navigation_controller
from ui.navigation_targets import (
    resolve_preset_detail_back_page_for_method,
    resolve_preset_detail_root_page_for_method,
    resolve_strategy_detail_root_page_for_method,
    resolve_zapret1_navigation_pages,
    resolve_zapret2_navigation_pages,
)
from ui.page_names import PageName
from ui.window_adapter import ensure_window_adapter


def _show_active_zapret2_control_page(window) -> None:
    from ui.ui_workflows import ensure_ui_workflows

    ensure_ui_workflows(window).show_active_zapret2_control_page()


def _open_zapret2_preset_detail(window, preset_name: str) -> None:
    from ui.ui_workflows import ensure_ui_workflows

    ensure_ui_workflows(window).open_zapret2_preset_detail(preset_name)


def _open_zapret1_preset_detail(window, preset_name: str) -> None:
    from ui.ui_workflows import ensure_ui_workflows

    ensure_ui_workflows(window).open_zapret1_preset_detail(preset_name)


def connect_signal_once(window, key: str, signal_obj, slot_obj) -> None:
    if key in window._lazy_signal_connections:
        return
    try:
        signal_obj.connect(slot_obj)
        window._lazy_signal_connections.add(key)
    except Exception:
        pass


def _connect_page_signal_if_present(window, key: str, page, signal_name: str, slot_obj) -> bool:
    signal_obj = get_page_signal(page, signal_name)
    if signal_obj is None:
        return False
    connect_signal_once(window, key, signal_obj, slot_obj)
    return True


def _connect_show_page_signal(window, key: str, signal_obj, target_page: PageName) -> None:
    connect_signal_once(
        window,
        key,
        signal_obj,
        lambda target=target_page, adapter=ensure_window_adapter(window): adapter.show_page(target),
    )


def _connect_show_page_signal_if_present(window, key: str, page, signal_name: str, target_page: PageName) -> bool:
    signal_obj = get_page_signal(page, signal_name)
    if signal_obj is None:
        return False
    _connect_show_page_signal(window, key, signal_obj, target_page)
    return True


def _connect_z2_navigation_signals(window, page_name: PageName, page: QWidget, z2_direct) -> None:
    if page_name == PageName.ZAPRET2_DIRECT:
        _connect_page_signal_if_present(
            window,
            "z2_direct.open_target_detail",
            page,
            PageSignalName.OPEN_TARGET_DETAIL,
            lambda target_key, current_strategy_id, w=window: on_open_target_detail(w, target_key, current_strategy_id),
        )

    if page_name in (z2_direct.strategies_page, z2_direct.user_presets_page, PageName.BLOBS):
        _connect_page_signal_if_present(
            window,
            f"back_to_control.{page_name.name}",
            page,
            PageSignalName.BACK_CLICKED,
            lambda w=window: _show_active_zapret2_control_page(w),
        )

    if page_name == z2_direct.user_presets_page:
        _connect_page_signal_if_present(
            window,
            f"{page_name.name}.preset_open_requested",
            page,
            PageSignalName.PRESET_OPEN_REQUESTED,
            lambda preset_name, w=window: _open_zapret2_preset_detail(w, preset_name),
        )

    if page_name == z2_direct.preset_detail_page:
        _connect_page_signal_if_present(
            window,
            "z2_preset_detail.back_clicked",
            page,
            PageSignalName.BACK_CLICKED,
            lambda target=resolve_preset_detail_back_page_for_method("direct_zapret2"), adapter=ensure_window_adapter(window): adapter.show_page(target),
        )
        _connect_page_signal_if_present(
                window,
                "z2_preset_detail.navigate_to_root",
                page,
                PageSignalName.NAVIGATE_TO_ROOT,
                lambda target=resolve_preset_detail_root_page_for_method("direct_zapret2"), adapter=ensure_window_adapter(window): adapter.show_page(target),
        )

    if page_name == z2_direct.control_page:
        signal_obj = get_page_signal(page, PageSignalName.NAVIGATE_TO_PRESETS)
        if signal_obj is not None:
            _connect_show_page_signal(window, f"{page_name.name}.navigate_to_presets", signal_obj, z2_direct.user_presets_page)

        signal_obj = get_page_signal(page, PageSignalName.NAVIGATE_TO_DIRECT_LAUNCH)
        if signal_obj is not None:
            _connect_show_page_signal(window, f"{page_name.name}.navigate_to_direct_launch", signal_obj, z2_direct.strategies_page)

        signal_obj = get_page_signal(page, PageSignalName.NAVIGATE_TO_BLOBS)
        if signal_obj is not None:
            _connect_show_page_signal(window, f"{page_name.name}.navigate_to_blobs", signal_obj, PageName.BLOBS)

        _connect_page_signal_if_present(
            window,
            f"{page_name.name}.direct_mode_changed",
            page,
            PageSignalName.DIRECT_MODE_CHANGED,
            lambda mode, w=window: on_direct_mode_changed(w, mode),
        )

    if page_name == z2_direct.strategy_detail_page:
        _connect_page_signal_if_present(window, "strategy_detail.back_clicked", page, PageSignalName.BACK_CLICKED, lambda w=window: on_strategy_detail_back(w))
        _connect_page_signal_if_present(
                window,
                "strategy_detail.navigate_to_root",
                page,
                PageSignalName.NAVIGATE_TO_ROOT,
                lambda target=resolve_strategy_detail_root_page_for_method("direct_zapret2"), adapter=ensure_window_adapter(window): adapter.show_page(target),
        )
        _connect_page_signal_if_present(
                window,
                "strategy_detail.strategy_selected",
                page,
                PageSignalName.STRATEGY_SELECTED,
                lambda target_key, strategy_id, w=window: on_strategy_detail_selected(w, target_key, strategy_id),
        )
        _connect_page_signal_if_present(
                window,
                "strategy_detail.filter_mode_changed",
                page,
                PageSignalName.FILTER_MODE_CHANGED,
                lambda target_key, filter_mode, w=window: on_strategy_detail_filter_mode_changed(w, target_key, filter_mode),
        )


def _connect_z1_navigation_signals(window, page_name: PageName, page: QWidget, z1_pages) -> None:
    if page_name in (z1_pages.strategies_page, z1_pages.user_presets_page):
        _connect_show_page_signal_if_present(window, f"back_to_z1_control.{page_name.name}", page, PageSignalName.BACK_CLICKED, z1_pages.control_page)

    if page_name == z1_pages.user_presets_page:
        _connect_page_signal_if_present(
            window,
            "z1_user_presets.preset_open_requested",
            page,
            PageSignalName.PRESET_OPEN_REQUESTED,
            lambda preset_name, w=window: _open_zapret1_preset_detail(w, preset_name),
        )

    if page_name == z1_pages.preset_detail_page:
        _connect_show_page_signal_if_present(window, "z1_preset_detail.back_clicked", page, PageSignalName.BACK_CLICKED, resolve_preset_detail_back_page_for_method("direct_zapret1"))
        _connect_show_page_signal_if_present(window, "z1_preset_detail.navigate_to_root", page, PageSignalName.NAVIGATE_TO_ROOT, resolve_preset_detail_root_page_for_method("direct_zapret1"))

    if page_name == z1_pages.strategies_page:
        _connect_page_signal_if_present(
            window,
            "z1_direct.target_clicked",
            page,
            PageSignalName.TARGET_CLICKED,
            lambda target_key, target_info, w=window: open_zapret1_target_detail(w, target_key, target_info),
        )

    if page_name == z1_pages.strategy_detail_page:
        _connect_show_page_signal_if_present(window, "z1_strategy_detail.back_clicked", page, PageSignalName.BACK_CLICKED, z1_pages.strategies_page)
        _connect_show_page_signal_if_present(window, "z1_strategy_detail.navigate_to_control", page, PageSignalName.NAVIGATE_TO_CONTROL, resolve_strategy_detail_root_page_for_method("direct_zapret1"))
        _connect_page_signal_if_present(
                window,
                "z1_strategy_detail.strategy_selected",
                page,
                PageSignalName.STRATEGY_SELECTED,
                lambda target_key, strategy_id, w=window: on_z1_strategy_detail_selected(w, target_key, strategy_id),
        )

    if page_name == z1_pages.control_page:
        _connect_show_page_signal_if_present(window, "z1_control.navigate_to_strategies", page, PageSignalName.NAVIGATE_TO_STRATEGIES, z1_pages.strategies_page)
        _connect_show_page_signal_if_present(window, "z1_control.navigate_to_presets", page, PageSignalName.NAVIGATE_TO_PRESETS, z1_pages.user_presets_page)
        _connect_show_page_signal_if_present(window, "z1_control.navigate_to_blobs", page, PageSignalName.NAVIGATE_TO_BLOBS, PageName.BLOBS)


def _connect_common_page_signals(window, page_name: PageName, page: QWidget) -> None:
    if page_name == PageName.AUTOSTART:
        _connect_page_signal_if_present(window, "autostart.autostart_enabled", page, PageSignalName.AUTOSTART_ENABLED, lambda w=window: on_autostart_enabled(w))
        _connect_page_signal_if_present(window, "autostart.autostart_disabled", page, PageSignalName.AUTOSTART_DISABLED, lambda w=window: on_autostart_disabled(w))
        _connect_page_signal_if_present(
                window,
                "autostart.navigate_to_dpi_settings",
                page,
                PageSignalName.NAVIGATE_TO_DPI_SETTINGS,
                lambda adapter=ensure_window_adapter(window): adapter.show_page(PageName.DPI_SETTINGS),
        )

    if page_name == PageName.APPEARANCE:
        signal_obj = get_page_signal(page, PageSignalName.DISPLAY_MODE_CHANGED)
        if signal_obj is not None:
            window.display_mode_changed = signal_obj
        else:
            signal_obj = get_page_signal(page, PageSignalName.THEME_CHANGED)
            if signal_obj is not None:
                window.display_mode_changed = signal_obj

        _connect_page_signal_if_present(window, "appearance.garland_changed", page, PageSignalName.GARLAND_CHANGED, window.set_garland_enabled)
        _connect_page_signal_if_present(window, "appearance.snowflakes_changed", page, PageSignalName.SNOWFLAKES_CHANGED, window.set_snowflakes_enabled)
        _connect_page_signal_if_present(window, "appearance.background_refresh_needed", page, PageSignalName.BACKGROUND_REFRESH_NEEDED, lambda w=window: on_background_refresh_needed(w))
        _connect_page_signal_if_present(window, "appearance.background_preset_changed", page, PageSignalName.BACKGROUND_PRESET_CHANGED, lambda preset, w=window: on_background_preset_changed(w, preset))
        _connect_page_signal_if_present(window, "appearance.opacity_changed", page, PageSignalName.OPACITY_CHANGED, lambda value, w=window: on_opacity_changed(w, value))
        _connect_page_signal_if_present(window, "appearance.mica_changed", page, PageSignalName.MICA_CHANGED, lambda enabled, w=window: on_mica_changed(w, enabled))
        _connect_page_signal_if_present(window, "appearance.animations_changed", page, PageSignalName.ANIMATIONS_CHANGED, lambda enabled, w=window: on_animations_changed(w, enabled))
        _connect_page_signal_if_present(window, "appearance.smooth_scroll_changed", page, PageSignalName.SMOOTH_SCROLL_CHANGED, lambda enabled, w=window: on_smooth_scroll_changed(w, enabled))
        _connect_page_signal_if_present(window, "appearance.editor_smooth_scroll_changed", page, PageSignalName.EDITOR_SMOOTH_SCROLL_CHANGED, lambda enabled, w=window: on_editor_smooth_scroll_changed(w, enabled))
        _connect_page_signal_if_present(
                window,
                "appearance.ui_language_changed",
                page,
                PageSignalName.UI_LANGUAGE_CHANGED,
                lambda language, w=window: ensure_navigation_controller(w).on_ui_language_changed(language),
        )

    if page_name == PageName.ABOUT:
        _connect_page_signal_if_present(window, "about.open_premium_requested", page, PageSignalName.OPEN_PREMIUM_REQUESTED, lambda w=window: open_subscription_dialog(w))
        _connect_show_page_signal_if_present(window, "about.open_updates_requested", page, PageSignalName.OPEN_UPDATES_REQUESTED, PageName.SERVERS)

    if page_name == PageName.PREMIUM:
        _connect_page_signal_if_present(
            window,
            "premium.subscription_updated",
            page,
            PageSignalName.SUBSCRIPTION_UPDATED,
            lambda is_premium, days_remaining, w=window: on_subscription_updated(w, is_premium, days_remaining),
        )

    if page_name == PageName.DPI_SETTINGS:
        _connect_page_signal_if_present(window, "dpi_settings.launch_method_changed", page, PageSignalName.LAUNCH_METHOD_CHANGED, lambda method, w=window: handle_launch_method_changed(w, method))

    if page_name in (PageName.ZAPRET1_DIRECT, PageName.ZAPRET2_DIRECT):
        _connect_page_signal_if_present(
            window,
            f"strategy_selected.{page_name.name}",
            page,
            PageSignalName.STRATEGY_SELECTED,
            lambda strategy_id, strategy_name, w=window: on_strategy_selected_from_page(w, strategy_id, strategy_name),
        )


def connect_lazy_page_signals(window, page_name: PageName, page: QWidget) -> None:
    z1_pages = resolve_zapret1_navigation_pages()
    _connect_common_page_signals(window, page_name, page)

    if page_name == PageName.ZAPRET2_DIRECT:
        _connect_page_signal_if_present(
            window,
            "z2_direct.open_target_detail",
            page,
            PageSignalName.OPEN_TARGET_DETAIL,
            lambda target_key, current_strategy_id, w=window: on_open_target_detail(w, target_key, current_strategy_id),
        )
    _connect_z2_navigation_signals(window, page_name, page, resolve_zapret2_navigation_pages("direct_zapret2"))
    _connect_z1_navigation_signals(window, page_name, page, z1_pages)

    if page_name == PageName.ORCHESTRA:
        _connect_page_signal_if_present(window, "orchestra.clear_learned_requested", page, PageSignalName.CLEAR_LEARNED_REQUESTED, lambda w=window: on_clear_learned_requested(w))


__all__ = ["connect_lazy_page_signals", "connect_signal_once"]
