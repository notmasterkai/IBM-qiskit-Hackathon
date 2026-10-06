"""Depolarizing noise model for the BB84 channel (Phase 3)."""
from qiskit_aer.noise import NoiseModel, depolarizing_error


def build_noise_model(noise_level: float) -> NoiseModel:
    """Depolarizing noise on the channel step. noise_level is the error probability, 0 to 1.

    Approach: the channel is an explicit identity gate (`id`) in every BB84 circuit,
    so the depolarizing error is attached to `id`. That way all four encodings
    (bit 0/1 x basis Z/X) pass through it. If noise sat on `x`/`h` instead, a |0>
    sent in the Z basis has no gates and would never be touched.

    With probability noise_level the qubit is replaced by a fully random state,
    which flips a measured bit half the time.
    """
    model = NoiseModel()
    model.add_all_qubit_quantum_error(depolarizing_error(noise_level, 1), ["id"])
    return model
