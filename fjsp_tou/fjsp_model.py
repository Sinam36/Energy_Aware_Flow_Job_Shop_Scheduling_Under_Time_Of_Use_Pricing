"""
fjsp_model.py — time-indexed ILP for energy-aware flexible job-shop scheduling with time-of-use prices and
maintenance.

Variables
  X[o,k,t] in {0,1} : operation o starts on machine k at time t.
      In the code a "mode" m is one (operation o, machine k) pair, so W[m, t] is X[o,k,t].
      Created only for 0 <= t <= h - p_ok (the operation must end inside the horizon) and only if
      [t, t+p_ok) does not overlap machine k's maintenance window; a variable that is not created is
      the same as one fixed to 0, which is how constraint (6) is enforced.
  L[t] in {0,1} : 1 if t < makespan (system still running at time t).   Cmax = sum_t L[t]

Constraints
  (1) each operation starts exactly once:        sum_{k,t} X[o,k,t] = 1                          for all o
  (2) precedence (q directly before o in a job): sum (t + p_qk) X[q,k,t]  <=  sum t X[o,k,t]
  (3) one operation per machine at a time:       sum of X[o,k,r] with r <= t <= r + p_ok - 1  <= 1   for all k, t
  (4) the system stops only once:                L[t] >= L[t+1]
  (5) system running while an operation runs:    L[t + p_ok - 1] >= X[o,k,t]
  (6) no processing during maintenance:          X[o,k,t] = 0 if [t, t+p_ok) overlaps [s_k, e_k)  (not created)
  (7) all variables binary

Objectives
  'makespan' : min Cmax = sum_t L[t]                                (phase 1)
  'cost'     : min TC = eC + eP + eI                                (phase 2; horizon h = T*)
  eC = sum_t P0 * c_t * L[t]
  eP = sum_{o,k,t} P_ok * (c_t + ... + c_{t+p_ok-1}) * X[o,k,t]
  eI = sum_k sum_t D_k * c_t * L[t]  -  sum_{o,k,t} D_k * (c_t + ... + c_{t+p_ok-1}) * X[o,k,t]
  (power values: see fjsp_data.py; maintenance hours fall inside eI's first term, i.e. are charged at idle power)
"""
import time
import pulp
import highspy
from fjsp_data import price

def run_price(t, p):
    return sum(price(r) for r in range(t, t + p))


def build(inst, h, objective):
    prob = pulp.LpProblem(f"{inst.name}_{objective}", pulp.LpMinimize)
    W = {}
    for mi, md in enumerate(inst.modes):
        a, b = inst.pm[md.k]
        for t in range(0, h - md.p + 1):
            if t < b and t + md.p > a:          # constraint (6): would overlap maintenance
                continue
            W[mi, t] = pulp.LpVariable(f"W_{mi}_{t}", cat="Binary")
    L = [pulp.LpVariable(f"L_{t}", cat="Binary") for t in range(h)]

    by_mode = {}
    for (mi, t), v in W.items():
        by_mode.setdefault(mi, []).append((t, v))

    # (1) each operation starts exactly once
    for oi, mis in inst.modes_of_op.items():
        terms = [v for mi in mis for _, v in by_mode.get(mi, [])]
        if not terms:
            raise ValueError(f"{inst.name}: op {oi} cannot be placed in horizon {h}")
        prob += pulp.lpSum(terms) == 1, f"c1_{oi}"
    # (2) precedence within a job
    for oi, q in inst.pred.items():
        if q is None:
            continue
        end_q = pulp.lpSum((t + inst.modes[mi].p) * v for mi in inst.modes_of_op[q] for t, v in by_mode.get(mi, []))
        start_o = pulp.lpSum(t * v for mi in inst.modes_of_op[oi] for t, v in by_mode.get(mi, []))
        prob += end_q <= start_o, f"c2_{q}_{oi}"
    # (3) one operation per machine at a time
    busy = {}
    for (mi, t), v in W.items():
        md = inst.modes[mi]
        for r in range(t, t + md.p):
            busy.setdefault((md.k, r), []).append(v)
    for (k, r), vs in busy.items():
        if len(vs) > 1:
            prob += pulp.lpSum(vs) <= 1, f"c3_{k}_{r}"
    # (4) the system stops only once
    for t in range(h - 1):
        prob += L[t] >= L[t + 1], f"c4_{t}"
    # (5) system running while an operation runs
    for (mi, t), v in W.items():
        prob += L[t + inst.modes[mi].p - 1] >= v, f"c5_{mi}_{t}"

    cmax = pulp.lpSum(L)
    eC = pulp.lpSum(inst.common_power * price(t) * L[t] for t in range(h))
    eP = pulp.lpSum(inst.modes[mi].power * run_price(t, inst.modes[mi].p) * v for (mi, t), v in W.items())
    eI = (pulp.lpSum(inst.idle_power[k] * price(t) * L[t] for k in range(inst.n_mach) for t in range(h))
          - pulp.lpSum(inst.idle_power[inst.modes[mi].k] * run_price(t, inst.modes[mi].p) * v
                       for (mi, t), v in W.items()))
    if objective == "makespan":
        prob += cmax
    elif objective == "cost":
        prob += eC + eP + eI
    else:
        raise ValueError(objective)
    return prob, W, L


def solve(inst, h, objective, time_limit, gap=0.0, threads=None):
    """Build + solve. Returns a dict with status, objective, HiGHS gap / bound, times and schedule."""
    t0 = time.time()
    prob, W, L = build(inst, h, objective)
    t_build = time.time() - t0
    solver = pulp.HiGHS(msg=False, timeLimit=time_limit, gapRel=gap, threads=threads)
    t0 = time.time()
    try:
        prob.solve(solver)
    except pulp.PulpSolverError:
        pass
    t_solve = time.time() - t0
    hs = prob.solverModel
    info = hs.getInfo()
    status = hs.modelStatusToString(hs.getModelStatus())
    has_sol = info.primal_solution_status == 2            # 2 = feasible solution available
    res = dict(objective=objective, h=h, status=status, has_solution=has_sol,
               n_bin=len(W) + len(L), n_cons=len(prob.constraints),
               t_build=t_build, t_solve=t_solve,
               obj=info.objective_function_value if has_sol else None,
               bound=info.mip_dual_bound, gap=info.mip_gap if has_sol else None, sched=None)
    if has_sol:
        sched = {}
        for (mi, t), v in W.items():
            if v.value() is not None and v.value() > 0.5:
                sched[inst.modes[mi].op] = (mi, t)
        res["sched"] = sched
    return res
