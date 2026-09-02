from __future__ import annotations

try:
    from PySide6.QtCore import QObject, Property, Signal, Slot
except ModuleNotFoundError as exc:  # pragma: no cover
    raise RuntimeError(
        "PySide6 is required for the GUI. Install with: pip install -e '.[gui]'"
    ) from exc

from .i18n import DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES, normalize_language, strings


class QtLanguageAdapter(QObject):
    """Small Qt-facing localization service.

    Translation stays entirely in the presentation layer.  Changing language
    emits a single property notification; the replay and experiment adapters
    refresh their localized view models without touching solver state.
    """

    languageChanged = Signal()

    def __init__(self, language: str = DEFAULT_LANGUAGE, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._language = normalize_language(language)
        self._strings = strings(self._language)

    @Property(str, notify=languageChanged)
    def language(self) -> str:
        return self._language

    @Property("QVariantMap", notify=languageChanged)
    def strings(self) -> dict[str, str]:
        return self._strings

    @Property("QVariantList", constant=True)
    def supportedLanguages(self) -> list[str]:
        return list(SUPPORTED_LANGUAGES)

    @Slot(str)
    def setLanguage(self, language: str) -> None:
        normalized = normalize_language(language)
        if normalized == self._language:
            return
        self._language = normalized
        self._strings = strings(normalized)
        self.languageChanged.emit()
