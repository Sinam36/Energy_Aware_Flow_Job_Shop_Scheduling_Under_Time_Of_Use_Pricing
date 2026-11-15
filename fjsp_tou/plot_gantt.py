
import argparse, json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import fjsp_data as D, fjsp_eval as E


def draw(ax, inst, sched, title, H):
    for k in range(inst.n_mach):
        a, b = inst.pm[k]
        if a < H:
            ax.barh(k, b - a, left=a, color="white", edgecolor="0.4", hatch="///", height=0.6)
    for oi, (mi, s) in sched.items():
        md = inst.modes[mi]
        j, o = inst.ops[oi]
        ax.barh(md.k, md.p, left=s, color=plt.cm.tab10(j % 10), edgecolor="black", height=0.6)
        ax.text(s + md.p / 2, md.k, f"J{j+1}O{o+1}", ha="center", va="center", fontsize=7, color="white")
    c = E.cost(inst, sched)
    ax.set_title(f"{title}: Cmax={c['Cmax']}, eC={c['eC']:.1f}, eP={c['eP']:.1f}, eI={c['eI']:.1f}, TC={c['TC']:.1f}", fontsize=9)
    ax.set_yticks(range(inst.n_mach)); ax.set_yticklabels([f"M{k+1}" for k in range(inst.n_mach)])
    ax.invert_yaxis(); ax.set_xlim(0, H)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/instances")
    ap.add_argument("--results", default="results")
    ap.add_argument("--instance", required=True)
    ap.add_argument("--mspan", default="mspans.json")
    a = ap.parse_args()
    inst = D.load(os.path.join(a.data, a.instance + ".dat"), json.load(open(a.mspan))[a.instance])
    S = json.load(open(os.path.join(a.results, "schedules.json")))
    get = lambda m: {int(o): tuple(v) for o, v in S[f"{a.instance}|{m}"].items()}
    s1, s2 = get("makespan_only"), get("energy_aware")
    H = max(E.makespan(inst, s1), E.makespan(inst, s2))
    fig, axs = plt.subplots(3, 1, figsize=(12, 2 + 1.1 * inst.n_mach),
                            gridspec_kw=dict(height_ratios=[inst.n_mach, inst.n_mach, 0.6]), sharex=True)
    draw(axs[0], inst, s1, "(a) Makespan only", H)
    draw(axs[1], inst, s2, "(b) Energy-aware, same makespan", H)
    pr = [D.price(t) for t in range(H)]
    axs[2].imshow([pr], aspect="auto", cmap="RdYlGn_r", extent=(0, H, 0, 1))
    for t in range(H):
        axs[2].text(t + 0.5, 0.5, str(pr[t]), ha="center", va="center", fontsize=6)
    axs[2].set_yticks([]); axs[2].set_xlabel("time step (hour)"); axs[2].set_title("hourly price", fontsize=8)
    fig.tight_layout()
    out = os.path.join(a.results, f"gantt_{a.instance}.png")
    fig.savefig(out, dpi=150)
    print("saved", out)


if __name__ == "__main__":
    main()
