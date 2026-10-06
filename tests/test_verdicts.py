"""Unit tests for the Clopper-Pearson interval and QBER verdicts (extension E2).

Run from the repo root:  python -m tests.test_verdicts
"""
from src.decision import BB84_THRESHOLDS, clopper_pearson, qber_verdict

N = 300   # same sample size as QBER_SAMPLE_SIZE in the notebook


def test_k_zero():
    lo, hi = clopper_pearson(0, N)
    assert lo == 0.0
    # closed form for k = 0 with alpha = 0.05: hi = 1 - 0.025 ** (1 / n)
    assert abs(hi - (1 - 0.025 ** (1 / N))) < 1e-9
    assert qber_verdict(0, N, "Low") == "Pass"


def test_k_equals_n():
    lo, hi = clopper_pearson(N, N)
    assert hi == 1.0
    assert abs(lo - 0.025 ** (1 / N)) < 1e-9   # closed form for k = n
    assert qber_verdict(N, N, "Low") == "Fail"


def test_clear_pass():
    # 3 mismatches in 300 (1%): upper bound is far below every Low/Medium accept limit
    assert qber_verdict(3, N, "Low") == "Pass"
    assert qber_verdict(3, N, "Medium") == "Pass"


def test_clear_fail():
    # 75 mismatches in 300 (25%, a full attack): lower bound is far above every reject limit
    for level in BB84_THRESHOLDS:
        assert qber_verdict(75, N, level) == "Fail"


def test_marginal():
    # 20 in 300 (6.7%): interval straddles the Low accept limit (0.08) and reject limit (0.11)
    lo, hi = clopper_pearson(20, N)
    limits = BB84_THRESHOLDS["Low"]
    assert hi >= limits["accept"] and lo <= limits["reject"]
    assert qber_verdict(20, N, "Low") == "Marginal"


def test_interval_contains_estimate():
    for k in (0, 1, 15, 75, 299, 300):
        lo, hi = clopper_pearson(k, N)
        assert 0.0 <= lo <= k / N <= hi <= 1.0


if __name__ == "__main__":
    tests = [t for name, t in sorted(globals().items()) if name.startswith("test_")]
    for t in tests:
        t()
        print("PASS", t.__name__)
    print(f"{len(tests)} tests passed")
