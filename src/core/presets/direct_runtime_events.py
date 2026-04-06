from __future__ import annotations

from core.services import (
    get_direct_flow_coordinator,
    get_preset_store,
    get_preset_store_v1,
)


def _resolve_direct_runtime_store(launch_method: str):
    method = str(launch_method or "").strip().lower()
    if method == "direct_zapret2":
        return get_preset_store()
    if method == "direct_zapret1":
        return get_preset_store_v1()
    raise ValueError(f"Unsupported direct launch method for runtime notifications: {launch_method}")


def notify_direct_preset_saved(launch_method: str, file_name: str) -> None:
    candidate = str(file_name or "").strip()
    if not candidate:
        return
    _resolve_direct_runtime_store(launch_method).notify_preset_saved(candidate)


def notify_direct_preset_switched(launch_method: str, file_name: str) -> None:
    candidate = str(file_name or "").strip()
    if not candidate:
        return
    _resolve_direct_runtime_store(launch_method).notify_preset_switched(candidate)


def activate_direct_preset_file(launch_method: str, file_name: str):
    method = str(launch_method or "").strip().lower()
    candidate = str(file_name or "").strip()
    if not candidate:
        raise ValueError("Preset file name is required")

    profile = get_direct_flow_coordinator().select_preset_file_name(method, candidate)
    notify_direct_preset_switched(method, profile.preset_file_name)
    return profile
