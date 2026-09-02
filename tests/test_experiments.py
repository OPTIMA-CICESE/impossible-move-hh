from __future__ import annotations

from pathlib import Path

import pytest

from impossible_move.experiments import (
    ExperimentCache,
    ExperimentConfiguration,
    ExperimentService,
    MovingInstanceGenerator,
    SearchSpaceEstimate,
    bell_number,
)


def test_configuration_accepts_only_supported_public_item_counts():
    for count in (10, 15, 20, 50, 100, 200, 500):
        assert ExperimentConfiguration(item_count=count).item_count == count
    with pytest.raises(ValueError):
        ExperimentConfiguration(item_count=11)
    with pytest.raises(ValueError):
        ExperimentConfiguration(truck_capacity=0)
    with pytest.raises(ValueError):
        ExperimentConfiguration(instance_index=5)


def test_generator_builds_five_reproducible_distinct_candidates():
    generator = MovingInstanceGenerator()
    first = generator.generate_set(item_count=20, capacity=17, batch_seed=12345)
    second = generator.generate_set(item_count=20, capacity=17, batch_seed=12345)
    assert [candidate.seed for candidate in first.candidates] == [candidate.seed for candidate in second.candidates]
    assert len({candidate.seed for candidate in first.candidates}) == 5
    assert [candidate.instance for candidate in first.candidates] == [candidate.instance for candidate in second.candidates]
    assert [candidate.label for candidate in first.candidates] == list("ABCDE")
    for candidate in first.candidates:
        assert len(candidate.instance.items) == 20
        assert candidate.instance.capacity == 17
        assert all(1 <= item.size <= 17 for item in candidate.instance.items)


def test_capacity_changes_generated_sizes_but_preserves_relative_domain_validity():
    generator = MovingInstanceGenerator()
    small = generator.generate_set(item_count=10, capacity=10, batch_seed=99).candidates[0].instance
    large = generator.generate_set(item_count=10, capacity=50, batch_seed=99).candidates[0].instance
    assert all(item.size <= 10 for item in small.items)
    assert all(item.size <= 50 for item in large.items)
    assert small.total_size != large.total_size


def test_search_space_statistics_use_hh_sequences_and_bell_partitions():
    stats = SearchSpaceEstimate.potential(10, heuristic_count=4)
    assert stats.decision_sequences == 4**10
    assert stats.theoretical_partitions == 115975
    assert bell_number(0) == 1
    assert bell_number(5) == 52
    view = stats.as_view()
    assert "10^" in view["decisionSequencesDisplay"]
    assert view["theoreticalPartitionsDisplay"] == "115 975"


def test_service_solves_and_then_hits_filesystem_cache(tmp_path: Path):
    service = ExperimentService(cache=ExperimentCache(tmp_path))
    config = ExperimentConfiguration(item_count=15, truck_capacity=12, instance_index=2, batch_seed=777)
    first = service.resolve(config)
    assert first.cache_hit is False
    assert first.statistics.decisions_observed == 15
    assert first.statistics.heuristic_options_scored == 60
    assert first.statistics.heuristic_options_not_selected == 45
    assert first.statistics.placement_evaluations >= 0
    assert (tmp_path / first.cache_key / "trace.json").is_file()
    assert (tmp_path / first.cache_key / "catalog.json").is_file()
    assert (tmp_path / first.cache_key / "instance.json").is_file()

    second = service.resolve(config)
    assert second.cache_hit is True
    assert second.cache_key == first.cache_key
    assert second.trace == first.trace
    assert second.catalog.instance_id == first.catalog.instance_id
    assert second.instance == first.instance
    assert second.statistics == first.statistics


def test_different_capacity_or_instance_uses_different_cache_key(tmp_path: Path):
    service = ExperimentService(cache=ExperimentCache(tmp_path))
    base = ExperimentConfiguration(item_count=10, truck_capacity=10, instance_index=0, batch_seed=12)
    a = service.resolve(base)
    b = service.resolve(base.with_capacity(11))
    c = service.resolve(base.with_instance_index(1))
    assert len({a.cache_key, b.cache_key, c.cache_key}) == 3


def test_500_item_candidate_generation_and_space_estimate_are_supported():
    service = ExperimentService(cache=ExperimentCache(Path("/tmp/impossible-move-test-unused")))
    config = ExperimentConfiguration(item_count=500, truck_capacity=20, batch_seed=101)
    generated = service.candidates(config)
    assert all(len(candidate.instance.items) == 500 for candidate in generated.candidates)
    stats = service.potential_statistics(config)
    assert len(str(stats.decision_sequences)) == 302
    assert len(str(stats.theoretical_partitions)) == 844
