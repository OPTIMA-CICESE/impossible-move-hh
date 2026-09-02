from impossible_move.experiments import ExperimentConfiguration, ExperimentService

service = ExperimentService()
config = ExperimentConfiguration(item_count=50, truck_capacity=20, instance_index=2)

print("Candidates:")
for candidate in service.candidates(config).candidates:
    instance = candidate.instance
    print(
        f"  {candidate.label}: seed={candidate.seed} "
        f"volume={instance.total_size} lower_bound={instance.volume_lower_bound}"
    )

result = service.resolve(config)
print("\nResolved:")
print(f"  candidate={config.instance_label}")
print(f"  cache_hit={result.cache_hit}")
print(f"  bins_used={result.bins_used}")
print(f"  events={len(result.trace.events)}")
print(f"  HH sequences={result.statistics.as_view()['decisionSequencesDisplay']}")
print(f"  theoretical partitions={result.statistics.as_view()['theoreticalPartitionsDisplay']}")
