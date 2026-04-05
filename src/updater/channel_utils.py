from __future__ import annotations


CANONICAL_UPDATE_CHANNELS = ("stable", "test")
_UPDATE_CHANNEL_ALIASES = {
    "dev": "test",
}


def normalize_update_channel(channel: str) -> str:
    """Normalize runtime update channel to one canonical value."""
    normalized = str(channel or "").strip().lower()
    if normalized in _UPDATE_CHANNEL_ALIASES:
        normalized = _UPDATE_CHANNEL_ALIASES[normalized]
    if normalized in CANONICAL_UPDATE_CHANNELS:
        return normalized
    return "stable"


def is_test_update_channel(channel: str) -> bool:
    return normalize_update_channel(channel) == "test"


def get_channel_installer_name(channel: str) -> str:
    return "Zapret2Setup_TEST.exe" if is_test_update_channel(channel) else "Zapret2Setup.exe"


def is_test_release_asset_name(file_name: str) -> bool:
    upper_name = str(file_name or "").strip().upper()
    return upper_name.startswith("ZAPRET2SETUP_TEST") or "_TEST" in upper_name
