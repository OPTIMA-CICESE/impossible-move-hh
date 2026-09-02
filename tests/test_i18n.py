from impossible_move.frontend.i18n import localized_item_name, normalize_language, strings, tr


def test_v090_language_catalogs_cover_same_keys():
    assert set(strings("es")) == set(strings("en"))


def test_v090_language_normalization_and_fallback():
    assert normalize_language("EN-US") == "en"
    assert normalize_language("es-MX") == "es"
    assert normalize_language("fr") == "es"
    assert tr("app_name", "en") == "The Impossible Move"
    assert tr("app_name", "es") == "La mudanza imposible"


def test_v090_generated_item_names_localize_without_touching_semantic_ids():
    assert localized_item_name("sofa", "Sofá 3", "en") == "Sofa 3"
    assert localized_item_name("sofa", "Sofá 3", "es") == "Sofá 3"
    assert localized_item_name("clothes_box", "Caja de ropa", "en") == "Clothes box"


def test_v090_all_qml_i18n_references_exist_in_both_catalogs():
    import re
    from pathlib import Path

    qml_root = Path(__file__).parents[1] / "src" / "impossible_move" / "frontend" / "qml"
    refs = set()
    for path in qml_root.rglob("*.qml"):
        refs.update(re.findall(r"i18n\\.strings\\.([A-Za-z0-9_]+)", path.read_text(encoding="utf-8")))
    assert refs <= set(strings("es"))
    assert refs <= set(strings("en"))
