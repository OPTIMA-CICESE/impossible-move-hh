from __future__ import annotations

import re
from pathlib import Path


QML_ROOT = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "impossible_move"
    / "frontend"
    / "qml"
)

# In a QML object body, child object declarations are declarative members and
# must not be separated from the following child declaration with a JS-style
# semicolon (e.g. `Text { ... }; Text { ... }`). Qt's parser reports this as
# "Unexpected token `;'".
INVALID_CHILD_SEPARATOR = re.compile(
    r"}\s*;\s*[A-Z][A-Za-z0-9_]*\s*{"
)


def test_qml_has_no_semicolon_between_child_object_declarations() -> None:
    failures: list[str] = []
    for path in sorted(QML_ROOT.rglob("*.qml")):
        text = path.read_text(encoding="utf-8")
        for match in INVALID_CHILD_SEPARATOR.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            failures.append(f"{path.relative_to(QML_ROOT)}:{line}: {match.group(0)!r}")

    assert not failures, "Invalid QML child-object separators:\n" + "\n".join(failures)


def test_qml_tooltip_usage_imports_qtquick_controls() -> None:
    failures: list[str] = []
    for path in sorted(QML_ROOT.rglob("*.qml")):
        text = path.read_text(encoding="utf-8")
        if "ToolTip." in text and "import QtQuick.Controls" not in text:
            failures.append(str(path.relative_to(QML_ROOT)))

    assert not failures, (
        "QML files use the ToolTip attached object without importing QtQuick.Controls:\n"
        + "\n".join(failures)
    )
