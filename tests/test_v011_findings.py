from pathlib import Path

from impossible_move.experiments import (
    ExperimentCache,
    ExperimentConfiguration,
    ExperimentService,
    MovingInstanceGenerator,
)
from impossible_move.frontend.comparison import ComparisonReplayController, comparison_view, move_explorer_view

ROOT = Path(__file__).parents[1]
QML = ROOT / "src" / "impossible_move" / "frontend" / "qml"


def test_v011_profiles_are_reproducible_and_distinct():
    gen = MovingInstanceGenerator()
    rows = {}
    for profile in ("natural", "contrastive", "challenge"):
        a = gen.generate_set(item_count=50, capacity=10, batch_seed=20260831, profile=profile)
        b = gen.generate_set(item_count=50, capacity=10, batch_seed=20260831, profile=profile)
        assert a == b
        rows[profile] = tuple(tuple(i.size for i in c.instance.items) for c in a.candidates)
    assert len(set(rows.values())) == 3


def test_v011_challenge_has_no_tiny_filler_at_capacity_10():
    gen = MovingInstanceGenerator()
    generated = gen.generate_set(item_count=200, capacity=10, batch_seed=20260831, profile="challenge")
    assert all(item.size >= 2 for c in generated.candidates for item in c.instance.items)


def test_v011_contrastive_and_challenge_show_policy_separation_without_forced_adaptive_winner(tmp_path):
    service = ExperimentService(cache=ExperimentCache(tmp_path))
    contrastive = []
    for idx in range(5):
        cfg = ExperimentConfiguration(item_count=50, truck_capacity=10, instance_index=idx, batch_seed=20260831, profile="contrastive")
        r = service.resolve_comparison(cfg, selected_policies=("adaptive", "random", "fixed"), fixed_heuristic_id="best_fit")
        contrastive.append(tuple(r.runs[p].bins_used for p in ("adaptive", "random", "fixed")))
    assert any(a != r for a, r, _ in contrastive)
    assert any(a < f for a, _, f in contrastive)
    assert any(a > f for a, _, f in contrastive)


def test_v011_profile_changes_cache_key(tmp_path):
    service = ExperimentService(cache=ExperimentCache(tmp_path))
    base = ExperimentConfiguration(item_count=10, truck_capacity=10, batch_seed=99)
    natural = service.resolve(base.with_profile("natural"))
    contrastive = service.resolve(base.with_profile("contrastive"))
    assert natural.cache_key != contrastive.cache_key
    assert natural.instance_seed != contrastive.instance_seed


def test_v011_profile_selector_and_help_are_wired_in_qml():
    qml = (QML / "components" / "ExperimentConfigPopup.qml").read_text(encoding="utf-8")
    assert "experiment.view.profileOptions" in qml
    assert "experiment.setProfile" in qml
    assert "corpus_profile_help_title" in qml
    assert "profile_contrastive_body" in qml


def test_v011_comparison_move_contents_expose_items_and_policy_placements(tmp_path):
    service = ExperimentService(cache=ExperimentCache(tmp_path))
    cfg = ExperimentConfiguration(item_count=10, truck_capacity=10, instance_index=0, batch_seed=123, profile="contrastive")
    resolved = service.resolve_comparison(cfg, selected_policies=("adaptive", "random", "fixed"), fixed_heuristic_id="best_fit")
    controller = ComparisonReplayController(resolved)
    controller.advance_decision()
    controller.advance_decision()
    view = comparison_view(controller, "en")
    explorer = move_explorer_view(controller, "en")
    assert "moveItems" not in view  # detailed rows are now lazy
    assert len(explorer["items"]) == 10
    assert sum(g["total"] for g in explorer["groups"]) == 10
    assert explorer["items"][0]["processed"] is True
    assert len(explorer["items"][0]["placements"]) == 3
    assert all(p["binId"] is not None for p in explorer["items"][0]["placements"])
    assert explorer["items"][2]["current"] is True


def test_v011_current_item_card_opens_move_explorer():
    comparison = (QML / "components" / "ComparisonPanel.qml").read_text(encoding="utf-8")
    explorer = (QML / "components" / "MoveExplorerPopup.qml").read_text(encoding="utf-8")
    assert "moveExplorer.open()" in comparison
    assert "i18n.strings.view_move" in comparison
    assert "explorerView.items" in explorer
    assert "explorerView.groups" in explorer
    assert "comparison.prepareMoveExplorer()" in comparison
