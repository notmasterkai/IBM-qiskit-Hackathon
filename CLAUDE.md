# CLAUDE.md

Instructions for Claude (Claude Code or any AI coding assistant) working in this repository. Read this whole file before writing or changing any code. These rules apply to every session.

---

## 1. Project in One Paragraph

**Threat-Aware Quantum-Secure Communication for Biomedical Networks**, built for Qiskit Fall Fest 2026 (IBM Qiskit), Track 2: Quantum Cryptography and Communication. A classical ML classifier trained on NSL-KDD estimates how dangerous the network looks (threat probability → Low / Medium / High). A Qiskit simulation of BB84 (with channel noise and an optional intercept-resend eavesdropper) produces a QBER. Decision rules, whose strictness depends on the threat level, turn the QBER into **Accept / Monitor / Reject**. Optional extension: an E91 (Bell / CHSH) protocol acts as an independent verifier, and a cross-check engine combines both verdicts and raises an **ANOMALY** flag when they disagree.

**Core idea:** the threat level changes how the quantum result is *interpreted* (the thresholds). It never changes the quantum physics or the simulation itself.

---

## 2. What This Project Does and Does Not Do

**Does:** decide whether a quantum-agreed key is safe to use, by combining network threat (ML) with channel disturbance (QBER, and optionally the Bell score S).

**Does not:**
- encrypt any data;
- check whether messages were altered;
- produce a final usable key (no error correction, no privacy amplification);
- run on real quantum hardware or real photons.

Never write code, comments, docs or demo text that suggests otherwise.

---

## 3. Who You Are Working With

- The team is **first-year students and beginners in Qiskit**: Lakshman AP (P2, BB84 core), Joel Alfred (P3, noise, eavesdropper, plots), Lavanya Loganathan (P1, classifier), Shriram Karthick VP (P4, decision logic, integration, docs, demo).
- The total build window is about **3.5 hours** during an overnight hackathon.
- They are coding with AI assistance and must be able to **explain every line** to judges.

Therefore:
- Write simple, readable code. Prefer clarity over cleverness.
- Comment the *why*, not just the *what*, especially for quantum steps.
- After each change, explain in plain language what you did and how to check it.
- Do not introduce advanced libraries, frameworks or patterns unless asked.
- Do not refactor working code that the task did not ask you to touch.

---

## 4. Golden Rules (Never Break These)

1. **Never invent numbers.** No made-up accuracies, QBER values, S values, F1 scores, run times or dataset sizes in code comments, docs, plots, print statements or the README. Only report what the code actually produced. Where a value is unknown, use `[TBD: ...]`.
2. **Never mark a feature as done unless it runs and passes its validation checks.** Features still marked **Planned** in §17 are not built.
3. **Never use `execute()`.** It was removed in Qiskit 1.0. Use `transpile(...)` and `backend.run(...)`.
4. **Always fix random seeds** (Python, NumPy, simulator) so results are reproducible.
5. **Never claim quantum advantage**, "first", "never done before" or "unbreakable". Novelty is the integration and the adaptive policy, "in the sources we reviewed".
6. **Never change threshold values, physics constants or decision tables** in this file without the team explicitly asking. If you think a value is wrong, say so and ask.
7. **Do one task at a time.** Work from `TASKS.md` in order. Do not build ahead.
8. **Run the validation checks** (§13) after any change to quantum code. If a check fails, stop and report it; do not tune code to force the expected number.
9. **Do not commit the dataset** or any large generated files.
10. **If something is unclear, ask** instead of guessing.

---

## 5. Tech Stack

| Tool | Use |
|---|---|
| Python 3.14.8 | Everything |
| `qiskit` (2.x) | Circuits, transpile |
| `qiskit-aer` | `AerSimulator`, noise models |
| `scikit-learn` | Preprocessing, logistic regression, random forest, metrics |
| `pandas` | Loading NSL-KDD |
| `numpy` | Random bits/bases, arrays |
| `matplotlib` | All plots |
| `scipy` | Only for the Clopper-Pearson intervals (`scipy.stats.beta`) |

Install:
```bash
pip install qiskit qiskit-aer scikit-learn pandas matplotlib
# for the confidence-interval verdicts (also pinned in requirements.txt):
pip install scipy
```

Do not add other dependencies without asking. Record the actual installed versions in the README when known.

---

## 6. Repository Layout

```
.
├── threat_aware_qkd.ipynb       # Main notebook: runs the full pipeline top to bottom
├── src/
│   ├── __init__.py
│   ├── classifier.py            # NSL-KDD loading, preprocessing, LogReg, Random Forest, threat bins
│   ├── bb84.py                  # BB84 circuits, eavesdropper, sifting, QBER estimation
│   ├── noise.py                 # Depolarizing noise model builder
│   └── decision.py              # Threshold tables and Accept / Monitor / Reject logic
├── data/
│   └── README.md                # How to download NSL-KDD; data files are NOT committed
├── results/                     # Saved plots (.png) and tables (.csv)
├── README.md
├── SKILLS.md
├── CLAUDE.md                    # This file
└── TASKS.md                     # Ordered build checklist
```

Optional extension (E91, built): `src/dual_protocol_outline.py` (simulation) with its rules in `decision.py` and unit tests in `tests/`.

Rules:
- Logic lives in `src/`. The notebook imports from `src/` and calls functions; it should not contain long logic blocks.
- The notebook must run **top to bottom** from a fresh kernel with no manual steps except downloading the dataset.
- Save every figure to `results/` with the filenames in §14.

---

## 7. Coding Style

- Small functions with one job each, type hints, and a short docstring stating inputs, outputs and units (for example "QBER as a fraction 0 to 1").
- Use `numpy.random.default_rng(seed)` for randomness; pass `rng` or `seed` into functions instead of using global random state.
- Represent QBER internally as a **fraction** (0.05), and display it as a percentage (5%) only in plots and printouts.
- Use clear names: `alice_bits`, `alice_bases`, `bob_bases`, `eve_fraction`, `noise_level`, `threat_level`.
- Bases: `0 = Z`, `1 = X`. Say so in a comment wherever they are created.
- No hard-coded magic numbers in functions: thresholds come from the tables in `decision.py`; experiment settings come from a config dict or dataclass at the top of the notebook.
- Optional: use `@dataclass` for settings such as the channel (noise level, eavesdropper fraction, seed).
- Print short, labelled outputs. No walls of text.

---

## 8. Module Specifications

### 8.1 `classifier.py` (P1)

- **Data:** NSL-KDD from Kaggle, placed in `data/`. File names: `KDDTrain+.txt` (train) and `KDDTest+.txt` (test). Never download or commit it automatically.
- **Preprocessing:**
  - encode categorical columns (`protocol_type`, `service`, `flag`); method: one-hot;
  - scale numeric features (fit the scaler on **training data only**, then apply to test);
  - binary label: `normal` → 0, every attack type → 1.
- **Models:** `LogisticRegression` (baseline) and `RandomForestClassifier`, both with `random_state` fixed.
- **Metrics on the test set:** accuracy, precision, recall, F1, confusion matrix. Report test numbers, not training numbers. The NSL-KDD test set contains attack types missing from training, so lower test scores are expected and normal.
- **Output:** threat probability = `predict_proba(...)[:, 1]` from the random forest.
- **Threat bins:** see §9.1.
- **Channel-level threat**: average random-forest probability over a window of `THREAT_WINDOW_SIZE` (100) consecutive test records, decided by the team.

### 8.2 `bb84.py` (P2, with P3 for Eve)

Steps:
1. Alice draws random bits and random bases (Z or X) with a seeded RNG.
2. Encode each bit into one qubit:

   | Bit | Z basis | X basis |
   |---|---|---|
   | 0 | \|0⟩ | \|+⟩ |
   | 1 | \|1⟩ | \|−⟩ |

   Bit 1 → apply `x`. X basis → then apply `h`.
3. **Channel:** the point where noise and Eve act (see §8.3 and below).
4. Bob draws random bases. X basis → apply `h` before measuring. Then measure.
5. **Sifting:** keep positions where Alice's basis equals Bob's basis.
6. **QBER estimation:** randomly sample a subset of sifted positions, compare bits, QBER = mismatches / sample size. The sampled bits are discarded (they are public). Sample size: 300 (`QBER_SAMPLE_SIZE`).
7. Return at least: QBER, number of sampled bits, number of mismatches, number of sifted bits, remaining raw key length.

**Eavesdropper (intercept-resend), attack fraction `f`:**
- For each qubit, Eve attacks with probability `f` (seeded).
- On attacked qubits, Eve picks a random basis, measures (mid-circuit measurement into her own classical bit), and resends the state matching her result in her basis. In circuit terms: if Eve's basis is X, apply `h`, `measure`, then `h` again; if Z, just `measure`. The measurement collapses the qubit, so the resent state is correct by construction.
- Expected: QBER ≈ 0.25 × f.

**Running circuits:**
- Use `AerSimulator`, `transpile(circuits, backend)`, `backend.run(circuits, shots=1, seed_simulator=SEED)` (or a justified alternative).
- **Batch** all circuits into one `run` call instead of looping `run` per qubit.
- **Bit ordering:** Qiskit classical bits are little-endian (bit 0 is the rightmost character of a counts key). If a circuit has two classical bits (Eve's and Bob's), parse keys carefully and comment how.
- Number of qubits per run: 2000. Shots per circuit: 1.

### 8.3 `noise.py` (P3)

- Build a `NoiseModel` with a depolarizing error from `qiskit_aer.noise` (`depolarizing_error`).
- **Important:** a qubit encoding bit 0 in the Z basis has **no gates**, so noise attached only to `x`/`h` would never touch it. Model the channel explicitly, for example by inserting an identity gate (`qc.id(0)`) as the "channel" step and attaching the depolarizing error to `id`. Then verify that `transpile` does not remove it (use `optimization_level=0` if needed) and that noise affects all four encodings. Document the chosen approach in a comment.
- Noise levels to sweep: 0, 0.02, 0.05, 0.10, 0.15, 0.20.
- Expected: QBER rises with noise strength even with no eavesdropper.

### 8.4 `decision.py` (P4)

- Store the threshold tables from §9 as plain data (dicts), not scattered `if` statements.
- `threat_level(p) -> "Low" | "Medium" | "High"`
- `decide_bb84(qber, level) -> "Accept" | "Monitor" | "Reject"`
- Comparisons follow §9.2 exactly, including the `<` / `>` conventions.
- Extensions: the pure decision rules live here: CI verdicts (§10, `clopper_pearson`, `qber_verdict`), E91 thresholds (§11, `E91_THRESHOLDS`, `e91_verdict`) and the cross-check matrix (§12, `CROSS_CHECK`, `cross_check`), all as plain lookup tables.

### 8.5 `dual_protocol_outline.py` (optional E91 extension; built)

File split (team decision): this file holds the **simulation** (`Channel`, `bb84_run`, `e91_run`, `measure`, and the top-level `decide` that combines everything). The **rules** (verdict functions, E91 thresholds, cross-check matrix) live in `decision.py`.

Functions:

| Function | Purpose |
|---|---|
| `Channel` | Dataclass: noise level, attack fraction f, seed; shared by both protocols |
| `bb84_run` | Runs BB84 on the channel; returns QBER, sample size, mismatches |
| `e91_run` | Runs the E91-style protocol; returns S and its standard error |
| Verdict functions | QBER or S (with uncertainty) → Pass / Marginal / Fail |
| Cross-check matrix | Two verdicts + threat level → Accept / Monitor / Reject + ANOMALY flag |
| `measure` | Helper to measure at a chosen basis or angle (via `ry` rotations) |
| `decide` | Top-level function combining everything into the final decision |

---

## 9. Decision Rules (Exact Values)

All values are **starting values and design choices to be tuned by the team**. Only 11% QBER, 25% QBER, S = 2.0 and S ≈ 2.83 are physics. Do not change them yourself.

### 9.1 Threat bins

| Level | Threat probability p |
|---|---|
| Low | p < 0.33 |
| Medium | 0.33 ≤ p ≤ 0.66 |
| High | p > 0.66 |

### 9.2 BB84 QBER thresholds

| Level | Accept if QBER < | Reject if QBER > | Otherwise |
|---|---|---|---|
| Low | 0.08 | 0.11 | Monitor |
| Medium | 0.05 | 0.11 | Monitor |
| High | 0.03 | 0.08 | Monitor |

Reference grid (use as a unit test):

| QBER | Low | Medium | High |
|---|---|---|---|
| 0.04 | Accept | Accept | Monitor |
| 0.06 | Accept | Monitor | Monitor |
| 0.09 | Monitor | Monitor | Reject |

### 9.3 Physics behind the values (for comments and explanations)

- Full intercept-resend → QBER ≈ 25%; fraction f → QBER ≈ 0.25 × f.
- Usable key fraction ≈ 1 − 2h(Q), where h is binary entropy; reaches zero near Q ≈ 11% (Shor and Preskill, asymptotic).
- 8%, 5% and 3% are design choices, not physical constants.

---

## 10. Confidence-Interval Verdicts (Implemented extension)

Each protocol returns **Pass / Marginal / Fail** instead of a single comparison:

| Verdict | QBER rule (95% Clopper-Pearson interval [lo, hi]) | S rule (S ± 2·SE) |
|---|---|---|
| Pass | `hi < accept_limit` | `S − 2·SE ≥ accept_limit` |
| Fail | `lo > reject_limit` | `S + 2·SE ≤ reject_limit` |
| Marginal | otherwise | otherwise |

Clopper-Pearson for k mismatches out of n sampled bits, α = 0.05:
- `lo = scipy.stats.beta.ppf(α/2, k, n − k + 1)`, with `lo = 0` when k = 0
- `hi = scipy.stats.beta.ppf(1 − α/2, k + 1, n − k)`, with `hi = 1` when k = n

S is a sum of four correlators; its standard error comes from the standard errors of the individual correlators (each estimated from its own number of rounds). Document the formula used in a comment.

---

## 11. E91 Bell Score Thresholds (Implemented extension)

| Level | Accept if S ≥ | Reject if S ≤ | Otherwise |
|---|---|---|---|
| Low | 2.4 | 2.0 | Monitor |
| Medium | 2.5 | 2.0 | Monitor |
| High | 2.6 | 2.2 | Monitor |

Physics: S ≤ 2 is the classical (local hidden-variable) bound; 2√2 ≈ 2.83 is the quantum maximum. Under intercept-resend with fraction f, S ≈ 2.83 × (1 − f/2). In this design the QBER rule triggers before S ≤ 2.

E91 implementation notes:
- Simplified "E91-style": a Bell pair (`h` then `cx`), four CHSH angle pairs for the S estimate, plus matched-setting key rounds.
- Measure at chosen angles using `ry` rotations before measurement. Choose the standard CHSH angles and **verify on an ideal channel that S comes out near 2.83** before trusting anything else. If it doesn't, the angles or rotation signs are wrong; fix them, never fudge.
- E91 is equivalent to BB84 for key security (Bennett, Brassard and Mermin 1992). It is a diagnostic, not a stronger key.

---

## 12. Cross-Check Matrix (Implemented extension)

| BB84 + E91 verdicts | Low | Medium | High | Flag |
|---|---|---|---|---|
| Pass + Pass | Accept | Accept | Accept | |
| Pass + Marginal (either order) | Accept | Monitor | Monitor | |
| Marginal + Marginal | Monitor | Monitor | Reject | |
| BB84 Pass + E91 Fail | Monitor | Monitor | Reject | ANOMALY |
| BB84 Fail + E91 Pass | Monitor | Reject | Reject | ANOMALY |
| Marginal + Fail (either order) | Monitor | Reject | Reject | |
| Fail + Fail | Reject | Reject | Reject | |

- **Monitor** means: rerun the failing protocol with more samples.
- An ANOMALY flag lists *possible* causes as hypotheses, never as proof.
- Both protocols share the same simulated channel, so their evidence is correlated. Disagreements are tested by injecting protocol-specific faults deliberately; say so wherever this is shown.
- Implement the matrix as a lookup table and unit-test every row.

---

## 13. Validation Checks (Run After Every Quantum Change)

| Check | Expected |
|---|---|
| No noise, no eavesdropper | QBER = 0 exactly. Anything else is a bug. |
| Full intercept-resend (f = 1), no noise | QBER ≈ 0.25 |
| Partial attack fraction f, no noise | QBER ≈ 0.25 × f |
| Noise only, increasing strength | QBER increases |
| Usable key fraction 1 − 2h(Q) | Reaches zero near Q ≈ 0.11 |
| Decision grid (§9.2) | All 9 cells match |
| E91 ideal channel (if built) | S near 2.83 |
| E91 with fraction f (if built) | S falls roughly as 2.83 × (1 − f/2) |

"≈" means within statistical error for the sample size used; tolerance (team decision): within 2 standard errors, SE = sqrt(p·(1−p)/n), where p is the expected QBER and n is the QBER sample size. Compute it in code (`qber_standard_error` in `src/bb84.py`); never hard-code it. When p = 0 the SE is 0, so the check is exact. Report the observed numbers exactly as produced. If a check fails, stop, report it, and debug. Never adjust code or seeds just to make a number match.

Add these as simple assert-style tests in the notebook or a `tests/` cell section.

---

## 14. Results and Plots

Save to `results/` with these names:

| File | Content |
|---|---|
| `qber_vs_eve_fraction.png` | QBER vs attack fraction f, with the theoretical 0.25 × f line |
| `qber_vs_noise.png` | QBER vs depolarizing noise strength |
| `confusion_matrix.png` | Random forest (and optionally LogReg) confusion matrix |
| `decision_map.png` | Threat level (rows) vs QBER (x-axis), coloured Accept / Monitor / Reject |
| `key_rate_curve.png` | Theoretical 1 − 2h(Q) vs Q |
| `metrics.csv` | Classifier metrics table |
| `scenarios.csv` | Scenario table: noise, f, threat level, QBER, decision |

Plot rules: axis labels with units, title, legend, QBER shown in %, error bars when multiple seeds are used (number of seeds: 20), consistent colours (Accept green, Monitor amber, Reject red). Never draw expected or fake data as if measured; theory lines must be labelled "theory".

After producing results, tell the team which `[TBD: result]` placeholders in README.md they can now fill in, and with which values from the output. Do not edit the README results yourself unless asked.

---

## 15. Workflow

1. Read `TASKS.md`. Pick the **next unchecked task** only.
2. Briefly state the plan (what files, what functions) before coding.
3. Implement it in `src/`, then wire it into the notebook.
4. Run it. Run the relevant validation checks.
5. Report: what changed, how to run it, the check outputs, and anything left `[TBD]`.
6. Tick the task in `TASKS.md` only if it runs and passes its checks.
7. Update the **Project Status** table in README.md (Planned → In progress → Implemented) only to match reality.
8. Suggest a short Git commit message, e.g. `bb84: add sifting and QBER estimation`.

Build order: classifier → BB84 → noise → eavesdropper → decision rules → integration → plots → demo. Extensions only after the core works, in this order: fixed vs adaptive comparison, confidence intervals, fake-backend noise (FakeBrisbane / FakeFez), per-attack-family results and feature importance; then E91, threshold-aware attacker, calibration check, timeline/interactive demo, man-in-the-middle authentication demo. Stretch (likely not in this hackathon): real final key, Bayesian decision rule.

**Time budget:** the core pipeline must work end to end first. If time is short, cut extensions, not validation checks.

---

## 16. Performance Limits

- Must run on a normal laptop in reasonable time (measured: about 5 minutes for the full notebook, including the E91 extension).
- Batch circuits; never call `backend.run` once per qubit in a loop.
- Keep qubit counts and sweep sizes modest; make them settings at the top of the notebook so the team can scale up or down.
- Classifier training must be fast; avoid large hyperparameter searches unless asked.

---

## 17. Feature Status (Source of Truth)

| Feature | Status |
|---|---|
| Core BB84 + noise + eavesdropper simulation | Implemented |
| NSL-KDD classifier (LogReg + Random Forest) | Implemented |
| Threat-aware decision rules | Implemented |
| E91 cross-verification layer | Implemented |
| Confidence-interval verdicts | Implemented |
| Fixed vs adaptive threshold comparison | Planned |
| Fake-backend noise, per-attack-family results, threshold-aware attacker, calibration, timeline demo | Planned |

Update this table together with README.md as work progresses.

---

## 18. Honest Limitations (Keep Consistent Everywhere)

- Simulation only; no real photons or hardware.
- No error correction or privacy amplification; we estimate whether a key is possible and do not produce a final key.
- NSL-KDD is general intrusion data (simulated traffic), not healthcare-specific.
- QBER alone cannot separate noise from an attacker; threat context sets the tolerance. A weak attacker below the accept limit may be accepted (e.g. f = 0.3 gives QBER ≈ 7.5%, accepted at Low threat).
- BB84 needs an authenticated classical channel; QKD complements post-quantum cryptography.
- If E91 is built: equivalent to BB84 for key security, so it is a diagnostic; S > 2 does not give device-independent security here; both protocols share the same simulated channel; disagreements come from injected faults; E91 is a simplified "E91-style" version.
- BB84, E91 and random forests are standard; ML for detecting attacks on QKD already exists. No quantum advantage is claimed.

---

## 19. Things You Must Never Do

- Use `execute()` or other removed Qiskit APIs.
- Hard-code an expected result (e.g. `qber = 0.25`) instead of computing it.
- Generate fake data, fake plots or placeholder numbers that look like real results.
- Fit the scaler or any preprocessing on the test set.
- Download or commit the dataset, or commit large result files without asking.
- Silently change thresholds, bins, physics constants or the decision tables.
- Build an extension before the core pipeline works.
- Add claims to README.md or slides that the code does not support.
- Write encryption or message-integrity code; it is out of scope.
- Rewrite large parts of the codebase when a small fix will do.

---

## 20. Definition of Done (Core Pipeline)

- The notebook runs top to bottom from a fresh kernel.
- Classifier trains and reports test-set metrics and a confusion matrix.
- BB84 passes the 0%, ≈25% and ≈0.25 × f checks.
- The noise sweep shows QBER rising with noise.
- Decision rules pass the 9-cell grid test.
- At least one end-to-end scenario goes from a network record → threat level → BB84 run → QBER → decision.
- All plots in §14 are saved in `results/`.
- README.md status table and results placeholders are ready for the team to fill with real outputs.