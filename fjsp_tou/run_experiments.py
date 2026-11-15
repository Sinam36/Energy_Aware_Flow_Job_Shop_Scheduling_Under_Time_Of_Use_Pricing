"""
run_experiments.py — runs every method on the chosen instances and writes the result tables.

Per instance:
  1. greedy heuristic            -> feasible schedule; its makespan is phase 1's horizon h0
  2. phase 1  (min makespan)     -> T*; its schedule is the "traditional" (makespan-only) baseline
  3. phase 2  (min cost, h = T*) -> energy-aware schedule (our two-phase method)
Every schedule is re-checked for feasibility and its cost recomputed independently (fjsp_eval);
any mismatch with the solver's objective is reported in the 'check' column.

Usage (see README.md):
  python run_experiments.py                                  (defaults: data/instances, all 8 instances, 120 s)
  python run_experiments.py --instances sfjs01 sfjs04 --time-limit 60
"""
import argparse, csv, json, os, time
import fjsp_data as D, fjsp_model as M, fjsp_eval as E


def size_str(inst):
    jobs = {j for j, _ in inst.ops}
    max_ops = max(o for _, o in inst.ops) + 1
    return f"{len(jobs)}/{max_ops}/{inst.n_mach}"


def check(inst, res, kind):
    """Feasibility + objective re-computation. Returns (cost dict or None, message)."""
    if not res["has_solution"]:
        return None, "no solution"
    errs = E.check_feasible(inst, res["sched"])
    c = E.cost(inst, res["sched"])
    expect = c["Cmax"] if kind == "makespan" else c["TC"]
    ok = abs(res["obj"] - expect) <= 1e-6 * max(1.0, abs(expect)) + 1e-3
    msg = "ok" if (not errs and ok) else ("INFEASIBLE: " + "; ".join(errs[:3]) if errs else
                                          f"OBJECTIVE MISMATCH solver={res['obj']:.3f} recomputed={expect:.3f}")
    return c, msg


def row(inst, method, h, res, c, msg, extra=None):
    r = dict(instance=inst.name, size=size_str(inst), mspan=inst.mspan, method=method, horizon=h,
             status=res.get("status", ""), Cmax=c["Cmax"] if c else "", eC=round(c["eC"], 1) if c else "",
             eP=round(c["eP"], 1) if c else "", eI=round(c["eI"], 1) if c else "", TC=round(c["TC"], 1) if c else "",
             gap=round(res["gap"], 5) if res.get("gap") is not None else "",
             time=round(res.get("t_solve", 0.0), 2), n_bin=res.get("n_bin", ""), check=msg)
    if extra:
        r.update(extra)
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/instances")
    ap.add_argument("--instances", nargs="+", default=["sfjs01","sfjs04","sfjs07","sfjs10","mfjs01","mfjs03","mfjs05","mfjs08"])
    ap.add_argument("--mspan", default="mspans.json", help="JSON file: instance -> mspan")
    ap.add_argument("--time-limit", type=float, default=120)
    ap.add_argument("--out", default="results")
    a = ap.parse_args()

    os.makedirs(a.out, exist_ok=True)
    mspans = json.load(open(a.mspan))
    rows, schedules = [], {}

    for name in a.instances:
        inst = D.load(os.path.join(a.data, name + ".dat"), mspans[name])
        print(f"\n=== {name}  size {size_str(inst)}  mspan {inst.mspan}  maintenance {inst.pm}", flush=True)

        # 1. greedy
        t0 = time.time(); g = E.greedy(inst); tg = time.time() - t0
        gres = dict(has_solution=True, sched=g, obj=E.cost(inst, g)["TC"], status="heuristic", t_solve=tg)
        gc, gmsg = check(inst, gres, "cost")
        rows.append(row(inst, "greedy", "", gres, gc, gmsg)); schedules[(name, "greedy")] = g
        h0 = gc["Cmax"]
        print(f"greedy: Cmax {h0}  TC {gc['TC']:.1f}  [{gmsg}]", flush=True)

        # 2. phase 1
        r1 = M.solve(inst, h0, "makespan", a.time_limit)
        c1, m1 = check(inst, r1, "makespan")
        rows.append(row(inst, "phase1_makespan_only", h0, r1, c1, m1))
        if c1 is None:
            print("phase 1 found no solution; skipping instance", flush=True)
            continue
        schedules[(name, "makespan_only")] = r1["sched"]
        T = c1["Cmax"]
        print(f"phase 1: T* {T} [{r1['status']}, gap {r1['gap']:.4f}, {r1['t_solve']:.1f}s]  [{m1}]", flush=True)

        # 3. phase 2
        r2 = M.solve(inst, T, "cost", a.time_limit)
        c2, m2 = check(inst, r2, "cost")
        rows.append(row(inst, "phase2_energy_aware", T, r2, c2, m2,
                        extra=dict(phase1_status=r1["status"], phase1_gap=round(r1["gap"], 5))))
        if c2:
            schedules[(name, "energy_aware")] = r2["sched"]
            print(f"phase 2: TC {c2['TC']:.1f} [{r2['status']}, gap {r2['gap']:.4f}, {r2['t_solve']:.1f}s]  [{m2}]", flush=True)

        # save after every instance, so partial results survive an interruption
        save(a.out, rows, schedules, inst_list=a.instances)

    save(a.out, rows, schedules, inst_list=a.instances)
    print(f"\nwritten: {a.out}/results.csv, {a.out}/summary.md, {a.out}/schedules.json")


def save(out, rows, schedules, inst_list):
    keys = []
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    with open(os.path.join(out, "results.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows(rows)
    json.dump({f"{n}|{m}": {str(o): list(v) for o, v in s.items()} for (n, m), s in schedules.items()},
              open(os.path.join(out, "schedules.json"), "w"))
    open(os.path.join(out, "summary.md"), "w").write(summary(rows, inst_list))


def summary(rows, inst_list):
    by = {(r["instance"], r["method"]): r for r in rows}
    L = []
    L.append("## Table A: Two-phase ILP results\n")
    L.append("| Instance | Size | Phase-1 Cmax (status, gap) | Phase-1 time (s) | Phase-2 TC (status, gap) | Phase-2 time (s) | Binaries P1 / P2 | Check |")
    L.append("|---|---|---|---|---|---|---|---|")
    for n in inst_list:
        p1, p2 = by.get((n, "phase1_makespan_only")), by.get((n, "phase2_energy_aware"))
        if not p1:
            continue
        L.append(f"| {n} | {p1['size']} | {p1['Cmax']} ({p1['status']}, {p1['gap']}) | {p1['time']} | "
                 f"{(str(p2['TC']) + ' (' + p2['status'] + ', ' + str(p2['gap']) + ')') if p2 else '-'} | "
                 f"{p2['time'] if p2 else '-'} | {p1['n_bin']} / {p2['n_bin'] if p2 else '-'} | {p2['check'] if p2 else p1['check']} |")
    L.append("\n## Table B: Energy saving at the same makespan (makespan-only schedule vs energy-aware)\n")
    L.append("| Instance | Size | Cmax | Greedy Cmax / TC | Makespan-only eC / eP / eI / TC | Energy-aware eC / eP / eI / TC | Saving |")
    L.append("|---|---|---|---|---|---|---|")
    for n in inst_list:
        g, p1, p2 = by.get((n, "greedy")), by.get((n, "phase1_makespan_only")), by.get((n, "phase2_energy_aware"))
        if not (p1 and p2 and p2["TC"] != ""):
            continue
        sav = 100 * (p1["TC"] - p2["TC"]) / p1["TC"]
        L.append(f"| {n} | {p1['size']} | {p1['Cmax']} | {g['Cmax']} / {g['TC']} | "
                 f"{p1['eC']} / {p1['eP']} / {p1['eI']} / {p1['TC']} | {p2['eC']} / {p2['eP']} / {p2['eI']} / {p2['TC']} | {sav:.1f}% |")
    L.append("\nNote: the makespan-only schedule is whichever minimum-makespan schedule the solver returned; "
             "its cost is not unique.")

    return "\n".join(L) + "\n"


if __name__ == "__main__":
    main()
