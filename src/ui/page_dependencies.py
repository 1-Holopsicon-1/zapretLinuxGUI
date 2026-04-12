from __future__ import annotations


INJECTABLE_PAGE_ATTRS: tuple[str, ...] = (
    "app_context",
    "app_runtime_state",
    "launch_runtime_service",
    "launch_runtime_api",
    "launch_controller",
    "ui_state_store",
    "window_notification_controller",
    "orchestra_runner",
)


def inject_page_dependencies(page, window) -> None:
    for attr_name in INJECTABLE_PAGE_ATTRS:
        try:
            current_value = getattr(page, attr_name, None)
        except Exception:
            current_value = None
        if current_value is not None:
            continue

        try:
            window_value = getattr(window, attr_name, None)
        except Exception:
            window_value = None
        if window_value is None:
            continue

        try:
            setattr(page, attr_name, window_value)
        except Exception:
            pass


__all__ = ["INJECTABLE_PAGE_ATTRS", "inject_page_dependencies"]
