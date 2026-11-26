# jbd-cli-fingerprint

Configuration, seeds and per-run results for

S. H. Kim and J.-M. Chung, "Low-Rank CLI Fingerprints for Beam-Aware Dynamic TDD in FR2 Networks:
Joint Beam-Duplex Control and Loss-Guarded O-RAN Automation," submitted to IEEE Access.

The simulator is not included here. It is available upon request from the authors
(Sung Hyun Kim, leothecat@yonsei.ac.kr).

## Layout

    config/
      params_default.json   simulation parameters (defaults, see Table 3)
      schemes.json          compared schemes
      worlds.json           model-mismatch worlds (Sec. VII-D), incl. coherent ones
      experiments.json      which runs go into which table/figure, seeds, run length, overrides
    results/                one JSON file per experiment, each a list of run records
      holdout.json          Table 5 (420 Mb/s/cell, seeds 10-29, 1000 epochs)
      lit.json              Table 6 (ABSF, cancellation; other rows shared with holdout.json)
      mismatch_sys.json, worlds.json   Fig. 4(b), Sec. VII-D (400 epochs)
      tune.json             per-world tuning of the blacklisting threshold and w_DL (seeds 0-9)
      offline_fingerprint.json  Tables 1 and 4
      fingerprint_budget.json   Fig. 4(a)
      convergence.json      Table 2
      capacity.json         Fig. 8, Sec. VII-H (seeds 10-19, 75 s runs, B = 32 and 64)
    make_tables.py          recomputes Tables 1/4/5/6, the Sec. VII-D margins and the Sec. VII-H capacities

## Seeds

Seeds 0-9 were used for tuning only, 10-29 for all reported comparisons.
For seed s the network/channel RNG is seeded with 1000 + 97*s and the traffic RNG with 5000 + 97*s,
so all schemes of an experiment see the same realization. In the offline study, realization r uses
1000 + r for the network and 77 + r for the estimator.

## Metrics in the run records

The field run is the name of the original run (scheme, world or load, and seed).

- sinrU_p5 / sinrD_p5: 5th percentile SINR over all scheduled UL / DL slot groups of the seven cells
  (warm-up included); the *_pw fields leave out the first 40 epochs
- delayU: mean UL queuing delay, only meaningful when stable == 1
- ue_thU_p5: 5th percentile over the 56 UEs of the UL throughput per UE (after warm-up)
- ue_share_p5: served UL groups / groups as best-SNR candidate, 5th percentile over UEs
- ue_exp_kept: share of CLI-exposed best-SNR UL choices that were still served

## Run

    pip install numpy scipy
    python make_tables.py

Data and config files: CC BY 4.0 (LICENSE-DATA). make_tables.py: MIT (LICENSE).
