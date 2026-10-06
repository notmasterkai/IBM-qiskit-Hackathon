"""Save the per-seed sweep values behind the QBER and S plots, for the website's interactive charts.

Run once (needs only the packages in requirements.txt, no dataset). It calls the same functions
with the same settings and seeds as threat_aware_qkd.ipynb, so the numbers are the notebook's
numbers; this script only SAVES them (one row per seed) so the website does not have to
re-simulate 20 seeds. Output: results/sweep_qber_vs_f.csv, sweep_qber_vs_noise.csv, sweep_s_vs_f.csv.
"""
import pandas as pd

from src.bb84 import run_bb84
from src.dual_protocol_outline import Channel, e91_run
from src.noise import build_noise_model

# Same values as the settings cell in threat_aware_qkd.ipynb
SEED, N_SEEDS = 42, 20
N_QUBITS, QBER_SAMPLE_SIZE, SHOTS, E91_ROUNDS = 2000, 300, 1, 2000
NOISE_LEVELS = [0.0, 0.02, 0.05, 0.10, 0.15, 0.20]
ATTACK_FRACTIONS = [0.0, 0.25, 0.5, 0.75, 1.0]
seeds = range(SEED, SEED + N_SEEDS)

rows = [{"f": f, "seed": s, "qber": run_bb84(N_QUBITS, QBER_SAMPLE_SIZE, SHOTS, s, build_noise_model(0.0), f).qber}
        for f in ATTACK_FRACTIONS for s in seeds]
pd.DataFrame(rows).to_csv("results/sweep_qber_vs_f.csv", index=False)

rows = [{"noise_level": n, "seed": s, "qber": run_bb84(N_QUBITS, QBER_SAMPLE_SIZE, SHOTS, s, build_noise_model(n), 0.0).qber}
        for n in NOISE_LEVELS for s in seeds]
pd.DataFrame(rows).to_csv("results/sweep_qber_vs_noise.csv", index=False)

rows = []
for f in ATTACK_FRACTIONS:
    for s in seeds:
        r = e91_run(Channel(0.0, f, s), E91_ROUNDS)
        rows.append({"f": f, "seed": s, "s": r.s, "s_se": r.s_se})
pd.DataFrame(rows).to_csv("results/sweep_s_vs_f.csv", index=False)
print("saved 3 files to results/")
