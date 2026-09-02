from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from impossible_move.experiments import DEFAULT_BATCH_SEED, INSTANCE_LABELS, SUPPORTED_PROFILES, ExperimentConfiguration
from impossible_move.logging_config import configure_logging, install_exception_hook, make_qt_message_handler


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Impossible Move outreach visualizer")
    parser.add_argument(
        "trace",
        nargs="?",
        type=Path,
        help="Optional existing RunTrace JSON. If omitted, a generated experiment is solved.",
    )
    parser.add_argument("--catalog", type=Path, help="Replay catalog for an existing trace")
    parser.add_argument(
        "--mode",
        choices=("presentation", "detailed"),
        default="presentation",
        help="Initial replay visibility mode",
    )
    parser.add_argument("--speed", type=float, default=None, help="Initial replay speed; defaults adapt to instance size")
    parser.add_argument("--items", type=int, default=10, help="Generated experiment item count")
    parser.add_argument("--capacity", type=int, default=10, help="Generated truck capacity")
    parser.add_argument(
        "--instance",
        choices=INSTANCE_LABELS,
        default="A",
        help="Generated candidate A-E",
    )
    parser.add_argument("--batch-seed", type=int, default=DEFAULT_BATCH_SEED)
    parser.add_argument("--profile", choices=SUPPORTED_PROFILES, default="natural", help="Generated corpus profile")
    parser.add_argument("--cache-dir", type=Path, help="Optional experiment cache directory")
    parser.add_argument("--language", choices=("es", "en"), default="es", help="Initial interface language")
    parser.add_argument("--theme", choices=("dark", "light"), default="dark", help="Initial interface theme")
    parser.add_argument("--log-dir", type=Path, help="Directory for persistent application logs")
    parser.add_argument(
        "--log-level",
        choices=("DEBUG", "INFO", "WARNING", "ERROR"),
        default="INFO",
        help="Persistent log verbosity",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    log_path = configure_logging(log_dir=args.log_dir, level=args.log_level)
    install_exception_hook()
    logger = logging.getLogger("impossible_move.frontend.app")
    logger.info(
        "Application starting | language=%s | profile=%s | items=%s | capacity=%s | instance=%s | log=%s",
        args.language, args.profile, args.items, args.capacity, args.instance, log_path,
    )

    try:
        from PySide6.QtCore import QUrl, qInstallMessageHandler
        from PySide6.QtGui import QGuiApplication, QIcon
        from PySide6.QtQml import QQmlApplicationEngine
    except ModuleNotFoundError as exc:
        logger.exception("PySide6 is not installed")
        raise SystemExit(
            "PySide6 is required for the GUI. Install with: pip install -e '.[gui]'"
        ) from exc

    qt_message_handler = make_qt_message_handler()
    qInstallMessageHandler(qt_message_handler)

    from impossible_move.experiments import ExperimentCache, ExperimentService
    from impossible_move.replay import ReplayController, ReplayMode, read_catalog
    from impossible_move.trace.serialization import read_trace

    from .experiment_adapter import QtExperimentAdapter
    from .comparison_adapter import QtComparisonAdapter
    from .i18n import tr
    from .language_adapter import QtLanguageAdapter
    from .theme_adapter import QtThemeAdapter
    from .qt_adapter import QtReplayAdapter

    config = ExperimentConfiguration(
        item_count=args.items,
        truck_capacity=args.capacity,
        instance_index=INSTANCE_LABELS.index(args.instance),
        batch_seed=args.batch_seed,
        profile=args.profile,
    )
    cache = ExperimentCache(args.cache_dir) if args.cache_dir else ExperimentCache()
    service = ExperimentService(cache=cache)

    active = None
    if args.trace is not None:
        trace = read_trace(args.trace)
        catalog = read_catalog(args.catalog) if args.catalog else None
    else:
        # The default 10-item run is tiny; resolving it before the window opens
        # means the application always starts with a meaningful demonstration.
        active = service.resolve(config)
        trace = active.trace
        catalog = active.catalog

    from .adaptive import recommended_speed, scale_for_catalog
    initial_speed = args.speed if args.speed is not None else recommended_speed(scale_for_catalog(catalog))
    controller = ReplayController(
        trace,
        catalog=catalog,
        mode=ReplayMode(args.mode),
        speed=initial_speed,
    )

    if sys.platform == "win32":
        # Ensure Windows groups the taskbar button under the game identity rather
        # than under python.exe, so the OPTIMA icon is used consistently.
        try:
            import ctypes

            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "CICESE.OPTIMA.ImpossibleMove.1"
            )
        except (AttributeError, OSError):
            pass

    app = QGuiApplication(sys.argv if argv is None else [sys.argv[0], *argv])
    app.setApplicationName(tr("app_name", args.language))
    app.setApplicationDisplayName(tr("app_name", args.language))
    app.setOrganizationName("OPTIMA · CICESE")
    branding_dir = Path(__file__).with_name("qml") / "assets" / "branding"
    icon_path = branding_dir / ("optima_app.ico" if sys.platform == "win32" else "optima_mark.png")
    if not icon_path.exists():
        icon_path = branding_dir / "optima_mark.png"
    game_icon = QIcon(str(icon_path)) if icon_path.exists() else QIcon()
    if not game_icon.isNull():
        app.setWindowIcon(game_icon)

    engine = QQmlApplicationEngine()
    language_adapter = QtLanguageAdapter(args.language)
    theme_adapter = QtThemeAdapter(args.theme)
    replay_adapter = QtReplayAdapter(controller, language_adapter=language_adapter)
    comparison_adapter = QtComparisonAdapter(language_adapter=language_adapter)
    experiment_adapter = QtExperimentAdapter(
        service,
        replay_adapter,
        comparison_adapter,
        configuration=config,
        active=active,
        language_adapter=language_adapter,
    )
    engine.rootContext().setContextProperty("i18n", language_adapter)
    engine.rootContext().setContextProperty("theme", theme_adapter)
    engine.rootContext().setContextProperty("replay", replay_adapter)
    engine.rootContext().setContextProperty("comparison", comparison_adapter)
    engine.rootContext().setContextProperty("experiment", experiment_adapter)

    qml_path = Path(__file__).with_name("qml") / "Main.qml"
    engine.load(QUrl.fromLocalFile(str(qml_path.resolve())))
    if not engine.rootObjects():
        logger.error("QML engine did not create a root object | qml=%s", qml_path)
        return 1
    if not game_icon.isNull():
        root_window = engine.rootObjects()[0]
        if hasattr(root_window, "setIcon"):
            root_window.setIcon(game_icon)
    logger.info("GUI ready | qml=%s", qml_path)
    exit_code = app.exec()
    logger.info("Application exiting | code=%s", exit_code)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
