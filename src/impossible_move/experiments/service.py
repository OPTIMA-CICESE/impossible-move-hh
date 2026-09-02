from __future__ import annotations

from dataclasses import dataclass
import logging
from secrets import randbits
from time import perf_counter

from impossible_move.domain.models import BinPackingInstance
from impossible_move.engine import BinPackingEngine
from impossible_move.heuristics import BestFit, FirstFit, NextFit, WorstFit
from impossible_move.hyperheuristics import ExplainableRuleBasedHH, FixedHyperHeuristic, RandomHyperHeuristic
from impossible_move.ordering import OriginalOrder
from impossible_move.replay import ReplayCatalog
from impossible_move.trace.policy import TracePolicy
from impossible_move.trace.trace import RunTrace

from .cache import ExperimentCache
from .generator import MovingInstanceGenerator
from .models import ExperimentConfiguration, GeneratedInstanceSet
from .statistics import SearchSpaceEstimate
from .comparison import (
    POLICY_ADAPTIVE, POLICY_FIXED, POLICY_RANDOM, ResolvedComparison, ResolvedPolicyRun,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ResolvedExperiment:
    configuration: ExperimentConfiguration
    instance_seed: int
    instance: BinPackingInstance
    trace: RunTrace
    catalog: ReplayCatalog
    statistics: SearchSpaceEstimate
    cache_hit: bool
    cache_key: str

    @property
    def bins_used(self) -> int:
        finished = self.trace.events[-1] if self.trace.events else None
        return int(getattr(finished, "bins_used", 0))


class ExperimentService:
    """Generate, solve and cache outreach experiments independently of Qt."""

    def __init__(
        self,
        *,
        generator: MovingInstanceGenerator | None = None,
        cache: ExperimentCache | None = None,
        engine: BinPackingEngine | None = None,
    ) -> None:
        self.generator = generator or MovingInstanceGenerator()
        self.cache = cache or ExperimentCache()
        self.engine = engine or BinPackingEngine()

    def candidates(self, config: ExperimentConfiguration) -> GeneratedInstanceSet:
        return self.generator.generate_set(
            item_count=config.item_count,
            capacity=config.truck_capacity,
            batch_seed=config.batch_seed,
            profile=config.profile,
        )

    @staticmethod
    def new_batch_seed() -> int:
        return randbits(63)

    def potential_statistics(self, config: ExperimentConfiguration) -> SearchSpaceEstimate:
        return SearchSpaceEstimate.potential(config.item_count, heuristic_count=4)

    def resolve(self, config: ExperimentConfiguration) -> ResolvedExperiment:
        started = perf_counter()
        logger.info(
            "Resolve requested | profile=%s | items=%s | capacity=%s | instance=%s | batch_seed=%s",
            config.profile, config.item_count, config.truck_capacity, config.instance_label, config.batch_seed,
        )
        generated = self.candidates(config)
        candidate = generated.selected(config.instance_index)

        cached = self.cache.load(config, candidate.seed)
        if cached is not None:
            logger.info(
                "Cache hit | key=%s | seed=%s | events=%s | elapsed_ms=%.1f",
                cached.cache_key, candidate.seed, len(cached.trace.events), (perf_counter() - started) * 1000,
            )
            return ResolvedExperiment(
                configuration=config,
                instance_seed=candidate.seed,
                instance=cached.instance,
                trace=cached.trace,
                catalog=cached.catalog,
                statistics=cached.statistics,
                cache_hit=True,
                cache_key=cached.cache_key,
            )

        logger.info(
            "Solver starting | seed=%s | trace_policy=%s",
            candidate.seed, TracePolicy.for_item_count(config.item_count).value,
        )
        result = self.engine.solve(
            candidate.instance,
            ExplainableRuleBasedHH(),
            [FirstFit(), BestFit(), WorstFit(), NextFit()],
            OriginalOrder(),
            run_id=f"experiment-{candidate.instance.id}",
            trace_policy=TracePolicy.for_item_count(config.item_count),
        )
        catalog = ReplayCatalog.from_instance(candidate.instance)
        statistics = self.potential_statistics(config).with_trace(result.trace)
        key = self.cache.store(
            config=config,
            instance_seed=candidate.seed,
            instance=candidate.instance,
            trace=result.trace,
            catalog=catalog,
            statistics=statistics,
        )
        logger.info(
            "Solver finished | key=%s | bins=%s | lower_bound=%s | events=%s | placements=%s | elapsed_ms=%.1f",
            key, result.solution.bins_used, result.solution.lower_bound, len(result.trace.events),
            statistics.placement_evaluations, (perf_counter() - started) * 1000,
        )
        return ResolvedExperiment(
            configuration=config,
            instance_seed=candidate.seed,
            instance=candidate.instance,
            trace=result.trace,
            catalog=catalog,
            statistics=statistics,
            cache_hit=False,
            cache_key=key,
        )
    def resolve_comparison(
        self,
        config: ExperimentConfiguration,
        *,
        selected_policies: tuple[str, ...] = (POLICY_ADAPTIVE, POLICY_RANDOM, POLICY_FIXED),
        fixed_heuristic_id: str = "best_fit",
    ) -> ResolvedComparison:
        """Solve the same generated instance with multiple selection policies.

        All runs use the identical item order and low-level heuristic portfolio.
        The random policy is seeded deterministically from the generated instance,
        making outreach comparisons reproducible.
        """
        if not selected_policies:
            raise ValueError("at least one comparison policy is required")
        unknown = set(selected_policies) - {POLICY_ADAPTIVE, POLICY_RANDOM, POLICY_FIXED}
        if unknown:
            raise ValueError(f"unknown comparison policies: {sorted(unknown)!r}")
        if fixed_heuristic_id not in {"first_fit", "best_fit", "worst_fit", "next_fit"}:
            raise ValueError("fixed_heuristic_id must identify one low-level heuristic")

        generated = self.candidates(config)
        candidate = generated.selected(config.instance_index)
        heuristics = [FirstFit(), BestFit(), WorstFit(), NextFit()]
        policy_objects = {
            POLICY_ADAPTIVE: ExplainableRuleBasedHH(),
            POLICY_RANDOM: RandomHyperHeuristic(seed=candidate.seed ^ 0x5EED5EED),
            POLICY_FIXED: FixedHyperHeuristic(fixed_heuristic_id),
        }
        labels = {
            POLICY_ADAPTIVE: "Adaptive HH",
            POLICY_RANDOM: "Random HH",
            POLICY_FIXED: "Fixed strategy",
        }
        runs: dict[str, ResolvedPolicyRun] = {}
        trace_policy = TracePolicy.for_item_count(config.item_count)
        for policy_id in selected_policies:
            started = perf_counter()
            result = self.engine.solve(
                candidate.instance,
                policy_objects[policy_id],
                heuristics,
                OriginalOrder(),
                run_id=f"comparison-{policy_id}-{candidate.instance.id}",
                trace_policy=trace_policy,
            )
            catalog = ReplayCatalog.from_instance(candidate.instance)
            runs[policy_id] = ResolvedPolicyRun(
                policy_id=policy_id,
                label=labels[policy_id],
                trace=result.trace,
                catalog=catalog,
                bins_used=result.solution.bins_used,
                lower_bound=result.solution.lower_bound,
                utilization=result.solution.utilization,
                fixed_heuristic_id=fixed_heuristic_id if policy_id == POLICY_FIXED else None,
            )
            logger.info(
                "Comparison policy solved | policy=%s | bins=%s | gap=%s | elapsed_ms=%.1f",
                policy_id, result.solution.bins_used,
                result.solution.bins_used - result.solution.lower_bound,
                (perf_counter() - started) * 1000,
            )

        # Post-hoc fixed-policy benchmark. This does not alter any replayed policy:
        # it answers the stronger question "how did the adaptive HH compare with
        # the best single low-level heuristic for this exact instance?".
        fixed_benchmarks: dict[str, int] = {}
        best_fixed_id: str | None = None
        best_fixed_bins: int | None = None
        if POLICY_ADAPTIVE in selected_policies:
            fixed_ids = ("first_fit", "best_fit", "worst_fit", "next_fit")
            for heuristic_id in fixed_ids:
                if (
                    POLICY_FIXED in runs
                    and fixed_heuristic_id == heuristic_id
                ):
                    bins_used = runs[POLICY_FIXED].bins_used
                else:
                    benchmark = self.engine.solve(
                        candidate.instance,
                        FixedHyperHeuristic(heuristic_id),
                        heuristics,
                        OriginalOrder(),
                        run_id=f"benchmark-fixed-{heuristic_id}-{candidate.instance.id}",
                        trace_policy=TracePolicy.COMPACT,
                    )
                    bins_used = benchmark.solution.bins_used
                fixed_benchmarks[heuristic_id] = bins_used
            best_fixed_id = min(fixed_ids, key=lambda hid: (fixed_benchmarks[hid], fixed_ids.index(hid)))
            best_fixed_bins = fixed_benchmarks[best_fixed_id]
            logger.info(
                "Best fixed benchmark | heuristic=%s | bins=%s | adaptive_bins=%s | delta=%s",
                best_fixed_id, best_fixed_bins, runs[POLICY_ADAPTIVE].bins_used,
                runs[POLICY_ADAPTIVE].bins_used - best_fixed_bins,
            )

        return ResolvedComparison(
            instance=candidate.instance,
            instance_seed=candidate.seed,
            runs=runs,
            selected_policies=tuple(selected_policies),
            fixed_heuristic_id=fixed_heuristic_id,
            fixed_benchmarks=fixed_benchmarks,
            best_fixed_heuristic_id=best_fixed_id,
            best_fixed_bins=best_fixed_bins,
        )

