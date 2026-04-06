from __future__ import annotations

from pathlib import Path
from .builtin_template_sync import (
    is_builtin_preset_file_name as _is_builtin_preset_file_name,
    list_installed_builtin_template_names,
    load_repo_builtin_templates,
    sync_repo_builtins_to_runtime_templates,
)
from .package_assets import package_dir
from .v1_template_runtime import (
    _extract_builtin_version as _extract_builtin_version_v1,
    _is_newer_builtin_version as _is_newer_builtin_version_v1,
    _normalize_template_header_v1,
    _sanitize_version_for_filename as _sanitize_version_for_filename_v1,
)


def list_repo_builtin_templates_v1() -> dict[str, str]:
    return load_repo_builtin_templates(
        _repo_builtin_templates_dir_v1(),
        normalize_content=_normalize_template_header_v1,
    )


def list_builtin_catalog_names_v1() -> list[str]:
    repo_templates = list_repo_builtin_templates_v1()
    if repo_templates:
        return sorted(repo_templates.keys(), key=lambda value: value.lower())
    return list_installed_builtin_template_names(_runtime_templates_dir_v1())


def is_builtin_preset_file_name_v1(file_name: str) -> bool:
    return _is_builtin_preset_file_name(file_name, list_builtin_catalog_names_v1())


def get_builtin_template_version_v1(content: str) -> str | None:
    return _extract_builtin_version_v1(content)


def sync_repo_builtins_to_runtime_templates_v1() -> bool:
    try:
        from config import get_zapret_presets_v1_template_dir

        templates_dir = Path(get_zapret_presets_v1_template_dir())
    except Exception:
        return False

    return sync_repo_builtins_to_runtime_templates(
        repo_templates=list_repo_builtin_templates_v1(),
        templates_dir=templates_dir,
        get_version=get_builtin_template_version_v1,
        is_newer_version=_is_newer_builtin_version_v1,
        sanitize_version_for_filename=_sanitize_version_for_filename_v1,
        log_prefix="built-in V1 template",
    )


def _repo_builtin_templates_dir_v1() -> Path:
    return package_dir("preset_zapret1") / "builtin_presets"


def _runtime_templates_dir_v1() -> Path:
    from config import get_zapret_presets_v1_template_dir

    return Path(get_zapret_presets_v1_template_dir())
