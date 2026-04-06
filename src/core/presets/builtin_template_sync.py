from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Callable, Iterable

from log import log

from .builtin_catalog import list_builtin_presets


def list_repo_builtin_template_paths(src_dir: Path) -> list[Path]:
    base = Path(src_dir)
    if not base.exists() or not base.is_dir():
        return []
    return [
        path
        for path in list_builtin_presets(base)
        if path.is_file() and not path.name.startswith("_")
    ]


def list_installed_builtin_template_names(templates_dir: Path) -> list[str]:
    base = Path(templates_dir)
    if not base.exists() or not base.is_dir():
        return []
    names: list[str] = []
    for path in list_builtin_presets(base):
        name = str(path.stem or "").strip()
        if name:
            names.append(name)
    return names


def load_repo_builtin_templates(
    src_dir: Path,
    *,
    normalize_content: Callable[[str, str], str],
) -> dict[str, str]:
    contents: dict[str, str] = {}
    for path in list_repo_builtin_template_paths(src_dir):
        name = str(path.stem or "").strip()
        if not name:
            continue
        try:
            raw = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        contents[name] = normalize_content(raw, name)
    return contents


def is_builtin_preset_file_name(file_name: str, builtin_names: Iterable[str]) -> bool:
    candidate = str(Path(str(file_name or "").strip()).stem or "").strip()
    if not candidate:
        return False
    target = candidate.casefold()
    return any(str(name or "").strip().casefold() == target for name in builtin_names)


def sync_repo_builtins_to_runtime_templates(
    *,
    repo_templates: dict[str, str],
    templates_dir: Path,
    get_version: Callable[[str], str | None],
    is_newer_version: Callable[[str | None, str | None], bool],
    sanitize_version_for_filename: Callable[[str | None], str],
    log_prefix: str,
) -> bool:
    if not repo_templates:
        return False

    templates_dir.mkdir(parents=True, exist_ok=True)
    backups_dir = templates_dir / "_builtin_version_backups"
    changed = False

    for name, content in repo_templates.items():
        dest = templates_dir / f"{name}.txt"
        repo_version = get_version(content)

        if not dest.exists():
            try:
                dest.write_text(content, encoding="utf-8")
                changed = True
                log(f"Seeded {log_prefix}: {dest}", "DEBUG")
            except Exception as exc:
                log(f"Failed to seed {log_prefix} {dest.name}: {exc}", "DEBUG")
            continue

        try:
            existing_content = dest.read_text(encoding="utf-8", errors="replace")
        except Exception:
            existing_content = ""
        existing_version = get_version(existing_content)

        if not is_newer_version(repo_version, existing_version):
            continue

        try:
            backups_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            from_v = sanitize_version_for_filename(existing_version)
            to_v = sanitize_version_for_filename(repo_version)
            backup_name = f"{dest.stem}__{timestamp}__{from_v}_to_{to_v}.txt"
            (backups_dir / backup_name).write_text(existing_content, encoding="utf-8")
        except Exception:
            pass

        try:
            dest.write_text(content, encoding="utf-8")
            changed = True
            log(
                f"{log_prefix.capitalize()} updated from repo version {existing_version or 'none'} "
                f"to {repo_version or 'none'}: {dest}",
                "DEBUG",
            )
        except Exception as exc:
            log(f"Failed to update {log_prefix} {dest.name}: {exc}", "DEBUG")

    return changed
