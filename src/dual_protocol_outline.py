"""E91-style protocol (Bell pairs + CHSH) on the same simulated channel as BB84.

Optional extension, simulation only. E91 is equivalent to BB84 for key security, so it is an
independent *diagnostic* here, not a stronger key. Rules (verdicts, thresholds, cross-check
matrix) live in decision.py; this file only simulates.

Where the channel acts: Alice keeps qubit 0 of every Bell pair. Qubit 1 is the one sent to Bob,
so Eve (intercept-resend) and the depolarizing noise act ONLY on qubit 1, in the same
"channel step" used in BB84: first Eve (if she attacks), then the identity gate `id` that
carries the depolarizing error. Alice's qubit never travels, so it is never touched.
"""
from dataclasses import dataclass

import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

from src.bb84 import BB84Result, eve_choices, run_bb84
from src.noise import build_noise_model

# ---- CHSH measurement angles (radians). Measuring at angle t means measuring cos(t)*Z + sin(t)*X.
ALICE_ANGLES = (0.0, np.pi / 2)             # a0, a1
BOB_ANGLES = (np.pi / 4, -np.pi / 4)        # b0, b1
# S = E(a0,b0) + E(a0,b1) + E(a1,b0) - E(a1,b1); the last correlator is subtracted.
CHSH_PAIRS = [(0, 0, +1), (0, 1, +1), (1, 0, +1), (1, 1, -1)]   # (alice index, bob index, sign in S)
CHSH_NAMES = ["E(a0,b0)", "E(a0,b1)", "E(a1,b0)", "E(a1,b1)"]
KEY_ANGLE = 0.0   # key rounds: both measure at the same angle (matched setting, Z basis)


@dataclass
class Channel:
    """The simulated channel, shared by BB84 and E91."""
    noise_level: float = 0.0     # depolarizing error probability, 0 to 1
    eve_fraction: float = 0.0    # share of qubits Eve intercepts, 0 to 1
    seed: int = 42


@dataclass
class E91Result:
    """Outcome of one E91-style run."""
    s: float                     # CHSH score S
    s_se: float                  # standard error of S
    correlators: dict            # name -> (E, standard error, number of rounds)
    key_rounds: int              # rounds with matched settings
    key_mismatches: int          # matched rounds where Alice and Bob disagreed


def ideal_correlator(alice_angle: float, bob_angle: float) -> float:
    """Theory for the Bell state (|00> + |11>)/sqrt(2): E(a, b) = cos(a - b)."""
    return float(np.cos(alice_angle - bob_angle))


def measure(qc: QuantumCircuit, qubit: int, clbit: int, angle: float) -> None:
    """Measure `qubit` at `angle` (observable cos(angle)*Z + sin(angle)*X) into `clbit`.

    The simulator can only measure in Z, so we first rotate the qubit by -angle around y
    (`ry`), then measure Z. Checked numerically: ry(-t) then Z measures cos(t)Z + sin(t)X.
    """
    qc.ry(-angle, qubit)
    qc.measure(qubit, clbit)


def build_e91_circuit(alice_angle: float, bob_angle: float, eve_basis: int | None = None) -> QuantumCircuit:
    """One E91 round. Qubit 0 stays with Alice, qubit 1 travels to Bob.

    Classical bits: 0 = Alice's result, 1 = Bob's result, 2 = Eve's result (stays 0 if no attack).
    eve_basis: None = no attack, 0 = Z, 1 = X.
    """
    qc = QuantumCircuit(2, 3)
    qc.h(0)        # Bell pair: h on qubit 0, then cx
    qc.cx(0, 1)
    qc.barrier()
    # --- CHANNEL STEP on the travelling qubit (qubit 1), same idea as in BB84
    if eve_basis is not None:
        if eve_basis == 1:
            qc.h(1)            # X basis: rotate, measure, rotate back so the resent state matches her result
        qc.measure(1, 2)       # Eve's own classical bit
        if eve_basis == 1:
            qc.h(1)
    qc.id(1)       # carries the depolarizing noise (noise.py attaches the error to `id`)
    qc.barrier()
    measure(qc, 0, 0, alice_angle)
    measure(qc, 1, 1, bob_angle)
    return qc


def _run(circuits: list, seed: int, noise_model) -> tuple:
    """Batch-run all rounds once; return Alice's and Bob's results as +1 / -1 arrays."""
    backend = AerSimulator(noise_model=noise_model)
    compiled = transpile(circuits, backend, optimization_level=0)   # keep the `id` channel gate
    result = backend.run(compiled, shots=1, seed_simulator=seed).result()
    alice, bob = [], []
    for i in range(len(circuits)):
        counts = result.get_counts(i)
        key = max(counts, key=counts.get)   # one shot -> one key such as '010'
        # Little-endian: classical bit 0 is the RIGHTMOST character.
        # key[-1] = Alice (clbit 0), key[-2] = Bob (clbit 1), key[-3] = Eve (clbit 2).
        alice.append(1 - 2 * int(key[-1]))  # bit 0 -> +1, bit 1 -> -1
        bob.append(1 - 2 * int(key[-2]))
    return np.array(alice), np.array(bob)


def e91_run(channel: Channel, n_rounds: int) -> E91Result:
    """Run n_rounds E91 rounds on the channel and return S, its standard error and the key-round stats.

    Each round picks one of 5 settings at random: the 4 CHSH angle pairs, or the matched key setting.
    """
    settings_rng = np.random.default_rng([channel.seed, 2])    # own generator for the setting choices
    setting = settings_rng.integers(0, len(CHSH_PAIRS) + 1, size=n_rounds)   # 0-3 CHSH pairs, 4 = key round
    attacked, eve_bases = eve_choices(n_rounds, channel.eve_fraction, channel.seed)   # same Eve as BB84

    angles = [(ALICE_ANGLES[CHSH_PAIRS[s][0]], BOB_ANGLES[CHSH_PAIRS[s][1]]) if s < 4 else (KEY_ANGLE, KEY_ANGLE)
              for s in setting]
    circuits = [build_e91_circuit(a, b, int(e) if hit else None)
                for (a, b), e, hit in zip(angles, eve_bases, attacked)]
    alice, bob = _run(circuits, channel.seed, build_noise_model(channel.noise_level))
    products = alice * bob   # +1 when they agree, -1 when they differ

    correlators, s, variance = {}, 0.0, 0.0
    for idx, (name, (_, _, sign)) in enumerate(zip(CHSH_NAMES, CHSH_PAIRS)):
        p = products[setting == idx]
        n = len(p)
        e = float(p.mean())
        # Each product is +1 or -1, so its variance is 1 - E^2; the mean of n of them has
        # standard error sqrt((1 - E^2) / n).
        se = float(np.sqrt((1 - e ** 2) / n))
        correlators[name] = (e, se, n)
        s += sign * e
        variance += se ** 2     # the four correlators use different rounds, so variances add
    key = products[setting == 4]
    return E91Result(s=s, s_se=float(np.sqrt(variance)), correlators=correlators,
                     key_rounds=len(key), key_mismatches=int(np.sum(key == -1)))


def bb84_run(channel: Channel, n_qubits: int, sample_size: int, shots: int) -> BB84Result:
    """BB84 on the same channel (thin wrapper around src/bb84.py)."""
    return run_bb84(n_qubits, sample_size, shots, channel.seed, build_noise_model(channel.noise_level),
                    channel.eve_fraction)


def s_check_label(observed_s: float, expected_s: float, standard_error: float) -> str:
    """'PASS (z = 0.35)' or 'MISS (z = 2.23)': observed S within 2 standard errors of the expected S.

    z = (observed - expected) / standard error. Same 2-SE rule as the QBER checks.
    """
    z = (observed_s - expected_s) / standard_error
    return f"{'PASS' if abs(z) <= 2 else 'MISS'} (z = {z:.2f})"


@dataclass
class DualDecision:
    """Everything the final decision is based on."""
    level: str
    bb84: BB84Result
    e91: E91Result
    bb84_verdict: str       # Pass / Marginal / Fail
    e91_verdict: str
    decision: str           # Accept / Monitor / Reject
    anomaly: bool           # True when the two protocols disagree (Pass vs Fail)


def decide(channel: Channel, level: str, n_qubits: int, sample_size: int, shots: int, n_rounds: int,
           e91_channel: Channel | None = None) -> DualDecision:
    """Run BB84 and E91, turn each result into a verdict, and combine them with the threat level.

    Normally both protocols use the SAME channel (so their evidence is correlated).
    e91_channel is ONLY for the injected-fault demonstrations below: it lets E91 run on a
    different, artificially disturbed channel. Never pass it for a real scenario.
    """
    from src.decision import cross_check, e91_verdict, qber_verdict   # rules live in decision.py

    bb84 = bb84_run(channel, n_qubits, sample_size, shots)
    e91 = e91_run(e91_channel or channel, n_rounds)
    bb84_v = qber_verdict(bb84.mismatches, bb84.sample_size, level)
    e91_v = e91_verdict(e91.s, e91.s_se, level)
    decision, anomaly = cross_check(bb84_v, e91_v, level)
    return DualDecision(level, bb84, e91, bb84_v, e91_v, decision, anomaly)


# ---------------------------------------------------------------------------
# INJECTED, ARTIFICIAL FAULTS: these are NOT real attacks. They exist only to show the two
# ANOMALY rows of the cross-check matrix. Each one adds extra depolarizing noise to ONE
# protocol only, so the other protocol still sees the honest channel.
# ---------------------------------------------------------------------------
def injected_bb84_only_fault(honest: Channel, extra_noise: float) -> tuple:
    """INJECTED (artificial): a fault only in the BB84 apparatus, e.g. a bad detector that scrambles
    Bob's qubits. Returns (bb84_channel, e91_channel): BB84 gets the extra noise, E91 stays honest."""
    return Channel(extra_noise, honest.eve_fraction, honest.seed), honest


def injected_e91_only_fault(honest: Channel, extra_noise: float) -> tuple:
    """INJECTED (artificial): a fault only in the E91 apparatus, e.g. a faulty entangled-pair source whose
    pairs partly decohere. Returns (bb84_channel, e91_channel): E91 gets the extra noise, BB84 stays honest."""
    return honest, Channel(extra_noise, honest.eve_fraction, honest.seed)
