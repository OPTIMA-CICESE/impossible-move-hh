from __future__ import annotations

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from types import TracebackType
from typing import Callable

APP_LOGGER_NAME = "impossible_move"
DEFAULT_MAX_BYTES = 5 * 1024 * 1024
DEFAULT_BACKUP_COUNT = 5


def default_log_root() -> Path:
    """Return a per-user writable directory for persistent application logs."""
    override = os.environ.get("IMPOSSIBLE_MOVE_LOG_DIR")
    if override:
        return Path(override).expanduser()
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return base / "ImpossibleMove" / "logs"
    state_home = os.environ.get("XDG_STATE_HOME")
    base = Path(state_home).expanduser() if state_home else Path.home() / ".local" / "state"
    return base / "impossible_move" / "logs"


def configure_logging(
    *,
    log_dir: str | Path | None = None,
    level: str | int = "INFO",
    console: bool = True,
    max_bytes: int = DEFAULT_MAX_BYTES,
    backup_count: int = DEFAULT_BACKUP_COUNT,
) -> Path:
    """Configure persistent rotating logging for the application.

    The function is idempotent for this package: previously installed handlers
    created by this function are replaced, which is useful in tests and when a
    caller changes ``--log-dir``.
    """
    directory = Path(log_dir).expanduser() if log_dir is not None else default_log_root()
    directory.mkdir(parents=True, exist_ok=True)
    log_path = directory / "impossible_move.log"

    numeric_level = logging.getLevelName(level.upper()) if isinstance(level, str) else int(level)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Unknown log level: {level}")

    logger = logging.getLogger(APP_LOGGER_NAME)
    logger.setLevel(numeric_level)
    logger.propagate = False

    for handler in list(logger.handlers):
        if getattr(handler, "_impossible_move_handler", False):
            logger.removeHandler(handler)
            handler.close()

    formatter = logging.Formatter(
        fmt="%(asctime)s.%(msecs)03d | %(levelname)-8s | %(threadName)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(formatter)
    file_handler._impossible_move_handler = True  # type: ignore[attr-defined]
    logger.addHandler(file_handler)

    if console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(formatter)
        console_handler._impossible_move_handler = True  # type: ignore[attr-defined]
        logger.addHandler(console_handler)

    logger.info("Logging initialized | file=%s | level=%s", log_path, logging.getLevelName(numeric_level))
    return log_path


def install_exception_hook() -> Callable[[type[BaseException], BaseException, TracebackType | None], None]:
    """Install an exception hook that preserves uncaught Python exceptions."""
    previous = sys.excepthook
    logger = logging.getLogger(f"{APP_LOGGER_NAME}.uncaught")

    def hook(exc_type: type[BaseException], exc: BaseException, tb: TracebackType | None) -> None:
        if issubclass(exc_type, KeyboardInterrupt):
            previous(exc_type, exc, tb)
            return
        logger.critical("Uncaught exception", exc_info=(exc_type, exc, tb))
        previous(exc_type, exc, tb)

    sys.excepthook = hook
    return previous


def make_qt_message_handler():
    """Create a Qt message handler without importing PySide6 in this module."""
    logger = logging.getLogger(f"{APP_LOGGER_NAME}.qt")

    def handler(mode, context, message: str) -> None:
        name = getattr(mode, "name", str(mode))
        lowered = name.lower()
        if "fatal" in lowered or "critical" in lowered:
            level = logging.CRITICAL if "fatal" in lowered else logging.ERROR
        elif "warning" in lowered:
            level = logging.WARNING
        elif "debug" in lowered:
            level = logging.DEBUG
        else:
            level = logging.INFO

        location_parts: list[str] = []
        file_name = getattr(context, "file", None)
        line = getattr(context, "line", None)
        function = getattr(context, "function", None)
        if file_name:
            location_parts.append(str(file_name))
        if line:
            location_parts.append(str(line))
        if function:
            location_parts.append(str(function))
        location = ":".join(location_parts)
        if location:
            logger.log(level, "%s | %s", message, location)
        else:
            logger.log(level, "%s", message)

    return handler
