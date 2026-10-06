# Demo walkthrough

**Project:** Threat-Aware Quantum-Secure Communication for Biomedical Networks (Team Daily Limit Reached)

Every number below comes from `threat_aware_qkd.ipynb`. It is a simulation: no real photons, no encryption, no final key.

**Before the demo:** run the whole notebook once (about 5 minutes on a laptop) so the outputs are on screen. Then scroll to the cells named below. Talk time for the demo: [TBD: rehearse and fill in].

## Demo on the website (recommended)

Start it with `streamlit run app.py` (see the README) and open http://localhost:8501. The Live demo page runs a real BB84 simulation each time you press **Run BB84 simulation** (about half a second). With "Real 100-record window" chosen as the threat source and the default seed 42, the results below are exactly the ones in our notebook's scenario table:

| Step | Live demo settings | What appears |
|---|---|---|
| Clean accepted | window *mostly normal (average 0.099)*, noise 0, f = 0 | Low, QBER 0.00%, **Accept** |
| Same QBER, different decision | noise 0.10, f = 0 with window *mostly normal* | Low, QBER 5.00%, **Accept** |
| | same settings with window *mixed (average 0.337)* | Medium, QBER 5.00%, **Monitor** |
| Full Eve rejected | any window, noise 0, f = 1 | QBER 26.00%, **Reject** |
| Weak Eve limitation | window *mostly normal*, noise 0, f = 0.3 | QBER 9.33%, **Monitor**: this is one run; try other seeds to see it wobble (our 20-seed average was 7.60%, which Low would Accept) |

Then open the **Results** page for the plots and tables (the what-if table is marked hypothetical) and the **Limitations** page. The sections below give the notebook version and the words to say.

---

## 1. The idea (say this first)

> "A classifier looks at network traffic and says how dangerous it looks: Low, Medium or High. A simulated quantum key exchange (BB84) measures how disturbed the channel was, called the QBER. The threat level does not change the physics. It only changes how strict we are when we read the QBER: Accept, Monitor or Reject."

Show the decision map (`results/decision_map.png`): for Low, Accept below 8%, Reject above 11%; for Medium, Accept below 5%, Reject above 11%; for High, Accept below 3%, Reject above 8%. Everything in between is Monitor.

---

## 2. Clean channel is accepted

Notebook cell: **6.2 scenario table**.

- Scenario `mostly normal + clean`: QBER **0.00%** → threat level Low → **Accept**.
- The same QBER of 0.00% is also Accepted at Medium (the `mixed` and `attack-heavy` windows).

> "No noise and no spy means Alice and Bob always agree, so the error rate is exactly zero. We tested this in 20 different random seeds and got 0 errors every time."

---

## 3. Same QBER, different decision (the main point)

Notebook cells: **6.1** and **6.2**.

**Two real network records on the same noisy channel (noise 0.10, no eavesdropper), QBER 5.0% for both:**

| Record | Threat probability | Level | Decision |
|---|---|---|---|
| real normal record (test row 2) | 0.000 | Low | **Accept** |
| real attack record (test row 0) | 1.000 | High | **Monitor** |

**Same result in the scenario table (noisy channel, QBER 5.00%):**

| Window | Avg threat probability | Level | Decision |
|---|---|---|---|
| mostly normal | 0.099 | Low | **Accept** |
| mixed | 0.337 | Medium | **Monitor** |
| attack-heavy | 0.545 | Medium | **Monitor** |

> "The quantum result is identical, 5% errors. On quiet traffic we accept the key. On hostile-looking traffic we do not trust it yet. Only the network threat changed."

---

## 4. Full eavesdropper is rejected

Notebook cell: **6.2 scenario table**.

- Scenario `full Eve` (Eve intercepts every qubit): QBER **26.00%** → **Reject** in all three windows.
- Over 20 seeds, the mean QBER at f = 1 was **25.47%** (plot: `results/qber_vs_eve_fraction.png`).

---

## 5. The honest limitation: a weak eavesdropper

Notebook cells: **6.2 scenario table** and **Weak Eve over 20 seeds**.

- Weak Eve (f = 0.3): the seed-42 run gave **9.33%** → **Monitor**.
- But that is one run. Averaged over 20 seeds the QBER was **7.60%** (theory 7.5%), and 7.60% would be **Accepted at Low threat**. Of the 20 single runs, 14 would be Accepted and 6 Monitored at Low.

> "QBER alone cannot tell noise from a weak attacker. The threat level helps, but a weak spy on a quiet network can slip under the limit. We report this as a limitation, not a success."

Also mention: the classifier's recall is 0.6094, so even a window with 90% real attacks only reached an average probability of 0.545 (Medium). **No real window reached High.** The table "what-if at High" in the README is hypothetical and is labelled that way.

---

## 6. The three numbers to explain aloud

**0%: the clean channel.**
> "If nobody disturbs the qubits, then whenever Alice and Bob happen to use the same basis, Bob reads exactly Alice's bit. So the error rate is zero. If we ever see anything else on a clean channel, our code has a bug."

**25%: a full eavesdropper.**
> "Eve has to measure each qubit, and she does not know which basis Alice used. Half the time she guesses right, and nothing goes wrong. Half the time she guesses wrong, and her measurement scrambles the qubit, so Bob then gets the wrong bit half of the time. Half times half is 25%. If she spies on only a fraction f of the qubits, we expect 0.25 × f." Our measured mean at f = 1 was 25.47%.

**11%: where the key becomes useless.**
> "A real system would shrink the key to throw away what Eve might know. The usable fraction is about 1 − 2h(Q), where h is the binary entropy. In our plot (`results/key_rate_curve.png`) this first reaches zero at 11.01%. Above that, in theory, no secret key can be made. 11% is physics. Our other limits, 8%, 5% and 3%, are our own design choices."

---

## 7. Optional: the E91 cross-check

**Idea (say this):**
> "BB84 gives one number, the QBER. We added a second, independent check on the same simulated channel: E91, which uses entangled pairs and gives a Bell score S. S is about 2.83 on a perfect channel and falls as an eavesdropper interferes; 2 is the classical bound. Each protocol gets a verdict, Pass, Marginal or Fail, from a 95% interval, and a small table combines both verdicts with the threat level. If one protocol Passes and the other Fails, we raise an ANOMALY flag."

**On the website:** open the **E91 cross-check** page, set the sliders, press **Run BB84 + E91** (about 1 second). Seed 42, from `results/crosscheck_scenarios.csv` and `results/crosscheck_injected_faults.csv`:

| Step | Settings | What appears |
|---|---|---|
| Clean accepted | Low threat, noise 0, f = 0, no fault | BB84 **Pass** (QBER 0.00%, 0 of 300); E91 **Pass** (S = 2.743 ± 0.074); decision **Accept** |
| Full Eve rejected | any threat level, noise 0, f = 1, no fault | BB84 **Fail** (QBER 26.00%); E91 **Fail** (S = 1.324 ± 0.095); decision **Reject** |
| ANOMALY, demonstration 1 | Low threat, choose **INJECTED fault in E91 only** | BB84 **Pass** (QBER 0.00%); E91 **Fail** (S = 1.496 ± 0.094); decision **Monitor**; red **ANOMALY** banner |
| ANOMALY, demonstration 2 | Low threat, choose **INJECTED fault in BB84 only** | BB84 **Fail** (QBER 20.67%); E91 **Pass** (S = 2.743 ± 0.074); decision **Monitor** (Reject at Medium); red **ANOMALY** banner |

**Say clearly that the two ANOMALY cases are INJECTED, ARTIFICIAL faults, not real attacks.** Each one adds extra noise to one protocol only (BB84-only: noise 0.40; E91-only: noise 0.50), so the other protocol still sees the honest channel. In a real system both protocols see the same channel, so in all 12 of our real cases (clean, noisy, weak Eve, full Eve at Low, Medium and High) no ANOMALY appeared. An ANOMALY only says the two protocols disagree; any cause is a hypothesis, not proof.

**The honest finding: dual mode is more conservative.**
> "With 95% intervals at our sample sizes, using both protocols is stricter than BB84 alone. On our 12 real cases it was stricter in 3, the same in 9, and never more lenient. For example, a noisy channel with a 5.00% QBER is Accepted at Low threat by BB84 alone, but only Monitored in dual mode, and a clean channel at High threat needs a rerun because S − 2 standard errors is 2.595, just under the 2.6 limit. Monitor means: rerun with more samples. With four times the samples, the clean channel at High gave S = 2.801 ± 0.036 and was Accepted. So we trade more reruns for fewer risky accepts."

(Source: `results/crosscheck_vs_bb84_only.csv`; one seed only, so treat the counts as an illustration. The 20-seed result for S vs f is in `results/s_vs_eve_fraction.png`: mean S = 2.816, 2.473, 2.115, 1.761 and 1.399 at f = 0, 0.25, 0.5, 0.75 and 1, following 2.83 × (1 − f/2).)

**E91 limitations to mention:** E91 is equivalent to BB84 for key security, so it is a diagnostic, not a stronger key; S above 2 does not give device-independent security here; both protocols share the same simulated channel, so their evidence is correlated; ours is a simplified "E91-style" version.

---

## 8. Things we do not claim

- No encryption, no message-integrity check, no final key (no error correction or privacy amplification).
- Simulation only. NSL-KDD is general intrusion data, not healthcare traffic.
- BB84 needs an authenticated classical channel.
- No quantum advantage.
