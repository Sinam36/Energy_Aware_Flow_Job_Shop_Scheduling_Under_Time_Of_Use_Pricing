from fjsp_data import price


def makespan(inst, sched):
    return max(s + inst.modes[mi].p for mi, s in sched.values())


def check_feasible(inst, sched):
    errs = []
    if set(sched) != set(range(len(inst.ops))):
        errs.append("not every operation is scheduled exactly once")
    for oi, (mi, s) in sched.items():
        md = inst.modes[mi]
        if md.op != oi:
            errs.append(f"op {oi}: mode belongs to another op")
        if s < 0:
            errs.append(f"op {oi}: negative start")
        a, b = inst.pm[md.k]                                          # maintenance overlap
        if s < b and s + md.p > a:
            errs.append(f"op {oi}: overlaps maintenance on machine {md.k}")
        q = inst.pred[oi]                                            # precedence
        if q is not None:
            mq, sq = sched[q]
            if sq + inst.modes[mq].p > s:
                errs.append(f"op {oi}: starts before predecessor {q} ends")
    by_m = {}
    for oi, (mi, s) in sched.items():                                # no overlap on a machine
        by_m.setdefault(inst.modes[mi].k, []).append((s, s + inst.modes[mi].p, oi))
    for k, iv in by_m.items():
        iv.sort()
        for (s1, e1, o1), (s2, e2, o2) in zip(iv, iv[1:]):
            if s2 < e1:
                errs.append(f"machine {k}: ops {o1} and {o2} overlap")
    return errs


def cost(inst, sched):
    """eC, eP, eI, TC (machines on from 0 to makespan; maintenance hours are charged at idle power)."""
    C = makespan(inst, sched)
    eC = sum(inst.common_power * price(t) for t in range(C))
    eP = 0.0
    eI = sum(inst.idle_power[k] * price(t) for k in range(inst.n_mach) for t in range(C))
    for oi, (mi, s) in sched.items():
        md = inst.modes[mi]
        run = sum(price(t) for t in range(s, s + md.p))
        eP += md.power * run
        eI -= inst.idle_power[md.k] * run
    return dict(Cmax=C, eC=eC, eP=eP, eI=eI, TC=eC + eP + eI)


def greedy(inst):
    """Repeatedly schedule, among operations whose predecessor is done, the (operation, machine)
    pair that FINISHES earliest; append it at the end of that machine, jumping past maintenance.
    Ties: lower processing power, then lower op index. Always feasible."""
    free = [0] * inst.n_mach
    end = {}
    sched = {}
    todo = set(range(len(inst.ops)))
    while todo:
        best = None
        for oi in todo:
            q = inst.pred[oi]
            if q is not None and q not in end:
                continue
            ready = 0 if q is None else end[q]
            for mi in inst.modes_of_op[oi]:
                md = inst.modes[mi]
                s = max(free[md.k], ready)
                a, b = inst.pm[md.k]
                if s < b and s + md.p > a:
                    s = b
                key = (s + md.p, md.power, oi)
                if best is None or key < best[0]:
                    best = (key, oi, mi, s)
        _, oi, mi, s = best
        md = inst.modes[mi]
        sched[oi] = (mi, s)
        end[oi] = s + md.p
        free[md.k] = s + md.p
        todo.remove(oi)
    return sched
