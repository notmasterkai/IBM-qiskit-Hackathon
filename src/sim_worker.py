"""Run one simulation in its own short-lived process, with a timeout (used by app.py only).

Why: Qiskit Aer crashed (segmentation fault on macOS) when circuits were built in Streamlit's
many short-lived threads, and a single long-lived worker thread then hung on the second click
on Linux (Streamlit Cloud). A fresh "spawn" process per simulation avoids both problems:
nothing is shared between runs, and a stuck run can simply be killed after the timeout.

The functions that run inside the child process live here (not in app.py) because a spawned
process can only import code from a real module. They contain the same calls as before, only moved.
"""
import multiprocessing as mp

import numpy as np

SIMULATION_TIMEOUT_SECONDS = 60  # a run longer than this is killed and reported as an error


class SimulationError(RuntimeError):
    """The simulation timed out, crashed, or raised an error. The message is safe to show to the user."""


def bb84_scenario(threat_prob: float, noise: float, f: float, n_qubits: int, sample_size: int,
                  shots: int, seed: int, table_rows: int) -> dict:
    """run_scenario result plus the first qubits of the same run (same seed, same calls, same order)."""
    from src.bb84 import alice_random, build_circuit, estimate_qber, eve_choices, run_circuits, sift
    from src.decision import run_scenario
    from src.noise import build_noise_model

    result = run_scenario(threat_prob, noise, f, n_qubits, sample_size, shots, seed)

    # run_scenario returns only totals, so to SHOW real per-qubit data we redo the same steps with the
    # same functions. Same seed means the same random draws, so the QBER must equal run_scenario's.
    rng = np.random.default_rng(seed)
    alice_bits, alice_bases = alice_random(n_qubits, rng)          # bases: 0 = Z, 1 = X
    bob_bases = rng.integers(0, 2, size=n_qubits)                  # 0 = Z, 1 = X
    attacked, eve_bases = eve_choices(n_qubits, f, seed)
    circuits = [build_circuit(b, a, c, int(e) if hit else None)
                for b, a, c, e, hit in zip(alice_bits, alice_bases, bob_bases, eve_bases, attacked)]
    bob_bits = run_circuits(circuits, shots, seed, build_noise_model(noise))
    alice_sifted, bob_sifted = sift(alice_bits, bob_bits, alice_bases, bob_bases)
    qber_result = estimate_qber(alice_sifted, bob_sifted, sample_size, rng)
    n = table_rows
    result["trace"] = {"alice_bits": alice_bits[:n].tolist(), "alice_bases": alice_bases[:n].tolist(),
                       "bob_bases": bob_bases[:n].tolist(), "bob_bits": bob_bits[:n].tolist(),
                       "attacked": attacked[:n].tolist(), "qber": qber_result.qber,
                       "sifted_count": qber_result.sifted_count}
    return result


def dual_decision(channel, level: str, n_qubits: int, sample_size: int, shots: int, n_rounds: int,
                  e91_channel) -> dict:
    """BB84 + E91 on the channel (or the injected-fault channels), returned as a plain dict."""
    from src.dual_protocol_outline import decide

    d = decide(channel, level, n_qubits, sample_size, shots, n_rounds, e91_channel)
    return {"qber": d.bb84.qber, "mismatches": d.bb84.mismatches, "sample_size": d.bb84.sample_size,
            "bb84_verdict": d.bb84_verdict, "s": d.e91.s, "s_se": d.e91.s_se, "e91_verdict": d.e91_verdict,
            "decision": d.decision, "anomaly": d.anomaly}


def _child(conn, func, args) -> None:
    """Runs in the child process: call func, send ("ok", result) or ("error", message) back."""
    try:
        conn.send(("ok", func(*args)))
    except BaseException as error:  # report everything, including odd errors, instead of dying silently
        conn.send(("error", f"{type(error).__name__}: {error}"))
    finally:
        conn.close()


def run_in_process(func, *args, timeout: float = SIMULATION_TIMEOUT_SECONDS):
    """Run func(*args) in a fresh spawned process and return its result.

    Raises SimulationError if it takes longer than `timeout` seconds, crashes, or raises.
    func and args must be picklable (module-level functions, numbers, strings, dataclasses).
    """
    ctx = mp.get_context("spawn")  # spawn = brand-new interpreter, works the same on Mac and Linux
    parent_conn, child_conn = ctx.Pipe(duplex=False)
    process = ctx.Process(target=_child, args=(child_conn, func, args), daemon=True)
    process.start()
    child_conn.close()  # parent must drop its copy, so a crashed child shows up as EOF instead of a hang
    try:
        if not parent_conn.poll(timeout):
            raise SimulationError(f"The simulation took longer than {timeout:.0f} s and was stopped. Please try again.")
        try:
            status, payload = parent_conn.recv()
        except EOFError:
            raise SimulationError("The simulation process crashed before returning a result. Please try again.")
        if status == "error":
            raise SimulationError(f"The simulation failed ({payload}).")
        return payload
    finally:
        if process.is_alive():
            process.terminate()
        process.join(5)
        parent_conn.close()
