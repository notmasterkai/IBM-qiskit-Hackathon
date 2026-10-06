"""Unit tests for E91 thresholds, e91_verdict and the cross-check matrix (extension).

The expected values below are typed in from CLAUDE.md sections 11 and 12, NOT read from the code's tables.
Run from the repo root:  python -m tests.test_cross_check
"""
from src.decision import CROSS_CHECK, E91_THRESHOLDS, cross_check, e91_verdict

LEVELS = ("Low", "Medium", "High")

# (BB84 verdict, E91 verdict, Low, Medium, High, ANOMALY): one entry per matrix row, both orders where the row says "either order"
SPEC_ROWS = [
    ("Pass", "Pass", "Accept", "Accept", "Accept", False),
    ("Pass", "Marginal", "Accept", "Monitor", "Monitor", False),
    ("Marginal", "Pass", "Accept", "Monitor", "Monitor", False),
    ("Marginal", "Marginal", "Monitor", "Monitor", "Reject", False),
    ("Pass", "Fail", "Monitor", "Monitor", "Reject", True),      # BB84 Pass + E91 Fail
    ("Fail", "Pass", "Monitor", "Reject", "Reject", True),       # BB84 Fail + E91 Pass
    ("Marginal", "Fail", "Monitor", "Reject", "Reject", False),
    ("Fail", "Marginal", "Monitor", "Reject", "Reject", False),
    ("Fail", "Fail", "Reject", "Reject", "Reject", False),
]


def test_thresholds_match_spec():
    assert E91_THRESHOLDS == {"Low": {"accept": 2.4, "reject": 2.0},
                              "Medium": {"accept": 2.5, "reject": 2.0},
                              "High": {"accept": 2.6, "reject": 2.2}}


def test_every_matrix_row_and_level():
    for bb84, e91, *decisions, anomaly in SPEC_ROWS:
        for level, expected in zip(LEVELS, decisions):
            assert cross_check(bb84, e91, level) == (expected, anomaly), (bb84, e91, level)


def test_matrix_has_exactly_nine_combinations():
    assert len(CROSS_CHECK) == 9 and len(SPEC_ROWS) == 9


def test_only_the_two_anomaly_rows_flag():
    flagged = {(b, e) for b, e, *_ , a in SPEC_ROWS if a}
    assert flagged == {("Pass", "Fail"), ("Fail", "Pass")}
    assert {k for k, (_, a) in CROSS_CHECK.items() if a} == flagged


def test_e91_verdict_clear_cases():
    for level in LEVELS:
        assert e91_verdict(2.83, 0.01, level) == "Pass"
        assert e91_verdict(1.4, 0.05, level) == "Fail"
        assert e91_verdict(2.3, 0.05, "Low") == "Marginal"   # 2.2 < 2.4 accept limit, 2.4 > 2.0 reject limit


def test_e91_verdict_limits_are_inclusive():
    # Pass when S - 2*SE >= accept (equal counts as Pass); Fail when S + 2*SE <= reject (equal counts as Fail)
    assert e91_verdict(2.5, 0.05, "Low") == "Pass"        # 2.5 - 0.1 = 2.4 exactly
    assert e91_verdict(2.4, 0.05, "Low") == "Marginal"    # 2.4 - 0.1 = 2.3 < 2.4
    assert e91_verdict(1.9, 0.05, "Low") == "Fail"        # 1.9 + 0.1 = 2.0 exactly
    assert e91_verdict(1.95, 0.05, "Low") == "Marginal"   # 1.95 + 0.1 = 2.05 > 2.0
    assert e91_verdict(2.1, 0.05, "High") == "Fail"       # High reject limit is 2.2: 2.1 + 0.1 = 2.2 exactly


if __name__ == "__main__":
    tests = [t for name, t in sorted(globals().items()) if name.startswith("test_")]
    for t in tests:
        t()
        print("PASS", t.__name__)
    print(f"{len(tests)} tests passed")
