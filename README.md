# Energy-aware FJSP under TOU pricing: two-phase ILP
Time-indexed ILP for energy-aware flexible job-shop scheduling under time-of-use pricing with scheduled maintenance,
solved lexicographically in two phases (makespan, then energy cost).

## Dependencies (no other packages needed)
- Python 3.9+
- `pulp` **2.x** (tested with 2.9.0). PuLP 3+ changed its API and this code will not run on it.
- `highspy` (the HiGHS solver; free, no licence)
- `matplotlib` (only for `plot_gantt.py`)

python -m pip install -r requirements.txt

## How to run
From inside this folder (`fjsp_tou/`), in this order:
```
python compute_mspan.py
python run_experiments.py
python plot_gantt.py --instance sfjs04
```
Defaults: data from `data/`, all 8 instances, 120 s time limit per solve. Options: `--instances sfjs01 sfjs04`
(subset), `--time-limit 60`.

Outputs: `mspans.json` (+ `.status`), `results/results.csv`, `results/summary.md` (Table A: two-phase ILP results; Table B: energy saving and greedy heuristic),
`results/schedules.json`, `results/gantt_sfjs04.png`.

## Data (included)
```
data/instances/       8 benchmark instances (.dat, OPL format, unmodified)
```
Fattahi et al. (2007) SFJS/MFJS instances with energy data from Meng et al. (2019)

## Files
| File | What it does |
|---|---|
| `fjsp_data.py` | Parses the OPL `.dat` files; sets processing times, powers, prices and maintenance windows |
| `fjsp_model.py` | The time-indexed ILP: constraints (1)–(7); objectives `makespan` (phase 1) and `cost` (phase 2) |
| `fjsp_eval.py` | Independent checker: feasibility of a schedule, cost recomputed from start times, greedy heuristic |
| `compute_mspan.py` | Computes the maintenance-placement parameter `mspan` for each instance (see below) |
| `run_experiments.py` | Runs greedy → phase 1 → phase 2 on each instance; writes the tables |
| `plot_gantt.py` | Gantt chart (makespan-only vs energy-aware) with hourly price strip |


## Method
Solver settings: HiGHS, relative gap 0 (solve to proven optimality), time limit per solve = `--time-limit`.
If phase 1 stops at the time limit, T* is only the best makespan found; its status and gap are recorded with phase 2.

## Checks performed
 The `check` column says `ok`
  only if the schedule is feasible **and** the recomputed value equals the solver's objective.

**`mspan`** is not given in the instance files. We set it to the minimum makespan of the instance **without
maintenance**, so maintenance is spread over the nominal production period and the last window falls where production
would otherwise end; `compute_mspan.py` computes it. For large instances this solve may hit the time limit; then the
best makespan found is used, and the solver status is recorded in `mspans.json.status`.
