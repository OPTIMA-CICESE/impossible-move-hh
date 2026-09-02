# Impossible Move / La mudanza imposible

**La mudanza imposible** is an OPTIMA/CICESE science-outreach application for explaining one-dimensional Bin Packing, combinatorial explosion, heuristics and explainable hyper-heuristics.

## Development version 0.9.1 · Public game version 1.0.0

V0.9.1 refines the second visual-review cycle while keeping the mathematical backend and trace-driven replay untouched. This release focuses on institutional precision, responsive window behavior, taskbar identity, hyper-heuristic pedagogy and lower-bound explainability.

### Main V0.9.1 changes

- About information now identifies Dr. Guillermo Falcón as **Responsable del grupo OPTIMA** in Spanish and **Research Group Head** in English, with localized degree styling (`Dr.` / `, PhD`);
- the duplicate About icon was removed from the title bar; About remains in the institutional footer;
- root and three-column layout constraints were made more responsive to the screen's available desktop size;
- truck cards reserve explicit space for the themed scrollbar so their rounded right edge is never covered;
- a multi-resolution OPTIMA `.ico` plus a Windows AppUserModelID are used so the taskbar/window identity no longer falls back to the Python icon;
- the HH panel now explicitly shows the **Hyper-Heuristic (HH)** as the decision layer (`State → HH → Strategy`) before opening its rule-based decision process;
- the lower-bound metric now has contextual help that explains the volume bound and evaluates the actual instance formula `ceil(total volume / truck capacity)`;
- the presenter now exposes `totalItemSize` so the lower-bound explanation remains exact both during replay and at the final state.

### Scale-dependent presentation

- **10–20 objects:** individual pending objects and full truck cards.
- **50–100 objects:** objects grouped by type, focused truck and compact truck grid.
- **200–500 objects:** progress/category dashboard, focused truck and global occupancy map.

Trace density remains adaptive (`FULL`, `STANDARD`, `COMPACT`) while preserving the HH trajectory and aggregate placement-evaluation counts.

## Install

Core + tests:

```bash
python -m pip install -e '.[dev]'
```

GUI:

```bash
python -m pip install -e '.[dev,gui]'
```

## Run

```bash
python examples/demo_frontend.py
```

or:

```bash
impossible-move-gui
```

English at startup:

```bash
impossible-move-gui --language en
```

A larger generated experiment:

```bash
impossible-move-gui --items 500 --capacity 20 --instance C
```

Existing traces remain supported:

```bash
impossible-move-gui examples/demo_rule_trace.json \
  --catalog examples/demo_rule_catalog.json \
  --mode presentation
```

## Architecture

```text
ExperimentConfiguration
        |
        v
five reproducible candidates A-E
        |
        v
BinPackingEngine + ExplainableRuleBasedHH
        |
        +---- TracePolicy FULL / STANDARD / COMPACT
        |
        v
trace + catalog + aggregate statistics
        |
        v
ReplayController                language-neutral
        |
        v
adaptive/localized presenter    ES / EN
        |
        v
Qt adapters                     timer + UI state only
        |
        v
QML                             custom themed interface
```

Changing language never mutates the optimization state or replay cursor.

## License and attribution

The software is distributed under the **BSD 3-Clause License**. See `LICENSE` for the complete terms.

Public-facing attribution is displayed in the About dialog. The current copyright notice is:

```text
Copyright (c) 2026, OPTIMA Research Group / CICESE
```

## Documentation

- `EXPERIMENT_DESIGN.md` — generated experiments/cache/search-space architecture;
- `ADAPTIVE_VISUALIZATION.md` — multiscale visualization and trace policy;
- `HH_DESIGN.md` — explainable rule-based HH;
- `REPLAY_DESIGN.md` — replay contract;
- `FRONTEND_DESIGN.md` — frontend organization through V0.9.1;
- `UI_CHANGELOG_V0_9_0.md` — mapping of the first 19 reviewed findings to changes;
- `UI_CHANGELOG_V0_9_1.md` — second-round findings R2-1 through R2-7;
- `V0_9_1_VALIDATION.md` — current automated validation report.

## Validation note

The artifact environment does not provide PySide6 or a Qt/QML runtime, so the final graphical smoke test must be performed on a machine with the `gui` extra installed. The backend, presenter, localization data, QML structure and packaging are validated automatically.

Current automated validation for V0.9.1: **105/105 tests passed**.

## Persistent logs (V0.9.2)

Execution and Qt/QML diagnostics are now preserved in a rotating log file. On Windows the default file is `%LOCALAPPDATA%\ImpossibleMove\logs\impossible_move.log`. Use `--log-dir` to choose another directory and `--log-level DEBUG` for more detail. See `LOGGING.md`.

## V0.10.1 — QML parser hotfix

V0.10.1 fixes the comparison-panel QML syntax error that could prevent the application from starting under a real Qt runtime. It also adds a regression guard for invalid semicolon-separated child object declarations. No optimization or replay semantics changed.

## V0.10.0 — decision history and policy comparison

V0.10.0 adds an interactive HH decision-history explorer and a synchronized comparison mode. The same generated move can now be solved by the explainable adaptive HH, a reproducible random HH, and a selectable fixed strategy. Choose one, two, or all three methods in **Configure move**; comparison runs advance by complete object decisions so the policies remain aligned.

The comparison is experimental rather than a claim of global optimality: a fixed or random policy may tie or outperform the adaptive HH on individual instances. The UI therefore emphasizes trucks used, utilization and distance from the volume lower bound instead of labelling a policy as optimal.


## V0.10.2 hotfix

Fixes Qt/QML loading of `TruckCard.qml` by importing `QtQuick.Controls` for the `ToolTip` attached object.

## V0.11.0 — corpus profiles and move explorer

V0.11.0 adds three reproducible corpus profiles (`natural`, `contrastive`, `challenge`) so outreach comparisons are not limited to a forgiving distribution in which all policies frequently tie. The profiles are documented in `CORPUS_DESIGN.md` and empirically audited in `CORPUS_AUDIT.md`. They do not force the adaptive HH to win; Best Fit remains a strong baseline.

Comparison mode also adds a shared move explorer: click the current item / **View move** to inspect the complete instance, grouped summaries for large moves, and the per-policy truck chosen for already processed items.

CLI example:

```bash
impossible-move-gui --items 200 --capacity 10 --profile contrastive --instance A
```

Reproduce the corpus audit:

```bash
python examples/audit_corpus.py
```

## V0.12.0 — performance, adaptive explorer, and dual theme

V0.12.0 focuses on keeping the outreach GUI responsive as the visualization grows. Comparison playback is capped at approximately 30 visual updates per second and batches decisions at high speed; the 500-item move explorer is generated only when opened and released when closed; replay decision history is cached and not pushed into QML on every automatic frame.

The move explorer now adapts to scale: small/medium instances retain a virtualized item list, while large instances open on a type summary and drill down into one category at a time. Per-item policy placements use explicit columns instead of compressed edge labels.

The GUI also supports `dark` and `light` themes from the custom title bar. All QML colors are supplied by a centralized palette, and small UI typography was raised to a readable minimum. A bilingual Instructions popup in the footer explains the complete workflow.

Run with a chosen initial theme:

```bash
impossible-move-gui --theme light
```

## V0.13.0 — regime switching, best-fixed benchmark, and R6 debugging fixes

V0.13.0 adds a fourth corpus profile, **Regime switching**, in which the online item pattern changes in reproducible phases during the same move. This profile is intended to create genuine opportunities for dynamic heuristic selection while preserving cases where a fixed heuristic ties or wins.

When the adaptive HH is compared, the backend now also evaluates First Fit, Best Fit, Worst Fit, and Next Fit as fixed policies and reports the **best fixed strategy in hindsight** after the replay finishes. This is a post-hoc benchmark, not information available to the HH during the run.

The release also fixes the HH identity overlap, makes instance-profile descriptions readable through a 2x2 layout plus hover tooltips, and audits all themed scrollbars so their tracks span the full scrollable viewport.

See `CORPUS_DESIGN.md`, `CORPUS_AUDIT.md`, `SCROLL_AUDIT.md`, and `V0_13_0_VALIDATION.md`.

## V0.13.1 — comparison scrolling and HH identity layout hotfix

V0.13.1 replaces the compressed HH identity diagram with a vertical semantic flow and makes the comparison screen globally scrollable. The post-hoc best-fixed benchmark is now content-sized and responsive, while each policy keeps a dedicated scrollable truck-summary viewport.
