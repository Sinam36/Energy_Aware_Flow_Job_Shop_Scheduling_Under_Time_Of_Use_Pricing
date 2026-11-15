
import argparse, json, os
import fjsp_data as D, fjsp_model as M, fjsp_eval as E


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/instances")
    ap.add_argument("--instances", nargs="+", default=["sfjs01","sfjs04","sfjs07","sfjs10","mfjs01","mfjs03","mfjs05","mfjs08"])
    ap.add_argument("--time-limit", type=float, default=120)
    ap.add_argument("--out", default="mspans.json")
    a = ap.parse_args()
    res = json.load(open(a.out)) if os.path.exists(a.out) else {}
    status = json.load(open(a.out + ".status")) if os.path.exists(a.out + ".status") else {}
    for name in a.instances:
        inst = D.load(os.path.join(a.data, name + ".dat"), mspan=10**6)
        inst.pm = [(10**7, 10**7 + D.PM_LEN)] * inst.n_mach            # remove all maintenance
        g = E.greedy(inst)
        r = M.solve(inst, E.makespan(inst, g), "makespan", a.time_limit)
        C = E.makespan(inst, r["sched"]) if r["has_solution"] else E.makespan(inst, g)
        res[name] = C
        status[name] = dict(status=r["status"], gap=r["gap"], time=round(r["t_solve"], 1))
        print(f"{name}: mspan = {C}   [{r['status']}, gap {r['gap']}, {r['t_solve']:.1f}s]", flush=True)
        json.dump(res, open(a.out, "w"), indent=1)
        json.dump(status, open(a.out + ".status", "w"), indent=1)


if __name__ == "__main__":
    main()
