
import ast, math, re
from dataclasses import dataclass, field

PRICE = [26, 26, 27, 26, 26, 29, 36, 46, 44, 39, 53, 47, 42, 42, 40, 39, 48, 67, 78, 80, 81, 73, 63, 48]
COMMON_POWER = 10          # common power P0
SCALE = 10                 # every cost term is divided by 10
PM_LEN = 4                 # maintenance length (time steps)


def opl_round(x):
    return int(math.floor(x + 0.5))


def price(t):
    return PRICE[t % 24]


def parse_dat(path):
    text = open(path).read()
    text = re.sub(r"//[^\n]*", "", text) 
    out = {}
    for stmt in text.split(";"):
        if "=" not in stmt:
            continue
        name, val = stmt.split("=", 1)
        name, val = name.strip(), val.strip()
        if name:
            out[name] = ast.literal_eval(val) 
    return out


@dataclass
class Mode:
    """One way to process an operation: on machine k, for p steps, drawing `power` (effective, kW-like)."""
    op: int          # index into Instance.ops
    k: int           # machine, 0-based
    p: int           # processing time (time steps)
    power: float     # effective processing power = power1


@dataclass
class Instance:
    name: str
    n_mach: int
    ops: list                         # list of (job, opindex) , both 0-based, job-major order
    modes: list                       # list of Mode
    idle_power: list                  # effective idle power per machine = pidle / 10
    common_power: float               # effective = 1
    pm: list                          # per machine (start, end) maintenance window, 0-based machines
    mspan: int
    modes_of_op: dict = field(default_factory=dict)
    pred: dict = field(default_factory=dict)          # op -> predecessor op (same job) or None


def load(path, mspan):
    d = parse_dat(path)
    nP, nJ, nM = d["nbProcess"], d["nbJobs"], d["nbMchs"]
    n_ops_job = d.get("Process1", [nP] * nJ)
    x, ptime, power1, pidle = d["x"], d["ptime"], d["power1"], d["pidle"]

    ops, modes = [], []
    for j in range(nJ):
        for o in range(n_ops_job[j]):
            ops.append((j, o))
    for oi, (j, o) in enumerate(ops):
        for k in range(nM):
            if x[k][j][o] == 1:
                p = opl_round(ptime[k][j][o] / 10)
                if p <= 0:
                    raise ValueError(f"{path}: zero processing time after /10 for op {j},{o} on machine {k}")
                modes.append(Mode(oi, k, p, float(power1[k][j][o])))

    # maintenance windows
    step = opl_round(mspan / nM)
    pm_s = [mspan - (nM - m) * step for m in range(1, nM + 1)]
    pm_s[0] = 4
    pm_s[-1] = mspan
    pm = [(s, s + PM_LEN) for s in pm_s]

    inst = Instance(name=path.split("/")[-1].replace(".dat", ""), n_mach=nM, ops=ops, modes=modes,
                    idle_power=[v / SCALE for v in pidle], common_power=COMMON_POWER / SCALE,
                    pm=pm, mspan=mspan)
    for mi, md in enumerate(modes):
        inst.modes_of_op.setdefault(md.op, []).append(mi)
    for oi, (j, o) in enumerate(ops):
        if oi not in inst.modes_of_op:
            raise ValueError(f"{path}: operation {j},{o} has no allowed machine")
        inst.pred[oi] = oi - 1 if o > 0 else None
    return inst
