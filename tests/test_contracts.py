import pytest

from impossible_move.explainability import DecisionReason
from impossible_move.optimization.contracts import (
    HeuristicSelection,
    PlacementDecision,
    PlacementEvaluation,
)


def test_placement_decision_existing_bin() -> None:
    decision = PlacementDecision(bin_id=2)
    assert decision.bin_id == 2
    assert not decision.create_new_bin


def test_placement_decision_new_bin() -> None:
    decision = PlacementDecision(create_new_bin=True)
    assert decision.bin_id is None


def test_placement_decision_requires_exactly_one_target() -> None:
    with pytest.raises(ValueError):
        PlacementDecision()
    with pytest.raises(ValueError):
        PlacementDecision(bin_id=1, create_new_bin=True)


def test_placement_evaluation_consistency() -> None:
    PlacementEvaluation(
        bin_id=0,
        feasible=True,
        remaining_before=5,
        remaining_after=2,
        score=2.0,
    )
    with pytest.raises(ValueError):
        PlacementEvaluation(
            bin_id=0,
            feasible=False,
            remaining_before=1,
            remaining_after=0,
        )


def test_heuristic_scores_are_defensively_copied() -> None:
    scores = {"ff": 0.5, "bf": 0.5}
    selection = HeuristicSelection("ff", scores)
    scores["ff"] = 99.0
    assert selection.scores is not None
    assert selection.scores["ff"] == 0.5
    with pytest.raises(TypeError):
        selection.scores["ff"] = 1.0  # type: ignore[index]


def test_heuristic_selection_reasons_are_typed_and_immutable() -> None:
    reason = DecisionReason("exact_fit", "bf", 4.0)
    selection = HeuristicSelection("bf", {"bf": 5.0}, (reason,))
    assert selection.reasons == (reason,)
    with pytest.raises(TypeError):
        HeuristicSelection("bf", {"bf": 1.0}, ({"rule_id": "x"},))  # type: ignore[arg-type]
