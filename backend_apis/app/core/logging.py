import logging

from app.core.settings import get_settings


def configure_logging() -> None:
    """
    Configure application-wide logging.

    Kept in a dedicated module so the entrypoint (`app.main`) stays small and readable.
    """
    settings = get_settings()
    logging.basicConfig(
        level=getattr(logging, settings.app.log_level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )

