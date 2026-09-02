from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
import logging

try:
    from PySide6.QtCore import QObject, Property, QTimer, Signal, Slot
except ModuleNotFoundError as exc:  # pragma: no cover - only without GUI extra
    raise RuntimeError(
        "PySide6 is required for the GUI. Install with: pip install -e '.[gui]'"
    ) from exc

from impossible_move.trace.policy import TracePolicy
from .adaptive import PresentationScale
from .i18n import DEFAULT_LANGUAGE, tr

logger = logging.getLogger(__name__)

from impossible_move.experiments import (
    INSTANCE_LABELS,
    SUPPORTED_ITEM_COUNTS,
    SUPPORTED_PROFILES,
    ExperimentConfiguration,
    ExperimentService,
    ResolvedExperiment,
)


class QtExperimentAdapter(QObject):
    """Qt-facing experiment configurator with asynchronous solve + cache lookup."""

    viewChanged = Signal()
    runReady = Signal()
    resolutionFailed = Signal(str)

    CAPACITY_PRESETS = (10, 15, 20, 25, 50)

    def __init__(
        self,
        service: ExperimentService,
        replay_adapter,
        comparison_adapter=None,
        *,
        configuration: ExperimentConfiguration | None = None,
        active: ResolvedExperiment | None = None,
        language_adapter=None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._service = service
        self._language_adapter = language_adapter
        if language_adapter is not None:
            language_adapter.languageChanged.connect(self._refresh)
        self._replay_adapter = replay_adapter
        self._comparison_adapter = comparison_adapter
        self._selected_policies = ["adaptive"]
        self._fixed_heuristic_id = "best_fit"
        self._comparison_active = None
        self._config = configuration or ExperimentConfiguration()
        self._active = active
        self._candidate_set = self._service.candidates(self._config)
        self._resolving = False
        self._error = ""
        self._future: Future | None = None
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="impossible-move")
        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(40)
        self._poll_timer.timeout.connect(self._poll_future)
        self._view: dict = {}
        self._refresh()

    @property
    def _language(self) -> str:
        return self._language_adapter.language if self._language_adapter is not None else DEFAULT_LANGUAGE

    def _candidate_rows(self) -> list[dict]:
        rows: list[dict] = []
        for candidate in self._candidate_set.candidates:
            instance = candidate.instance
            rows.append(
                {
                    "index": candidate.index,
                    "label": candidate.label,
                    "seed": str(candidate.seed),
                    "totalSize": instance.total_size,
                    "lowerBound": instance.volume_lower_bound,
                    "selected": candidate.index == self._config.instance_index,
                }
            )
        return rows

    def _active_view(self) -> dict:
        if self._active is None and self._comparison_active is None:
            return {}
        cfg = self._active.configuration if self._active is not None else self._config
        stats = self._active.statistics.as_view() if self._active is not None else self._service.potential_statistics(cfg).as_view()
        return {
            "itemCount": cfg.item_count,
            "capacity": cfg.truck_capacity,
            "instanceIndex": cfg.instance_index,
            "instanceLabel": cfg.instance_label,
            "profile": cfg.profile,
            "batchSeed": str(cfg.batch_seed),
            "instanceSeed": str(self._active.instance_seed if self._active is not None else self._comparison_active.instance_seed),
            "cacheHit": self._active.cache_hit if self._active is not None else False,
            "cacheKey": self._active.cache_key if self._active is not None else "comparison",
            "statistics": stats,
            "label": tr(
                "active_move_label",
                self._language,
                count=cfg.item_count,
                capacity=cfg.truck_capacity,
                profile=tr(f"profile_{cfg.profile}", self._language),
                instance=cfg.instance_label,
            ),
            "profileLabel": tr(f"profile_{cfg.profile}", self._language),
            "tracePolicy": TracePolicy.for_item_count(cfg.item_count).value,
            "presentationScale": PresentationScale.for_item_count(cfg.item_count).value,
        }

    def _refresh(self) -> None:
        potential = self._service.potential_statistics(self._config).as_view()
        selected = self._candidate_set.selected(self._config.instance_index)
        self._view = {
            "supportedItemCounts": list(SUPPORTED_ITEM_COUNTS),
            "supportedProfiles": list(SUPPORTED_PROFILES),
            "profile": self._config.profile,
            "profileOptions": [
                {"id": "natural", "label": tr("profile_natural", self._language), "description": tr("profile_natural_body", self._language), "selected": self._config.profile == "natural"},
                {"id": "contrastive", "label": tr("profile_contrastive", self._language), "description": tr("profile_contrastive_body", self._language), "selected": self._config.profile == "contrastive"},
                {"id": "challenge", "label": tr("profile_challenge", self._language), "description": tr("profile_challenge_body", self._language), "selected": self._config.profile == "challenge"},
                {"id": "regime", "label": tr("profile_regime", self._language), "description": tr("profile_regime_body", self._language), "selected": self._config.profile == "regime"},
            ],
            "capacityPresets": list(self.CAPACITY_PRESETS),
            "instanceLabels": list(INSTANCE_LABELS),
            "itemCount": self._config.item_count,
            "capacity": self._config.truck_capacity,
            "instanceIndex": self._config.instance_index,
            "instanceLabel": self._config.instance_label,
            "batchSeed": str(self._config.batch_seed),
            "selectedSeed": str(selected.seed),
            "candidates": self._candidate_rows(),
            "selectedCandidate": {
                "label": selected.label,
                "seed": str(selected.seed),
                "totalSize": selected.instance.total_size,
                "lowerBound": selected.instance.volume_lower_bound,
            },
            "potentialStatistics": potential,
            "tracePolicy": TracePolicy.for_item_count(self._config.item_count).value,
            "presentationScale": PresentationScale.for_item_count(self._config.item_count).value,
            "active": self._active_view(),
            "resolving": self._resolving,
            "error": self._error,
            "selectedPolicies": list(self._selected_policies),
            "policyOptions": [
                {"id": "adaptive", "label": tr("comparison_adaptive", self._language), "selected": "adaptive" in self._selected_policies},
                {"id": "random", "label": tr("comparison_random", self._language), "selected": "random" in self._selected_policies},
                {"id": "fixed", "label": tr("comparison_fixed", self._language), "selected": "fixed" in self._selected_policies},
            ],
            "fixedHeuristicId": self._fixed_heuristic_id,
            "fixedHeuristicOptions": [
                {"id": "first_fit", "label": "First Fit"}, {"id": "best_fit", "label": "Best Fit"},
                {"id": "worst_fit", "label": "Worst Fit"}, {"id": "next_fit", "label": "Next Fit"},
            ],
        }
        self.viewChanged.emit()

    @Property("QVariantMap", notify=viewChanged)
    def view(self) -> dict:
        return self._view

    @Property(bool, notify=viewChanged)
    def resolving(self) -> bool:
        return self._resolving


    @Slot(str)
    def setProfile(self, profile: str) -> None:
        if self._resolving:
            return
        try:
            self._config = self._config.with_profile(str(profile))
        except ValueError as exc:
            self._error = str(exc)
            self._refresh()
            return
        logger.info("Configuration changed | profile=%s", self._config.profile)
        self._candidate_set = self._service.candidates(self._config)
        self._error = ""
        self._refresh()

    @Slot(int)
    def setItemCount(self, item_count: int) -> None:
        if self._resolving:
            return
        self._config = self._config.with_item_count(int(item_count))
        logger.info("Configuration changed | items=%s", self._config.item_count)
        self._candidate_set = self._service.candidates(self._config)
        self._error = ""
        self._refresh()

    @Slot(int)
    def setCapacity(self, capacity: int) -> None:
        if self._resolving:
            return
        capacity = int(capacity)
        if capacity <= 0:
            self._error = tr("positive_capacity_error", self._language)
            self._refresh()
            return
        self._config = self._config.with_capacity(capacity)
        logger.info("Configuration changed | capacity=%s", self._config.truck_capacity)
        self._candidate_set = self._service.candidates(self._config)
        self._error = ""
        self._refresh()

    @Slot(int)
    def selectInstance(self, index: int) -> None:
        if self._resolving:
            return
        try:
            self._config = self._config.with_instance_index(int(index))
            logger.info("Configuration changed | instance=%s", self._config.instance_label)
        except ValueError as exc:
            self._error = str(exc)
        else:
            self._error = ""
        self._refresh()

    @Slot()
    def regenerate(self) -> None:
        if self._resolving:
            return
        self._config = self._config.with_batch_seed(self._service.new_batch_seed())
        logger.info("Generated new candidate batch | batch_seed=%s", self._config.batch_seed)
        self._candidate_set = self._service.candidates(self._config)
        self._error = ""
        self._refresh()

    @Slot(str, bool)
    def setPolicySelected(self, policy_id: str, selected: bool) -> None:
        if self._resolving or policy_id not in {"adaptive", "random", "fixed"}:
            return
        policies = list(self._selected_policies)
        if selected and policy_id not in policies:
            policies.append(policy_id)
        elif not selected and policy_id in policies:
            policies.remove(policy_id)
        if not policies:
            self._error = tr("comparison_select_one", self._language)
            self._refresh()
            return
        order = {"adaptive": 0, "random": 1, "fixed": 2}
        self._selected_policies = sorted(policies, key=order.get)
        self._error = ""
        self._refresh()

    @Slot(str)
    def setFixedHeuristic(self, heuristic_id: str) -> None:
        if heuristic_id in {"first_fit", "best_fit", "worst_fit", "next_fit"}:
            self._fixed_heuristic_id = heuristic_id
            self._refresh()

    @Slot()
    def resolveSelected(self) -> None:
        if self._resolving:
            return
        self._resolving = True
        self._error = ""
        config = self._config
        logger.info(
            "Asynchronous resolve submitted | profile=%s | items=%s | capacity=%s | instance=%s",
            config.profile, config.item_count, config.truck_capacity, config.instance_label,
        )
        if self._selected_policies == ["adaptive"]:
            self._future = self._executor.submit(self._service.resolve, config)
        else:
            self._future = self._executor.submit(
                self._service.resolve_comparison,
                config,
                selected_policies=tuple(self._selected_policies),
                fixed_heuristic_id=self._fixed_heuristic_id,
            )
        self._poll_timer.start()
        self._refresh()

    @Slot()
    def _poll_future(self) -> None:
        future = self._future
        if future is None or not future.done():
            return
        self._poll_timer.stop()
        self._future = None
        try:
            resolved = future.result()
        except Exception as exc:  # pragma: no cover - backend cases tested separately
            logger.exception("Asynchronous resolve failed")
            self._resolving = False
            self._error = f"{tr('solve_error', self._language)}: {exc}"
            self._refresh()
            self.resolutionFailed.emit(self._error)
            return
        self._resolving = False
        self._error = ""
        if hasattr(resolved, "runs"):
            logger.info("Comparison resolve ready | policies=%s", resolved.selected_policies)
            self._comparison_active = resolved
            self._active = None
            if self._comparison_adapter is not None:
                self._comparison_adapter.load(resolved)
        else:
            logger.info(
                "Asynchronous resolve ready | cache_hit=%s | key=%s | bins=%s",
                resolved.cache_hit, resolved.cache_key, resolved.bins_used,
            )
            self._active = resolved
            self._comparison_active = None
            if self._comparison_adapter is not None:
                self._comparison_adapter.clear()
            self._replay_adapter.load_run(resolved.trace, resolved.catalog)
        self._refresh()
        self.runReady.emit()
