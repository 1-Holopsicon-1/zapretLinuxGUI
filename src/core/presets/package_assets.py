from __future__ import annotations

from pathlib import Path


def public_runtime_root() -> Path:
    """Returns the bundled public runtime root.

    In source-tree execution this resolves to `public_zapretgui/src/`.
    In bundled execution it resolves to the extracted runtime root where
    PyInstaller/Nuitka place package data next to Python modules.
    """
    return Path(__file__).resolve().parents[2]


def package_dir(package_name: str) -> Path:
    module = __import__(package_name, fromlist=["__file__"])
    return Path(module.__file__).resolve().parent
