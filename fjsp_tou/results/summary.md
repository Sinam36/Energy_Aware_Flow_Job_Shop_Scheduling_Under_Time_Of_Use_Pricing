## Table A: Two-phase ILP results

| Instance | Size | Phase-1 Cmax (status, gap) | Phase-1 time (s) | Phase-2 TC (status, gap) | Phase-2 time (s) | Binaries P1 / P2 | Check |
|---|---|---|---|---|---|---|---|
| sfjs01 | 2/2/2 | 13 (Optimal, 0.0) | 0.02 | 2286.1 (Optimal, 0.0) | 0.01 | 57 / 44 | ok |
| sfjs04 | 3/2/2 | 44 (Optimal, 0.0) | 0.42 | 14304.3 (Optimal, 0.0) | 0.12 | 386 / 304 | ok |
| sfjs07 | 3/3/5 | 51 (Optimal, 0.0) | 0.32 | 17276.5 (Optimal, 0.0) | 0.74 | 561 / 561 | ok |
| sfjs10 | 4/3/5 | 66 (Optimal, 0.0) | 1.06 | 32263.5 (Optimal, 0.0) | 0.68 | 1098 / 864 | ok |
| mfjs01 | 5/3/6 | 56 (Optimal, 0.0) | 12.92 | 37692.5 (Optimal, 0.0) | 1.63 | 1738 / 1098 | ok |
| mfjs03 | 6/3/7 | 59 (Optimal, 0.0) | 26.95 | 41146.9 (Optimal, 0.0) | 6.35 | 2993 / 1563 | ok |
| mfjs05 | 7/3/7 | 64 (Optimal, 0.0) | 29.67 | 50994.7 (Optimal, 0.0) | 7.59 | 3459 / 2000 | ok |

## Table B: Energy saving at the same makespan (makespan-only schedule vs energy-aware)

| Instance | Size | Cmax | Greedy Cmax / TC | Makespan-only eC / eP / eI / TC | Energy-aware eC / eP / eI / TC | Saving |
|---|---|---|---|---|---|---|
| sfjs01 | 2/2/2 | 13 | 15 / 2330.6 | 467.0 / 2149.0 / 70.5 / 2686.5 | 467.0 / 1752.2 / 66.9 / 2286.1 | 14.9% |
| sfjs04 | 3/2/2 | 44 | 55 / 15887.8 | 1987.0 / 12650.7 / 139.2 / 14776.9 | 1987.0 / 12158.1 / 159.2 / 14304.3 | 3.2% |
| sfjs07 | 3/3/5 | 51 | 51 / 19268.7 | 2331.0 / 14884.3 / 1249.6 / 18464.9 | 2331.0 / 13544.5 / 1401.0 / 17276.5 | 6.4% |
| sfjs10 | 4/3/5 | 66 | 78 / 34462.0 | 2955.0 / 30199.1 / 1233.6 / 34387.7 | 2955.0 / 28004.4 / 1304.1 / 32263.5 | 6.2% |
| mfjs01 | 5/3/6 | 56 | 76 / 39466.4 | 2494.0 / 35345.2 / 1355.3 / 39194.5 | 2494.0 / 33730.5 / 1468.0 / 37692.5 | 3.8% |
| mfjs03 | 6/3/7 | 59 | 89 / 47611.5 | 2630.0 / 39617.1 / 1645.6 / 43892.7 | 2630.0 / 36817.5 / 1699.4 / 41146.9 | 6.3% |
| mfjs05 | 7/3/7 | 64 | 91 / 53977.8 | 2840.0 / 47656.5 / 1647.7 / 52144.2 | 2840.0 / 46423.1 / 1731.6 / 50994.7 | 2.2% |

Note: the makespan-only schedule is whichever minimum-makespan schedule the solver returned; its cost is not unique.

## mfjs08 (run separately, laptop: Intel i7, 32 GB)

| Instance | Size | Maintenance-placement solve | Greedy Cmax / TC | Phase 1 |
|---|---|---|---|---|
| mfjs08 | 9/4/8 | Time limit reached (120 s), no feasible solution; greedy makespan 157 used | 162 / 111151.1 | Time limit reached (120 s), no feasible solution |
