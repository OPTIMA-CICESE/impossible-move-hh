from __future__ import annotations

try:
    from PySide6.QtCore import QObject, Property, Signal, Slot
except ModuleNotFoundError as exc:  # pragma: no cover
    raise RuntimeError("PySide6 is required for the GUI") from exc

SUPPORTED_THEMES = ("dark", "light")

_DARK = {
    "window": "#08111D",
    "titleBar": "#0A1624",
    "panel": "#0D1928",
    "panelRaised": "#111F31",
    "card": "#122236",
    "cardDark": "#0B1624",
    "cardSoft": "#16273A",
    "border": "#29415D",
    "borderStrong": "#35506F",
    "text": "#F4F7FB",
    "textSecondary": "#B8C8DB",
    "textMuted": "#8FA6C1",
    "textSubtle": "#7890AC",
    "accent": "#F6C453",
    "accentHover": "#FFD56E",
    "accentPressed": "#E2A931",
    "accentText": "#0C1726",
    "success": "#8BE0C6",
    "danger": "#A4424F",
    "button": "#18263A",
    "buttonHover": "#21334A",
    "buttonPressed": "#22344D",
    "track": "#101B2A",
    "bar": "#5F86B5",
    "selected": "#203A54",
    "overlay": "#07101BE6",
}

_LIGHT = {
    "window": "#EEF3F8",
    "titleBar": "#E4EBF3",
    "panel": "#F7FAFD",
    "panelRaised": "#FFFFFF",
    "card": "#EDF3F9",
    "cardDark": "#E2EAF3",
    "cardSoft": "#E8EFF7",
    "border": "#B7C7D8",
    "borderStrong": "#8EA6BF",
    "text": "#14263A",
    "textSecondary": "#314C68",
    "textMuted": "#536F8C",
    "textSubtle": "#617C98",
    "accent": "#B9810B",
    "accentHover": "#D39713",
    "accentPressed": "#9B6B07",
    "accentText": "#FFFFFF",
    "success": "#147C67",
    "danger": "#B43D4D",
    "button": "#E5EDF6",
    "buttonHover": "#D7E3EF",
    "buttonPressed": "#C9D8E7",
    "track": "#D9E4EF",
    "bar": "#4E739A",
    "selected": "#DCEAF7",
    "overlay": "#DCE5EECC",
}


class QtThemeAdapter(QObject):
    themeChanged = Signal()

    def __init__(self, theme: str = "dark", parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._theme = theme if theme in SUPPORTED_THEMES else "dark"

    @Property(str, notify=themeChanged)
    def mode(self) -> str:
        return self._theme

    @Property("QVariantMap", notify=themeChanged)
    def colors(self) -> dict[str, str]:
        return dict(_LIGHT if self._theme == "light" else _DARK)

    @Property("QVariantList", constant=True)
    def supportedThemes(self) -> list[str]:
        return list(SUPPORTED_THEMES)

    @Slot(str)
    def setTheme(self, theme: str) -> None:
        value = str(theme).lower()
        if value not in SUPPORTED_THEMES or value == self._theme:
            return
        self._theme = value
        self.themeChanged.emit()
