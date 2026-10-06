# TASKS.md

Ordered build checklist for **Threat-Aware Quantum-Secure Communication for Biomedical Networks** (Qiskit Fall Fest 2026, Track 2).

## How to Use This File

- Work **top to bottom**. Do one task at a time.
- Tell Claude: *"Do the next unchecked task in TASKS.md."*
- Tick a box `[x]` only when the task **runs** and its **Done when** checks pass.
- Never tick a task because the code "looks right". Run it.
- If a check fails, stop and fix it before moving on. Never tweak code or seeds to force an expected number.
- "Close to" / "≈" checks mean within 2 standard errors: SE = sqrt(p·(1−p)/n), p = expected QBER, n = QBER sample size. Computed in code, not hard-coded.
- After each task: update the Project Status table in README.md and CLAUDE.md §17 if a feature changed status, and make a Git commit.
- All rules, thresholds and file names come from **CLAUDE.md**. If this file and CLAUDE.md disagree, CLAUDE.md wins. Ask the team.

**Owners:** P1 classifier · P2 BB84 core · P3 noise, eavesdropper, sweeps and plots · P4 decision logic, integration, README, slides, demo. Names: P1 Lavanya Loganathan · P2 Lakshman AP · P3 Joel Alfred · P4 Shriram Karthick VP.

**Parallel work:** Phase 1 (P1) and Phases 2 to 4 (P2, P3) can run at the same time. Phase 5 (P4) can start once the function signatures are agreed. Everyone meets at Phase 6.

**Time budget:** about 3.5 hours total. Planned split per phase: [TBD: team to decide]. Rule: the core pipeline (Phases 0 to 7) must work before any extension is started.

---

## Phase 0: Setup (P4)

- [x] **0.1 Create the repository structure**
  - Create `src/` (with `__init__.py`, `classifier.py`, `bb84.py`, `noise.py`, `decision.py`), `data/`, `results/`, and the notebook `threat_aware_qkd.ipynb`.
  - Add `.gitignore` excluding `data/*` (except `data/README.md`), `__pycache__/`, `.ipynb_checkpoints/`.
  - **Done when:** the folder layout matches CLAUDE.md §6 and the empty notebook opens.

- [x] **0.2 Install and check dependencies**
  - `pip install qiskit qiskit-aer scikit-learn pandas matplotlib`
  - Print versions of qiskit, qiskit-aer, scikit-learn, pandas, matplotlib and Python.
  - **Done when:** all imports work and the versions are recorded in README.md (replace the `[TBD]` versions).

- [x] **0.3 Add a settings cell at the top of the notebook**
  - One place for: `SEED`, number of qubits per run, QBER sample size, shots, noise levels to sweep, attack fractions to sweep, number of seeds for error bars. Values: set (see the settings cell).
  - **Done when:** no other cell hard-codes these values.

- [x] **0.4 Download NSL-KDD and write `data/README.md`**
  - Download from Kaggle (https://www.kaggle.com/datasets/hassan06/nslkdd) into `data/` manually. Do not commit the files.
  - `data/README.md` explains where to get the data and the expected file names (`KDDTrain+.txt`, `KDDTest+.txt`).
  - **Done when:** the notebook can load the training and test files with pandas.

---

## Phase 1: Threat Classifier (P1)

- [x] **1.1 Load and inspect NSL-KDD**
  - Load train and test files with correct column names.
  - Print the number of rows, columns and label counts (real values from the data).
  - **Done when:** row counts are printed and copied into README.md (replace `[TBD: number]`).

- [x] **1.2 Preprocess**
  - Binary label: `normal` → 0, every attack → 1.
  - Encode categorical columns (`protocol_type`, `service`, `flag`). Method: one-hot.
  - Scale numeric features: fit on **train only**, apply to test.
  - Make sure train and test end up with the same columns in the same order.
  - **Done when:** `X_train`, `X_test`, `y_train`, `y_test` exist with matching feature counts and no missing values.

- [x] **1.3 Train logistic regression (baseline)**
  - Fixed `random_state`. Report test-set accuracy, precision, recall, F1 and confusion matrix.
  - **Done when:** metrics print without errors.

- [x] **1.4 Train random forest**
  - Fixed `random_state`. Same metrics on the test set.
  - **Done when:** metrics print and both models' results are saved to `results/metrics.csv`.

- [x] **1.5 Threat probability and threat levels**
  - Threat probability = random forest `predict_proba(...)[:, 1]`.
  - `threat_level(p)` in `decision.py`: Low if p < 0.33, Medium if 0.33 ≤ p ≤ 0.66, High if p > 0.66.
  - Channel threat level: average probability over a window of `THREAT_WINDOW_SIZE` (100) consecutive test records (team decision).
  - **Done when:** `threat_level(0.1) == "Low"`, `threat_level(0.5) == "Medium"`, `threat_level(0.9) == "High"`, and the distribution of threat levels on the test set is printed.

- [x] **1.6 Confusion matrix plot**
  - Save `results/confusion_matrix.png`.
  - **Done when:** the file exists and has a title and axis labels.

---

## Phase 2: BB84 Core (P2)

- [x] **2.1 Alice: random bits and bases**
  - Seeded `numpy.random.default_rng`. Bases: `0 = Z`, `1 = X`.
  - **Done when:** the same seed gives the same bits and bases twice in a row.

- [x] **2.2 Encode qubits**
  - One single-qubit circuit per bit: bit 1 → `x`; X basis → then `h`.
  - Leave a clearly marked **channel step** in each circuit for noise and Eve (see CLAUDE.md §8.2 and §8.3).
  - **Done when:** drawing four example circuits (bit 0/1 × basis Z/X) shows the right gates.

- [x] **2.3 Bob: random bases and measurement**
  - X basis → `h` before `measure`.
  - Run all circuits in **one batched** `backend.run(...)` call on `AerSimulator`, after `transpile`. Use `seed_simulator`. Never use `execute()`.
  - Parse results carefully (little-endian bit order).
  - **Done when:** Bob gets one result bit per qubit.

- [x] **2.4 Sifting**
  - Keep positions where Alice's basis equals Bob's basis.
  - **Done when:** about half the positions survive, and the printed fraction comes from the run.

- [x] **2.5 QBER estimation**
  - Randomly sample a subset of sifted positions (sample size from settings), count mismatches, QBER = mismatches / sample size. Discard sampled bits from the raw key.
  - Return QBER, sample size, mismatches, sifted count and remaining raw key length.
  - **Done when:** the function returns all five values.

- [x] **2.6 Validation check: ideal channel**
  - No noise, no eavesdropper.
  - **Done when:** QBER is exactly 0. If not, there is a bug: stop and fix it.

---

## Phase 3: Channel Noise (P3)

- [x] **3.1 Build the depolarizing noise model**
  - `NoiseModel` with `depolarizing_error` attached to the explicit channel step (e.g. an `id` gate), so noise affects **all four** encodings, including bit 0 in the Z basis.
  - Check that `transpile` keeps the channel step (use `optimization_level=0` if needed).
  - **Done when:** with a non-zero noise level, errors appear for all four encodings in a quick test.

- [x] **3.2 Noise sweep**
  - Run BB84 at each noise level from settings, no eavesdropper.
  - **Done when:** QBER increases with noise strength, and the values are printed as produced.

---

## Phase 4: Eavesdropper (P3)

- [x] **4.1 Intercept-resend with attack fraction f**
  - Each qubit is attacked with probability f (seeded).
  - Eve picks a random basis; X basis → `h`, `measure` (her own classical bit), `h`; Z basis → `measure`.
  - **Done when:** the circuits for attacked qubits show Eve's mid-circuit measurement.

- [x] **4.2 Validation check: full attack**
  - f = 1, no noise.
  - **Done when:** QBER is close to 0.25 (within statistical error for the sample size). Report the actual value.

- [x] **4.3 Validation check: partial attack sweep**
  - Sweep f over the values in settings, no noise.
  - **Done when:** QBER follows roughly 0.25 × f. Report actual values.

---

## Phase 5: Decision Rules (P4)

- [x] **5.1 Threshold tables**
  - In `decision.py`, store the BB84 QBER table from CLAUDE.md §9.2 as a dict. Do not change the values.
  - **Done when:** the table prints and matches CLAUDE.md exactly.

- [x] **5.2 `decide_bb84(qber, level)`**
  - Accept if QBER < accept limit; Reject if QBER > reject limit; otherwise Monitor.
  - **Done when:** the 9-cell grid test passes:

    | QBER | Low | Medium | High |
    |---|---|---|---|
    | 0.04 | Accept | Accept | Monitor |
    | 0.06 | Accept | Monitor | Monitor |
    | 0.09 | Monitor | Monitor | Reject |

---

## Phase 6: Integration (P4, everyone)

- [x] **6.1 End-to-end function**
  - One function that takes a threat level (from the classifier), a noise level and an attack fraction f, runs BB84, and returns QBER and the decision.
  - **Done when:** one network record → threat probability → threat level → BB84 run → QBER → decision works and prints each step.

- [x] **6.2 Scenario table**
  - Run a set of scenarios (combinations of threat level, noise level and f; chosen by the team: [TBD]).
  - **Team decision (after Phase 1):** build each scenario's threat window from *chosen test traffic* (mostly normal, mixed, attack-heavy), then report the threat level each window actually gets. Do not change the bins or rig the data. If no window reaches High, say so honestly. (Test-set windows taken in file order were 211 Medium and 14 Low, no High.)
  - Save `results/scenarios.csv` with columns: scenario, noise level, f, threat level, QBER, decision.
  - **Done when:** the CSV exists and every value comes from an actual run.

- [x] **6.3 Fresh-kernel run**
  - Restart the kernel and run the notebook top to bottom.
  - **Done when:** it completes with no errors and no manual steps.

---

## Phase 7: Results and Plots (P3, P4)

- [x] **7.1 `results/qber_vs_eve_fraction.png`**: measured QBER vs f, with the labelled theory line 0.25 × f.
- [x] **7.2 `results/qber_vs_noise.png`**: measured QBER vs noise strength.
- [x] **7.3 `results/decision_map.png`**: threat level (rows) vs QBER (x-axis), coloured Accept green / Monitor amber / Reject red.
- [x] **7.4 `results/key_rate_curve.png`**: theory curve 1 − 2h(Q), labelled "theory", reaching zero near 11%.
- [x] **7.5 Error bars from multiple seeds**: repeat the QBER sweeps over the number of seeds in settings; add error bars to 7.1 and 7.2.
  - **Done when (all of 7):** every plot has a title, axis labels with units, a legend where needed, and QBER shown in %. No expected or fake data drawn as measured.

---

## Phase 8: Documentation and Demo (P4, everyone)

- [x] **8.1 Fill README.md placeholders**
  - Replace `[TBD: result]` entries with values from the actual outputs: classifier metrics, validation checks, scenario table, plot images.
  - Update the Project Status table and the Track 2 task coverage table (Planned → Implemented where true).
  - **Done when:** every remaining `[TBD]` in README.md is either filled with a real value or clearly still unknown.

- [x] **8.2 Update SKILLS.md**
  - Change rows from Planned/learning to Studied where the skill was actually used; adjust levels honestly. Fill in the per-member section.
  - **Done when:** SKILLS.md matches what was really built.

- [x] **8.3 Update CLAUDE.md §17 status table** to match README.md.

- [ ] **8.4 Demo script**
  - A short walkthrough: one Low-threat scenario accepted, one High-threat scenario at the same QBER not accepted, one full-attack scenario rejected. Use real outputs from Phase 6.
  - Everyone can explain the 0% / 25% / 11% numbers aloud.
  - **Done when:** the demo runs live from the notebook in [TBD: minutes].

- [ ] **8.5 Final check against the hackathon deliverables**
  - Working code / notebook · README / documentation · results and visualizations · classical comparison · short presentation / demo.
  - **Done when:** each deliverable exists and is linked from README.md.

---

## Extensions (Only After Phases 0 to 8 Are Done)

Do these in order. Mark each feature's status in README.md and CLAUDE.md as you go.

### Cheap

- [ ] **E1 Fixed vs adaptive threshold comparison**
  - Run the same scenarios through one fixed threshold ([TBD: value]) and through the adaptive thresholds. Count false accepts (attacked channel accepted) and false rejects (honest channel rejected).
  - **Done when:** a comparison table with real counts is saved and added to README.md.

- [x] **E2 Confidence-interval verdicts**
  - `pip install scipy`. Clopper-Pearson 95% interval for QBER; Pass / Marginal / Fail rules from CLAUDE.md §10.
  - **Done when:** unit tests cover k = 0, k = n, a clear Pass, a clear Fail and a Marginal case.

- [ ] **E3 Fake-backend noise (FakeBrisbane / FakeFez)**
  - Run BB84 with a realistic hardware-like noise model and compare QBER with the depolarizing model.
  - **Done when:** results are reported as produced, with a note that this is still simulation.

- [ ] **E4 Per-attack-family results and feature importance**
  - Classifier performance per NSL-KDD attack family; random forest feature importance plot.
  - **Done when:** the table and plot are saved to `results/`.

### Moderate

- [x] **E5 E91 cross-verification** (CLAUDE.md §8.5, §11, §12)
  - Build in `src/dual_protocol_outline.py` (simulation; the rules are in `src/decision.py`): `Channel`, `bb84_run`, `e91_run`, verdict functions, cross-check matrix, `measure`, `decide`.
  - First check: ideal channel gives S near 2.83. Then S falls roughly as 2.83 × (1 − f/2).
  - Unit-test every row of the cross-check matrix, including both ANOMALY rows.
  - **Done when:** all checks pass and README.md limitations for E91 are kept.

- [ ] **E6 Threshold-aware attacker**: an eavesdropper who chooses f to keep QBER just below the accept limit; report how often they are accepted.
- [ ] **E7 Calibration check**: check whether the random forest's probabilities are well calibrated, and what that means for the threat bins.
- [ ] **E8 Timeline and interactive demo**: show decisions changing over a sequence of scenarios.
- [ ] **E9 Man-in-the-middle authentication demo**: show why BB84 needs an authenticated classical channel.

### Stretch (Likely Beyond This Hackathon)

- [ ] **E10 Real final key**: error correction and privacy amplification.
- [ ] **E11 Bayesian decision rule.**

---

## Before Submitting

- [ ] Notebook runs top to bottom from a fresh kernel.
- [ ] All validation checks pass and the real values are in README.md.
- [ ] No invented numbers anywhere (search all files for numbers you cannot trace to an output).
- [ ] No `execute()` anywhere in the code.
- [ ] Dataset not committed.
- [ ] README.md, SKILLS.md and CLAUDE.md status tables agree with each other.
- [ ] AI-assistance statement in README.md is accurate.
- [ ] Final Git commit pushed; repository link added to README.md.