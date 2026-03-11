"""
Compatibility shim.

Enterprise layout uses `app.core.settings` as the canonical settings module.
This file re-exports the same public symbols so existing imports keep working.
"""

from app.core.settings import (  # noqa: F401
    AppSettings,
    MQTTSettings,
    Settings,
    TelemetrySettings,
    ThingsBoardDownloadSettings,
    get_settings,
)

