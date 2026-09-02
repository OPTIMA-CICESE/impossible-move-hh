from __future__ import annotations

from impossible_move.experiments import ExperimentConfiguration, ExperimentService


def main() -> None:
    service = ExperimentService()
    print("Corpus audit · capacity 10 · batch seed 20260831")
    print("cells = Adaptive / Random / selected Best Fit / best fixed in hindsight")
    for count in (50, 100, 200):
        print(f"\n{count} objects")
        for profile in ("natural", "contrastive", "challenge", "regime"):
            cells = []
            for index in range(5):
                cfg = ExperimentConfiguration(
                    item_count=count,
                    truck_capacity=10,
                    instance_index=index,
                    batch_seed=20260831,
                    profile=profile,
                )
                resolved = service.resolve_comparison(
                    cfg,
                    selected_policies=("adaptive", "random", "fixed"),
                    fixed_heuristic_id="best_fit",
                )
                cells.append(
                    "/".join(
                        (
                            str(resolved.runs["adaptive"].bins_used),
                            str(resolved.runs["random"].bins_used),
                            str(resolved.runs["fixed"].bins_used),
                            f"{resolved.best_fixed_bins}:{resolved.best_fixed_heuristic_id}",
                        )
                    )
                )
            print(f"  {profile:11s}: " + "  ".join(cells))


if __name__ == "__main__":
    main()
