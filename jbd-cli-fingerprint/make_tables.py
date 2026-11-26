# Recompute Tables 1/4/5/6, Sec. VII-D and the Sec. VII-H capacities from results/
# usage: python make_tables.py   (numpy, scipy)

import collections, json, os
import numpy as np
from scipy import stats

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
SEEDS = list(range(10, 30))   # held-out


def load(name, key):
    out = collections.defaultdict(dict)
    for r in json.load(open(os.path.join(ROOT, name + ".json"))):
        out[key(r)][r["seed"]] = r
    return out


def holm(p):
    p = np.asarray(p, float)
    order = np.argsort(p)
    adj = np.empty_like(p)
    run = 0.0
    for r, i in enumerate(order):
        run = max(run, (len(p) - r) * p[i])
        adj[i] = min(run, 1.0)
    return adj


def paired(a, b, k):
    d = np.array([a[s][k] - b[s][k] for s in SEEDS])
    ci = stats.t.ppf(0.975, len(d) - 1) * d.std(ddof=1) / np.sqrt(len(d))
    return d.mean(), ci, stats.ttest_1samp(d, 0).pvalue


def mean(D, k):
    return np.mean([D[s][k] for s in SEEDS])


def table5(H):
    ref = H["Reactive DTDD + Blacklist (0 dB) + AI-BM"]
    keys = ["sinrU_p5", "sinrD_p5", "delayU", "ue_thU_p5"]
    tests = []
    for s in H:
        if s == "Reactive DTDD + Blacklist (0 dB) + AI-BM":
            continue
        for k in keys:
            if s == "Static TDD" and k in ("delayU", "ue_thU_p5"):   # unstable, no delay
                continue
            tests.append((s, k) + paired(H[s], ref, k))
    adj = holm([t[4] for t in tests])

    print("\nTable 5")
    print(f"{'scheme':42s}{'UL5':>7s}{'DL5':>7s}{'delay':>8s}{'UEthr5':>8s}")
    for s in sorted(H):
        print(f"{s:42s}" + "".join(f"{mean(H[s], k):{w}.2f}" for k, w in zip(keys, (7, 7, 8, 8))))
    print("diff. to tuned blacklisting (** p<.01, * p<.05, Holm)")
    for t, a in zip(tests, adj):
        sig = "**" if a < .01 else "*" if a < .05 else ""
        print(f"   {t[0]:42s} {t[1]:10s} {t[2]:+7.2f} +/- {t[3]:.2f} {sig}")


def table6(H, L):
    jbd = H["JBD (proposed)"]
    rows = {"Beam-agnostic DTDD": H["Reactive DTDD + AI-BM"],
            "Tuned blacklisting": H["Reactive DTDD + Blacklist (0 dB) + AI-BM"]}
    rows.update(L)
    tests = [(n, k) + paired(D, jbd, k) for n, D in rows.items() for k in ("sinrU_p5", "delayU")]
    print("\nTable 6, diff. to JBD")
    for t, a in zip(tests, holm([t[4] for t in tests])):
        print(f"   {t[0]:22s} {t[1]:9s} {t[2]:+7.2f} +/- {t[3]:.2f}  {'' if a < .05 else '(n.s.)'}")


def mismatch(S, W):
    print("\nSec. VII-D, UL tail: JBD (est.) minus blacklisting; retained value")
    for w in ["ideal", "realistic", "dense_m15", "harsh", "realistic_coh"]:
        if w == "realistic_coh":   # new world, all runs in results/worlds
            agn, bl0, j, jx = (W[f"{x}__realistic_coh"] for x in ("AGN", "BL0", "JBD", "JBDexact"))
            blt = W["BLtuned__realistic_coh"]
        else:
            agn, bl0 = S[f"{w}__exact__AGN"], S[f"{w}__robust_online__BL0"]
            j, jx = S[f"{w}__robust_online__JBD"], S[f"{w}__exact__JBD"]
            blt = W.get(f"BLtuned__{w}") or bl0     # 0 dB is already the best threshold in 'ideal'
        a = paired(j, bl0, "sinrU_p5")
        b = paired(j, blt, "sinrU_p5")
        kept = (mean(j, "sinrU_p5") - mean(agn, "sinrU_p5")) / (mean(jx, "sinrU_p5") - mean(agn, "sinrU_p5"))
        print(f"   {w:14s} vs 0 dB {a[0]:+.2f}+/-{a[1]:.2f} | vs re-tuned {b[0]:+.2f}+/-{b[1]:.2f} | kept {kept * 100:.1f}%")


def offline():
    by = collections.defaultdict(list)
    for r in json.load(open(os.path.join(ROOT, "offline_fingerprint.json"))):
        by[r["cond"]].append(r)
    print("\nTables 1/4, MAE [dB] on pairs with CLI/N >= 0 dB, 256 meas.")
    for c, v in by.items():
        m = lambda k: np.mean([x[k] for x in v])
        print(f"   {c:14s} spec {m('spec_struct_mae_db_strong'):5.2f}  prop {m('prop_struct_mae_db_strong'):5.2f}  "
              f"prop+rand {m('prop_random_mae_db_strong'):5.2f}  unmeas {m('prop_struct_unmeas_mae_db_strong'):5.2f}  "
              f"rank(S+1) {m('rank_mae_db'):5.2f}  energy {m('energy_top') * 100:6.2f}%")


def capacity():
    D = collections.defaultdict(lambda: collections.defaultdict(dict))
    for r in json.load(open(os.path.join(ROOT, "capacity.json"))):
        b, load = r["tag"].split("_")[:2]
        D[(int(b[1:]), r["scheme"])][int(load[4:])][r["seed"]] = r

    def cap(b, sch):
        loads = sorted(D[(b, sch)])
        out = {}
        for s in sorted(set.intersection(*[set(D[(b, sch)][l]) for l in loads])):
            c = loads[0] - 10          # unstable already at the lowest load
            for l in loads:
                if D[(b, sch)][l][s]["stable"] < 0.5:
                    break
                c = l
            out[s] = c
        return out

    print("\nSec. VII-H, stable capacity [Mb/s/cell], fingerprint gain over beam-agnostic DTDD")
    for b in (32, 64):
        bl, agn = cap(b, "Reactive DTDD + Blacklist (0 dB) + AI-BM"), cap(b, "Reactive DTDD + AI-BM")
        d = np.array([bl[s] - agn[s] for s in sorted(bl)])
        print(f"   B={b}: per seed {d.tolist()}  mean {d.mean():.1f}  median {np.median(d):.0f}  p={stats.wilcoxon(d).pvalue:.3f}")
    j, jh = cap(64, "JBD (proposed)"), cap(64, "JBD (Hier-BM)")
    d = np.array([j[s] - jh[s] for s in sorted(j)])
    print(f"   B=64, JBD AI-BM minus hier. sweep: mean {d.mean():.1f}  p={stats.wilcoxon(d).pvalue:.3f}")


if __name__ == "__main__":
    H = load("holdout", lambda r: r["scheme"])
    L = load("lit", lambda r: r["tag"].split("__")[1])
    W = load("worlds", lambda r: r["tag"])
    S = load("mismatch_sys", lambda r: r["run"].rsplit("__s", 1)[0])
    table5(H)
    table6(H, L)
    mismatch(S, W)
    offline()
    capacity()
