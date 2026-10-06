"""BB84 circuits, sifting and QBER estimation, with optional noise and an intercept-resend eavesdropper.

Noise (optional noise_model) and Eve both act at the marked CHANNEL STEP.
Bases are encoded as 0 = Z, 1 = X everywhere.
"""
from dataclasses import dataclass

import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator


@dataclass
class BB84Result:
    """Outcome of one BB84 run. QBER is a fraction (0.05 means 5%)."""
    qber: float
    sample_size: int
    mismatches: int
    sifted_count: int
    raw_key_length: int   # sifted bits left after the public sample is thrown away


def alice_random(n_qubits: int, rng: np.random.Generator):
    """Alice's random bits and random bases (0 = Z, 1 = X), as arrays of 0/1."""
    alice_bits = rng.integers(0, 2, size=n_qubits)
    alice_bases = rng.integers(0, 2, size=n_qubits)  # 0 = Z, 1 = X
    return alice_bits, alice_bases


def build_circuit(bit: int, alice_basis: int, bob_basis: int, eve_basis: int | None = None) -> QuantumCircuit:
    """One-qubit BB84 circuit: Alice encodes, the channel acts, Bob measures.

    eve_basis = None means Eve does not touch this qubit; 0 = Z or 1 = X means she
    intercepts it. Two classical bits: clbit 0 holds Bob's result, clbit 1 holds
    Eve's (it stays 0 when she does not attack).
    """
    qc = QuantumCircuit(1, 2)
    # --- Alice: bit 1 -> X gate; X basis -> then a Hadamard (gives |+> or |->)
    if bit == 1:
        qc.x(0)
    if alice_basis == 1:
        qc.h(0)
    qc.barrier()
    # --- CHANNEL STEP. First Eve (if she attacks), then the identity gate that carries
    # the depolarizing noise (without a gate, a |0> sent in the Z basis would have
    # nothing for noise to act on).
    if eve_basis is not None:
        # Intercept-resend: measure in Eve's basis (X basis: H first), store her result
        # in her own classical bit 1, then undo the H so the state she resends is
        # the one matching her result in her basis. The measurement already collapsed it.
        if eve_basis == 1:
            qc.h(0)
        qc.measure(0, 1)
        if eve_basis == 1:
            qc.h(0)
    qc.id(0)
    qc.barrier()
    # --- Bob: to measure in the X basis, apply H first, then measure normally
    if bob_basis == 1:
        qc.h(0)
    qc.measure(0, 0)
    return qc


def run_circuits(circuits: list, shots: int, seed: int, noise_model=None, return_eve: bool = False):
    """Run ALL circuits in one batched call; return Bob's result bit per circuit.

    With return_eve=True, returns (bob_bits, eve_bits).

    optimization_level=0 stops transpile from deleting the identity channel gate.
    """
    backend = AerSimulator(noise_model=noise_model)  # None = ideal channel
    compiled = transpile(circuits, backend, optimization_level=0)
    result = backend.run(compiled, shots=shots, seed_simulator=seed).result()
    bob_bits, eve_bits = [], []
    for i in range(len(circuits)):
        counts = result.get_counts(i)
        key = max(counts, key=counts.get)  # with shots=1 there is exactly one key, e.g. '10'
        # Qiskit is little-endian: classical bit 0 is the RIGHTMOST character of the key.
        # Bob measured into clbit 0 -> key[-1]. Eve measured into clbit 1 -> key[-2].
        bob_bits.append(int(key[-1]))
        eve_bits.append(int(key[-2]))
    if return_eve:
        return np.array(bob_bits), np.array(eve_bits)
    return np.array(bob_bits)


def sift(alice_bits, bob_bits, alice_bases, bob_bases):
    """Keep only positions where Alice's and Bob's bases match. Returns both bit arrays."""
    keep = alice_bases == bob_bases
    return alice_bits[keep], bob_bits[keep]


def estimate_qber(alice_sifted, bob_sifted, sample_size: int, rng: np.random.Generator) -> BB84Result:
    """Compare a random sample of sifted bits; QBER = mismatches / sample size.

    The sampled bits are public afterwards, so they are removed from the raw key.
    """
    sifted_count = len(alice_sifted)
    if sample_size > sifted_count:
        raise ValueError(f"sample_size {sample_size} is larger than sifted bits {sifted_count}")
    sample_idx = rng.choice(sifted_count, size=sample_size, replace=False)
    mismatches = int(np.sum(alice_sifted[sample_idx] != bob_sifted[sample_idx]))
    return BB84Result(
        qber=mismatches / sample_size,
        sample_size=sample_size,
        mismatches=mismatches,
        sifted_count=sifted_count,
        raw_key_length=sifted_count - sample_size,
    )


def eve_choices(n_qubits: int, eve_fraction: float, seed: int):
    """Which qubits Eve attacks (each with probability eve_fraction) and her random bases.

    Uses its own seeded generator so Eve's randomness never disturbs Alice's and Bob's.
    Returns (attacked: bool array, eve_bases: 0 = Z, 1 = X).
    """
    eve_rng = np.random.default_rng([seed, 1])
    attacked = eve_rng.random(n_qubits) < eve_fraction
    eve_bases = eve_rng.integers(0, 2, size=n_qubits)  # 0 = Z, 1 = X
    return attacked, eve_bases


def run_bb84(n_qubits: int, sample_size: int, shots: int, seed: int, noise_model=None,
             eve_fraction: float = 0.0) -> BB84Result:
    """Full BB84 run. Ideal channel unless a noise_model and/or eve_fraction (0 to 1) is given.

    Same seed -> same result.
    """
    rng = np.random.default_rng(seed)
    alice_bits, alice_bases = alice_random(n_qubits, rng)
    bob_bases = rng.integers(0, 2, size=n_qubits)  # 0 = Z, 1 = X
    attacked, eve_bases = eve_choices(n_qubits, eve_fraction, seed)
    circuits = [build_circuit(b, a, c, int(e) if hit else None)
                for b, a, c, e, hit in zip(alice_bits, alice_bases, bob_bases, eve_bases, attacked)]
    bob_bits = run_circuits(circuits, shots, seed, noise_model)
    alice_sifted, bob_sifted = sift(alice_bits, bob_bits, alice_bases, bob_bases)
    return estimate_qber(alice_sifted, bob_sifted, sample_size, rng)


def qber_standard_error(expected_qber: float, sample_size: int) -> float:
    """Standard error of a QBER estimate: sqrt(p * (1 - p) / n), p = expected QBER (fraction)."""
    return float(np.sqrt(expected_qber * (1 - expected_qber) / sample_size))


def within_two_se(observed_qber: float, expected_qber: float, sample_size: int) -> bool:
    """Team tolerance for every 'approximately' check: observed is within 2 standard errors."""
    return abs(observed_qber - expected_qber) <= 2 * qber_standard_error(expected_qber, sample_size)


def check_label(observed_qber: float, expected_qber: float, sample_size: int) -> str:
    """'PASS (z = 0.35)' or 'MISS (z = 2.23)' using the 2-standard-error tolerance.

    z = (observed - expected) / SE. When the expected QBER is 0 the SE is 0, so the
    check is exact: any difference is a MISS.
    """
    se = qber_standard_error(expected_qber, sample_size)
    if se == 0:
        return "PASS (exact)" if observed_qber == expected_qber else "MISS (exact)"
    z = (observed_qber - expected_qber) / se
    return f"{'PASS' if abs(z) <= 2 else 'MISS'} (z = {z:.2f})"
