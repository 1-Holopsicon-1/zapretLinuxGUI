"""Ленивые экспорты Orchestra Zapret2 pages."""

from __future__ import annotations

from importlib import import_module


_PAGE_EXPORTS: dict[str, tuple[str, str]] = {
    "OrchestraZapret2DirectControlPage": (".direct_control_page", "OrchestraZapret2DirectControlPage"),
    "OrchestraZapret2PresetDetailPage": (".preset_detail_page", "OrchestraZapret2PresetDetailPage"),
    "OrchestraZapret2StrategyDetailPage": (".strategy_detail_page", "OrchestraZapret2StrategyDetailPage"),
    "OrchestraZapret2UserPresetsPage": (".user_presets_page", "OrchestraZapret2UserPresetsPage"),
}

__all__ = list(_PAGE_EXPORTS)


def __getattr__(name: str):
    spec = _PAGE_EXPORTS.get(name)
    if spec is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module_name, attr_name = spec
    module = import_module(module_name, __name__)
    value = getattr(module, attr_name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
