# SKILLS.md

**Project:** Threat-Aware Quantum-Secure Communication for Biomedical Networks
**Event:** Qiskit Fall Fest 2026, Overnight Quantum Computing Hackathon (IBM Qiskit), Track 2: Quantum Cryptography and Communication
**Team:** Daily Limit Reached (Lakshman AP, Joel Alfred, Lavanya Loganathan, Shriram Karthick VP)

This document lists the technical skills, concepts and tools our team used and is still learning in this project. We are first-year students and beginners in Qiskit. We built the prototype with AI-assisted coding (Claude Code and Claude AI).

> **Status:** The core pipeline is built. **Studied** now means we learned the concept and used it in the prototype or in our design; the prototype was built with AI help, so levels are conservative. **Planned/learning** marks skills for extensions we did not build (fake backends, calibration, per-attack-family results). The E91 / CHSH and confidence-interval skills were used in the E91 extension. The levels below are an honest self-assessment, not a claim of expertise.

---

## How to Read This Document

**Status column:**

| Status | Meaning |
|---|---|
| **Studied** | We learned this concept during the design phase and used it in our design, slides or reasoning. |
| **Planned/learning** | We plan to use this when building the prototype or an extension. It has not been used in code yet. |

**Level column:**

| Level | Meaning |
|---|---|
| **Beginner** | We met this for the first time in this project or understand it at a basic level. We could explain the idea but would need help to apply it. |
| **Working** | We understand it well enough to explain it and work through it ourselves, for example the 25% intercept-resend argument by hand. We could apply it on a similar problem with reference material. |
| **Comfortable** | We have used it before this project and could apply it independently. |

---

## 1. Quantum Computing Concepts

| Skill / Concept | What we did or plan to do with it in this project | Status | Level |
|---|---|---|---|
| Qubits | Designed BB84 so that each key bit is carried by one qubit in a single-qubit circuit. | Studied | Working |
| Superposition | Used the \|+⟩ and \|−⟩ states (X basis) in our design so that measuring in the wrong basis gives a random result. | Studied | Working |
| Measurement and collapse | Used the fact that measuring gives a plain 0 or 1 and changes the state to explain why an eavesdropper leaves errors. | Studied | Working |
| Bases (Z and X) | Designed random basis choices for Alice and Bob, with sifting keeping only positions where the bases match. | Studied | Working |
| No-cloning | Used to explain why Eve cannot copy qubits and must measure (and disturb) the originals. | Studied | Beginner |
| Noise | Ran a depolarizing noise sweep and saw QBER rise with noise (about noise level / 2). | Studied | Working |
| QBER (Quantum Bit Error Rate) | Designed QBER, estimated from a sample of sifted bits, as the main input to the Accept / Monitor / Reject decision. | Studied | Working |
| BB84 protocol | Designed the full flow: random bits and bases, encoding, measurement, sifting and QBER estimation, plus an intercept-resend eavesdropper with attack fraction f. | Studied | Working |
| Bell states and entanglement | Learned that BB84 does not need entanglement but E91 does, and built Bell pairs (`h` then `cx`) in the E91 extension, with Alice keeping one qubit and the other travelling to Bob. | Studied | Beginner |
| CHSH inequality and the Bell score S | Learned that S ≤ 2 is the classical bound and 2√2 ≈ 2.83 is the quantum maximum, computed S from four correlators, and saw it fall as 2.83 × (1 − f/2) under intercept-resend. | Studied | Beginner |
| BBM92 equivalence (E91 vs BB84) | Learned that E91 is equivalent to BB84 for key security (Bennett, Brassard and Mermin 1992), so E91 is an independent diagnostic, not a stronger key. | Studied | Beginner |

**Related ideas we also learned:**

| Concept | What we did or plan to do with it in this project | Status | Level |
|---|---|---|---|
| Intercept-resend attack | Worked out why full interception gives about 25% QBER (½ × ½) and about 0.25 × f for a partial attack, then checked it in the simulation (25.47% at f = 1 over 20 seeds). | Studied | Working |
| Usable key fraction 1 − 2h(Q) | Learned that the usable key fraction reaches zero near 11% QBER (Shor and Preskill), used this as our upper Reject threshold, and plotted the theory curve (first zero at Q = 11.01%). | Studied | Beginner |
| Error correction and privacy amplification | Learned what these steps do in real QKD and why we only estimate key feasibility instead of producing a final key. Listed as stretch future work. | Studied | Beginner |

---

## 2. Qiskit Skills

| Skill | What we did or plan to do with it in this project | Status | Level |
|---|---|---|---|
| `QuantumCircuit` | Built single-qubit BB84 circuits using the X gate (to encode bit 1), the H gate (to switch to or measure in the X basis) and measurement. | Studied | Beginner |
| `AerSimulator` | Ran all circuits on the Qiskit Aer simulator, with and without noise. | Studied | Beginner |
| `transpile` and `.run()` | Used the Qiskit 2.x workflow of transpiling circuits and calling `backend.run(...)`, not the removed `execute()`. | Studied | Beginner |
| Building a noise model with depolarizing errors | Created a `NoiseModel`, attached a depolarizing error to the channel gate, and swept its strength to produce QBER vs channel noise. | Studied | Beginner |
| Mid-circuit measurement | Modelled the eavesdropper by measuring the qubit in the middle of the circuit (Eve's measurement) before Bob's final measurement. | Studied | Beginner |
| Measuring at chosen angles with `ry` rotations | Rotated qubits with `ry(−angle)` before a Z measurement to measure at the CHSH angles, and checked the rotation convention numerically. | Studied | Beginner |
| Batching circuits | Ran all circuits of a BB84 round together in one job instead of one at a time. | Studied | Beginner |
| Shots | Set one shot per circuit (each qubit is sent once) and read the result bit from the counts. | Studied | Beginner |
| Seeds | Fixed random seeds (for bits, bases and the simulator) so runs are reproducible, and used 20 different seeds for error bars. | Studied | Beginner |
| Bit ordering | Learned that Qiskit orders classical bits little-endian (rightmost character is classical bit 0) and used it to read Bob's bit and Eve's bit from the two-bit counts keys. | Studied | Working |
| Fake backends (FakeBrisbane / FakeFez), optional | Plan to try realistic hardware-like noise from Qiskit fake backends as a cheap future-work extension. | Planned/learning | Beginner |

---

## 3. Machine Learning Skills

| Skill | What we did or plan to do with it in this project | Status | Level |
|---|---|---|---|
| Data preprocessing | Loaded NSL-KDD and converted the multi-class attack labels into a binary normal vs attack label. | Studied | Beginner |
| Encoding and scaling | One-hot encoded the categorical columns (`protocol_type`, `service`, `flag`) and scaled numeric features, fitting the scaler on training data only. | Studied | Beginner |
| Logistic regression | Trained a logistic regression classifier as the simple classical baseline. | Studied | Beginner |
| Random forest | Trained a random forest classifier and used its predicted probabilities as the threat probability. | Studied | Beginner |
| Evaluation metrics | Computed accuracy, precision, recall, F1 and the confusion matrix on the test set, and used them to explain why test scores are lower (unseen attack types) and why recall caps the window threat level. | Studied | Working |
| Probability calibration | Learned that predicted probabilities are not automatically well calibrated, which matters because we bin them into Low / Medium / High; a calibration check is planned future work. | Planned/learning | Beginner |
| Per-attack-family results and feature importance | Plan to break results down by attack family and look at which features the random forest relies on most. | Planned/learning | Beginner |

---

## 4. Statistics Skills

| Skill | What we did or plan to do with it in this project | Status | Level |
|---|---|---|---|
| Finite-sample uncertainty | Learned that QBER and S are estimated from a limited sample, so they have statistical error; a larger sample gives a tighter estimate but leaves fewer bits for the key, which is one reason the Monitor zone exists. | Studied | Beginner |
| Confidence intervals (Clopper-Pearson) | Put a 95% Clopper-Pearson interval around QBER and gave Pass / Marginal / Fail verdicts depending on where the interval falls relative to the thresholds, with unit tests for k = 0 and k = n. | Studied | Beginner |
| Standard error of a sum of correlators | Estimated each correlator's standard error as sqrt((1 − E²) / n), added the four variances to get the standard error of S, and used S ± 2 standard errors for the E91 verdict. | Studied | Beginner |
| False-accept and false-reject rates | Defined our success metrics as false accepts (an attacked channel accepted) and false rejects (an honest channel rejected); plan to count them in the fixed vs adaptive comparison. | Studied | Beginner |

---

## 5. Software and Workflow Skills

| Skill | What we did or plan to do with it in this project | Status | Level |
|---|---|---|---|
| Jupyter notebooks | Built the full pipeline as a notebook that runs top to bottom from a fresh kernel. | Studied | Beginner |
| Structuring a multi-module pipeline | Planned the code layout: separate modules for the classifier, BB84, noise and decision logic in `src/`, joined together in one notebook. | Studied | Beginner |
| Dataclasses | Used a Python dataclass for the BB84 run result. (Holding the channel settings in a dataclass is not done.) | Studied | Beginner |
| `scipy.stats` | Used `scipy.stats.beta` to compute the Clopper-Pearson intervals. | Studied | Beginner |
| Reproducible seeds | Fixed seeds for NumPy and the simulator, used 20 different seeds for error bars, and kept the notebook runnable in order. | Studied | Working |
| Plotting (matplotlib) | Produced QBER vs eavesdropping fraction, QBER vs noise (with error bars over 20 seeds), confusion matrix, decision map and usable key fraction plots. | Studied | Beginner |
| Git | Used Git locally to commit each phase. Pushing to GitHub: [TBD: confirm]. | Studied | Beginner |
| README writing | Wrote technical documentation explaining the design, decision rules, limitations and plan. | Studied | Beginner |
| Teamwork | Split the work into four roles (classifier, BB84 core, noise and eavesdropper, decision logic and integration) and prepared the Review 1 deck together. | Studied | Working |
| AI-assisted coding | Used Claude Code and Claude AI to plan and write the code and documentation, and checked the results against known theory (0% / 25% / 11%). | Studied | Beginner |

---

## 6. Security Concepts

| Concept | What we did or plan to do with it in this project | Status | Level |
|---|---|---|---|
| Key distribution vs encryption | Learned that our project decides whether a quantum-agreed key is safe to use; it does not encrypt data or check whether messages were altered. | Studied | Working |
| RSA / ECC and Shor's algorithm | Learned that RSA and ECC rely on hard maths problems that Shor's algorithm could solve on a large future quantum computer, and used this as the motivation for the project. | Studied | Beginner |
| Harvest now, decrypt later | Used this idea to explain why long-lived healthcare data needs protection today, before large quantum computers exist. | Studied | Working |
| Authenticated classical channels | Learned that BB84 needs an authenticated classical channel for comparing bases and the QBER sample; listed as a limitation, with a man-in-the-middle demo as future work. | Studied | Beginner |
| Threat modelling | Defined our attacker (an intercept-resend eavesdropper with attack fraction f) and designed the Accept / Monitor / Reject rules around false accepts and false rejects; a threshold-aware attacker is planned future work. | Studied | Beginner |
| Attack-vs-noise ambiguity | Learned that QBER alone cannot separate channel noise from an attacker, which is why our design uses the threat level to set how much error is tolerated. | Studied | Working |
| QKD vs post-quantum cryptography | Learned that QKD complements post-quantum cryptography rather than replacing it. | Studied | Beginner |
| Literature review and honest novelty claims | Reviewed sources on ML for QKD and QKD in healthcare, and worded our contribution carefully: BB84, E91 and random forests are standard, and we do not claim to be first. | Studied | Beginner |

---

## 7. Per-Member Skills

### Lakshman AP
- **Role:** P2 (BB84 core)
- **Main skills used:** [TBD]
- **New skills learned:** [TBD]
- **Self-assessed level in main area:** [TBD: Beginner / Working / Comfortable]
- **What I would learn next:** [TBD]

### Joel Alfred
- **Role:** P3 (noise, eavesdropper, plots)
- **Main skills used:** [TBD]
- **New skills learned:** [TBD]
- **Self-assessed level in main area:** [TBD: Beginner / Working / Comfortable]
- **What I would learn next:** [TBD]

### Lavanya Loganathan
- **Role:** P1 (classifier)
- **Main skills used:** [TBD]
- **New skills learned:** [TBD]
- **Self-assessed level in main area:** [TBD: Beginner / Working / Comfortable]
- **What I would learn next:** [TBD]

### Shriram Karthick VP
- **Role:** P4 (decision logic, integration, docs, demo)
- **Main skills used:** [TBD]
- **New skills learned:** [TBD]
- **Self-assessed level in main area:** [TBD: Beginner / Working / Comfortable]
- **What I would learn next:** [TBD]

**Role reference:**

| Role | Responsibility |
|---|---|
| P1 | NSL-KDD preprocessing and classical classifier |
| P2 | BB84 core in Qiskit |
| P3 | Noise model, eavesdropper, QBER sweeps and plots |
| P4 | Decision logic, integration, README, slides, demo |

---

## 8. Skills We Want to Build Next

These follow the future-work plan in the README:

- Running circuits with realistic noise from fake backends, and later on real IBM Quantum hardware.
- Probability calibration and threshold tuning with proper validation data.
- Implementing error correction and privacy amplification for a real final key.
- Bayesian decision rules.
- Post-quantum cryptography and how it can work alongside QKD.