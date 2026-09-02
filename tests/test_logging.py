from __future__ import annotations

import logging
from pathlib import Path

from impossible_move.logging_config import APP_LOGGER_NAME, configure_logging


def test_configure_logging_writes_persistent_file(tmp_path: Path) -> None:
    path = configure_logging(log_dir=tmp_path, level="DEBUG", console=False)
    logger = logging.getLogger(f"{APP_LOGGER_NAME}.test")
    logger.info("persistent-test-message")
    for handler in logging.getLogger(APP_LOGGER_NAME).handlers:
        handler.flush()

    assert path == tmp_path / "impossible_move.log"
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "persistent-test-message" in text
    assert "Logging initialized" in text


def test_configure_logging_replaces_owned_handlers(tmp_path: Path) -> None:
    configure_logging(log_dir=tmp_path, console=False)
    configure_logging(log_dir=tmp_path, console=False)
    owned = [
        h for h in logging.getLogger(APP_LOGGER_NAME).handlers
        if getattr(h, "_impossible_move_handler", False)
    ]
    assert len(owned) == 1


def test_qt_message_handler_is_forwarded_to_file(tmp_path: Path) -> None:
    from impossible_move.logging_config import make_qt_message_handler

    configure_logging(log_dir=tmp_path, level="DEBUG", console=False)

    class FakeMode:
        name = "QtWarningMsg"

    class FakeContext:
        file = "Main.qml"
        line = 42
        function = "binding"

    make_qt_message_handler()(FakeMode(), FakeContext(), "qml-warning-test")
    for handler in logging.getLogger(APP_LOGGER_NAME).handlers:
        handler.flush()
    text = (tmp_path / "impossible_move.log").read_text(encoding="utf-8")
    assert "qml-warning-test" in text
    assert "Main.qml:42:binding" in text
