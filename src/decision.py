"""Threshold tables and Accept / Monitor / Reject logic (QBER rules come in Phase 5)."""

# Threat bins from CLAUDE.md section 9.1
LOW_MAX = 0.33     # Low if p < 0.33
HIGH_MIN = 0.66    # High if p > 0.66; Medium in between (both ends included)


def threat_level(p: float) -> str:
    """Map a threat probability (0 to 1) to 'Low', 'Medium' or 'High'."""
    if p < LOW_MAX:
        return "Low"
    if p > HIGH_MIN:
        return "High"
    return "Medium"


# BB84 QBER thresholds from CLAUDE.md section 9.2 (QBER as a fraction, 0 to 1).
# Accept if QBER < accept; Reject if QBER > reject; anything else is Monitor.
# 0.11 is physics (usable key reaches zero); 0.08, 0.05 and 0.03 are design choices.
BB84_THRESHOLDS = {
    "Low":    {"accept": 0.08, "reject": 0.11},
    "Medium": {"accept": 0.05, "reject": 0.11},
    "High":   {"accept": 0.03, "reject": 0.08},
}


def decide_bb84(qber: float, level: str) -> str:
    """Return 'Accept', 'Monitor' or 'Reject' for a QBER (fraction) at a threat level.

    Strict comparisons: a QBER exactly at a limit is NOT accepted and NOT rejected,
    so it falls in the Monitor zone.
    """
    limits = BB84_THRESHOLDS[level]
    if qber < limits["accept"]:
        return "Accept"
    if qber > limits["reject"]:
        return "Reject"
    return "Monitor"


def run_scenario(threat_prob: float, noise_level: float, eve_fraction: float,
                 n_qubits: int, sample_size: int, shots: int, seed: int) -> dict:
    """End to end: threat probability -> threat level -> BB84 run -> QBER -> decision.

    The threat level only changes how the QBER is interpreted; the quantum
    simulation is the same whatever the threat level is.
    """
    # Imported here so the threat bins above stay usable without Qiskit
    from src.bb84 import run_bb84
    from src.noise import build_noise_model

    level = threat_level(threat_prob)
    result = run_bb84(n_qubits, sample_size, shots, seed, build_noise_model(noise_level), eve_fraction)
    return {"threat_prob": threat_prob, "threat_level": level, "qber": result.qber,
            "mismatches": result.mismatches, "sample_size": result.sample_size,
            "decision": decide_bb84(result.qber, level)}


# ---------------------------------------------------------------------------
# Confidence-interval verdicts (CLAUDE.md section 10, extension E2)
# ---------------------------------------------------------------------------
CI_ALPHA = 0.05   # 95% interval


def clopper_pearson(k: int, n: int, alpha: float = CI_ALPHA) -> tuple:
    """Exact (Clopper-Pearson) confidence interval (lo, hi) for k mismatches out of n sampled bits.

    Returned as fractions 0 to 1. lo = 0 when k = 0 and hi = 1 when k = n, because the
    beta formulas are undefined at those edges.
    """
    from scipy.stats import beta   # only needed here, so only imported here

    lo = 0.0 if k == 0 else float(beta.ppf(alpha / 2, k, n - k + 1))
    hi = 1.0 if k == n else float(beta.ppf(1 - alpha / 2, k + 1, n - k))
    return lo, hi


def qber_verdict(k: int, n: int, level: str) -> str:
    """'Pass', 'Fail' or 'Marginal' for k mismatches in n sampled bits at a threat level.

    Pass: even the pessimistic end of the interval (hi) is below the accept limit.
    Fail: even the optimistic end of the interval (lo) is above the reject limit.
    Marginal: anything in between. Limits come from BB84_THRESHOLDS (unchanged).
    """
    lo, hi = clopper_pearson(k, n)
    limits = BB84_THRESHOLDS[level]
    if hi < limits["accept"]:
        return "Pass"
    if lo > limits["reject"]:
        return "Fail"
    return "Marginal"


# ---------------------------------------------------------------------------
# E91 thresholds, verdict and cross-check matrix (CLAUDE.md sections 11 and 12; extension)
# ---------------------------------------------------------------------------
# Bell score S thresholds. 2.0 (classical bound) and 2.83 (quantum maximum) are physics;
# 2.4, 2.5, 2.6 and 2.2 are design choices.
E91_THRESHOLDS = {
    "Low":    {"accept": 2.4, "reject": 2.0},
    "Medium": {"accept": 2.5, "reject": 2.0},
    "High":   {"accept": 2.6, "reject": 2.2},
}


def e91_verdict(s: float, se: float, level: str) -> str:
    """'Pass', 'Fail' or 'Marginal' for a Bell score S with standard error se at a threat level.

    Pass: even the pessimistic end (S - 2*SE) is at or above the accept limit.
    Fail: even the optimistic end (S + 2*SE) is at or below the reject limit.
    Marginal: anything in between.
    """
    limits = E91_THRESHOLDS[level]
    if s - 2 * se >= limits["accept"]:
        return "Pass"
    if s + 2 * se <= limits["reject"]:
        return "Fail"
    return "Marginal"


# Cross-check matrix: (BB84 verdict, E91 verdict) -> ((Low, Medium, High) decisions, ANOMALY flag).
# Both orders of "Pass + Marginal" and "Marginal + Fail" are listed explicitly.
CROSS_CHECK = {
    ("Pass", "Pass"):         (("Accept", "Accept", "Accept"), False),
    ("Pass", "Marginal"):     (("Accept", "Monitor", "Monitor"), False),
    ("Marginal", "Pass"):     (("Accept", "Monitor", "Monitor"), False),
    ("Marginal", "Marginal"): (("Monitor", "Monitor", "Reject"), False),
    ("Pass", "Fail"):         (("Monitor", "Monitor", "Reject"), True),    # BB84 Pass + E91 Fail: ANOMALY
    ("Fail", "Pass"):         (("Monitor", "Reject", "Reject"), True),     # BB84 Fail + E91 Pass: ANOMALY
    ("Marginal", "Fail"):     (("Monitor", "Reject", "Reject"), False),
    ("Fail", "Marginal"):     (("Monitor", "Reject", "Reject"), False),
    ("Fail", "Fail"):         (("Reject", "Reject", "Reject"), False),
}
_LEVEL_INDEX = {"Low": 0, "Medium": 1, "High": 2}


def cross_check(bb84_verdict: str, e91_verdict_: str, level: str) -> tuple:
    """Combine the two verdicts with the threat level. Returns (decision, anomaly flag).

    'Monitor' means: rerun the failing protocol with more samples. An ANOMALY flag means the
    protocols disagree; any cause is a hypothesis, never proof.
    """
    decisions, anomaly = CROSS_CHECK[(bb84_verdict, e91_verdict_)]
    return decisions[_LEVEL_INDEX[level]], anomaly
