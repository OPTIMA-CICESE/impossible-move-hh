# La Mudanza Imposible

**La Mudanza Imposible** is an interactive scientific-outreach application for explaining **1D Bin Packing**, **heuristics**, and **hyper-heuristics** through the metaphor of a moving process.

Household objects are treated as items with a volume, while moving trucks are bins with limited capacity. The objective is to place all objects while using as few trucks as possible.

The project is developed within **OPTIMA / CICESE** as an educational and research-oriented demonstrator of adaptive heuristic selection.

---

## What does the application show?

The application lets the user compare different ways of making packing decisions over the **same instance and item order**:

- **Adaptive Hyper-Heuristic**
  - Observes the current packing state.
  - Scores several low-level heuristics.
  - Selects one heuristic at each decision.
  - Exposes the reasoning behind its choices.
- **Random Hyper-Heuristic**
  - Selects among the available low-level heuristics randomly.
  - Uses reproducible seeds.
- **Fixed Strategy**
  - Executes a single low-level heuristic throughout the full instance.

Available low-level heuristics:

- First Fit
- Best Fit
- Worst Fit
- Next Fit

The adaptive hyper-heuristic is **not assumed to be optimal**. The purpose of the demonstrator is to show when adaptive heuristic selection can help, when it ties with a fixed strategy, and when a fixed strategy can still perform better.

---

## Main features

- Interactive PySide6 / Qt Quick GUI.
- Spanish and English interfaces.
- Light and dark themes.
- Explainable adaptive hyper-heuristic.
- Synchronized replay of multiple methods.
- Visualization of:
  - current object,
  - truck occupancy,
  - heuristic selected,
  - heuristic scores,
  - active decision rules,
  - decision history,
  - cumulative trucks used.
- Comparison against the **best fixed strategy a posteriori**.
- Reproducible experiment generation.
- Multiple instance sizes: 10, 15, 20, 50, 100, 200, and 500 objects.
- Configurable truck capacity.
- Five reproducible instances per configuration.
- Persistent rotating logs.
- Scalable visualization modes for small and large experiments.

---

## Instance profiles

### Natural

Household-like size distributions. These instances often produce similar results among strong packing heuristics, which is expected.

### Contrastive

Amplifies the consequences of placement decisions while keeping the instances reproducible.

### Challenge

Reduces the presence of very small objects that can easily repair fragmented free space.

### Regime Switching

Introduces temporal changes in the size distribution during the same run.

This profile is particularly useful for illustrating why adaptive heuristic selection can matter: the heuristic that is useful in one phase of the move may not be the most useful in another.

---

## Best fixed strategy benchmark

When the adaptive hyper-heuristic is evaluated, the application can also execute all four fixed heuristics:

```text
First Fit
Best Fit
Worst Fit
Next Fit
```

The best fixed strategy is computed **a posteriori** and used only as a benchmark.

The adaptive advantage is reported as:

```text
adaptive trucks - best fixed trucks
```

Therefore:

- negative value -> adaptive HH used fewer trucks;
- zero -> tie;
- positive value -> the best fixed heuristic used fewer trucks.

This benchmark does **not** influence the decisions made during the replay.

---

## Project architecture

The application separates optimization logic from visualization.

```text
Domain
  |
  +-- Item
  +-- Bin
  +-- BinPackingInstance
  +-- BinPackingState
  +-- BinPackingSolution

Low-level heuristics
  |
  +-- First Fit
  +-- Best Fit
  +-- Worst Fit
  +-- Next Fit

Hyper-heuristics
  |
  +-- Adaptive rule-based HH
  +-- Random HH
  +-- Fixed strategy policy

Execution engine
  |
  +-- Solution
  +-- RunTrace

Replay layer
  |
  +-- ReplayController
  +-- Qt adapter

Frontend
  |
  +-- PySide6
  +-- Qt Quick / QML
```

The frontend replays precomputed traces instead of directly controlling the optimization process.

---

## Explainable adaptive hyper-heuristic

At each decision, the adaptive HH observes features of the current state, such as:

- current item size relative to truck capacity;
- number of feasible trucks;
- exact-fit opportunities;
- residual capacity after placement;
- dispersion of residual capacities;
- global utilization;
- feasibility and residual capacity of the most recent truck.

These observations activate interpretable rules that contribute to the scores of the available low-level heuristics.

The GUI exposes these contributions so the user can inspect **why** a heuristic was selected.

Conceptually:

```text
Current object + packing state
            |
            v
   Adaptive Hyper-Heuristic
            |
            v
 Selects a low-level heuristic
            |
            v
 FF / BF / WF / NF
            |
            v
     Placement decision
```

---

## Installation

### Requirements

- Python 3.10+
- PySide6
- A platform supported by Qt

Clone the repository:

```bash
git clone git@github.com:OPTIMA-CICESE/impossible-move-hh.git
cd impossible-move-hh
```

Install the project in editable mode with development and GUI dependencies:

```bash
python -m pip install -e ".[dev,gui]"
```

---

## Running the GUI

The simplest way to launch the complete demonstrator is:

```bash
python examples/demo_frontend.py
```

If the command-line entry point is installed, the GUI can also be launched with:

```bash
impossible-move-gui
```

Example:

```bash
impossible-move-gui --items 200 --capacity 10 --profile regime --instance C
```

Additional examples:

```bash
impossible-move-gui --profile natural
impossible-move-gui --profile contrastive
impossible-move-gui --profile challenge
impossible-move-gui --profile regime
```

Launch in English:

```bash
impossible-move-gui --language en
```

Launch in light mode:

```bash
impossible-move-gui --theme light
```

Enable detailed logging:

```bash
impossible-move-gui --log-level DEBUG
```

---

## Logging

On Windows, logs are stored by default under:

```text
%LOCALAPPDATA%\ImpossibleMove\logs\impossible_move.log
```

The logging system records application startup/shutdown, experiment configuration, generation, cache behavior, solver summaries, relevant replay events, Python exceptions, and Qt/QML warnings/errors.

Logs are rotated automatically.

---

## Reproducibility

Experiments are generated deterministically from their configuration.

Relevant parameters include:

- number of objects;
- truck capacity;
- corpus profile;
- instance identifier;
- algorithm configuration;
- random seed where applicable.

The same configuration can therefore be replayed and compared consistently across methods.

---

## Potential decision space

With four available low-level heuristics and a sequence of `n` decisions, the hyper-heuristic has a potential decision-sequence space of:

```text
4^n
```

This value represents the number of possible sequences of heuristic selections.

The adaptive HH does **not** exhaustively explore all these sequences. It follows a single path by making one selection at each decision.

The application also uses the Bell number as an educational reference for the theoretical number of ways in which `n` objects may be partitioned before capacity constraints are considered.

---

## Lower bound

The demonstrator reports the standard volume-based lower bound:

```text
LB = ceil(total object volume / truck capacity)
```

This value is a lower bound only. It is **not necessarily the optimal number of trucks**.

---

## Development

Run the test suite with:

```bash
pytest
```

Compile Python sources:

```bash
python -m compileall .
```

Build the package:

```bash
python -m build
```

Generated artifacts, caches, logs, virtual environments, and local experiment outputs should not be committed to the repository.

---

## Educational purpose

The project is designed to help explain several ideas:

1. Optimization problems may admit many valid solutions with different quality.
2. A heuristic provides a strategy for constructing a solution efficiently.
3. Different heuristics can behave differently on the same problem.
4. A hyper-heuristic operates at a higher level by selecting or managing heuristics.
5. An adaptive method is useful when the best strategy is not known in advance or when the structure of the problem changes during execution.
6. Adaptation does not guarantee superiority on every instance.

---

## License

This project is released under the **BSD 3-Clause License**.

See [`LICENSE`](LICENSE) for the complete license text.

---

## Project

**OPTIMA Research Group**  
**CICESE - Centro de Investigacion Cientifica y de Educacion Superior de Ensenada**

Research Group Head: **Guillermo Falcon, PhD**

---

## Citation

If you use this software in academic work, please cite the corresponding publication or project reference once available.

A formal citation entry will be added to this repository in a future release.
