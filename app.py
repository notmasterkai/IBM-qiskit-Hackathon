"""Streamlit website for: Threat-Aware Quantum-Secure Communication for Biomedical Networks.

Run locally:  streamlit run app.py
It reuses our existing code in src/ and the saved files in results/. It does NOT need the
NSL-KDD dataset: threat probabilities come from results/threat_probabilities.csv
(made by make_threat_probs.py) and the per-seed sweep values behind the interactive charts
come from results/sweep_*.csv (made by make_sweep_data.py). Simulation only: no real photons,
no encryption.

Look and feel: teal = classical / machine learning, purple = quantum.
Decisions keep their colours: Accept green, Monitor amber, Reject red.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))  # so "import src..." works however the app is launched

from src.classifier import build_window            # picks records for a "real window"
from src.decision import BB84_THRESHOLDS, E91_THRESHOLDS, decide_bb84, threat_level
from src.dual_protocol_outline import Channel, injected_bb84_only_fault, injected_e91_only_fault
from src.sim_worker import SimulationError, bb84_scenario, dual_decision, run_in_process

RESULTS = ROOT / "results"

# Same values as the settings cell in threat_aware_qkd.ipynb (kept small so a run takes seconds)
SEED = 42
N_QUBITS = 2000
QBER_SAMPLE_SIZE = 300
SHOTS = 1
THREAT_WINDOW_SIZE = 100
E91_ROUNDS = 2000   # E91 rounds per run (notebook setting)
INJECTED_BB84_FAULT_NOISE = 0.40   # INJECTED, artificial: noise applied to BB84 only (notebook setting)
INJECTED_E91_FAULT_NOISE = 0.50    # INJECTED, artificial: noise applied to E91 only (notebook setting)
WINDOW_ATTACK_SHARES = {"mostly normal": 0.10, "mixed": 0.50, "attack-heavy": 0.90}
QUBIT_TABLE_ROWS = 15              # how many qubits the "first qubits" table shows

# Colours. Decisions: Accept green, Monitor amber, Reject red. Teal = classical / ML, purple = quantum.
DECISION_STYLE = {"Accept": ("#2e9e5b", "white"), "Monitor": ("#f0a202", "black"), "Reject": ("#d64545", "white")}
TEAL, PURPLE, NAVY_CARD, GRID = "#14b8a6", "#a78bfa", "#111c33", "#223152"
RED = "#d64545"

st.set_page_config(page_title="Threat-Aware Quantum-Secure Communication", layout="wide")

STYLE = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap');
.stApp, .stApp p, .stApp li, .stApp label, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp button,
.stApp input, .stApp textarea, .stApp div[data-testid="stMarkdownContainer"] {{ font-family: 'IBM Plex Sans', sans-serif; }}
.stApp code, .stApp pre, div[data-testid="stMetricValue"], .mono {{ font-family: 'IBM Plex Mono', monospace; }}
.hero {{ border-left: 6px solid {TEAL}; border-image: linear-gradient({TEAL}, {PURPLE}) 1; padding: .2rem 0 .2rem 1rem; margin-bottom: 1rem; }}
.hero-title {{ font-size: 1.7rem; font-weight: 700; line-height: 1.2; }}
.hero-sub {{ color: #9fb0cc; font-size: .95rem; margin-top: .25rem; }}
.hero-sub b {{ color: {TEAL}; }}
div[data-testid="stMetric"] {{ background: {NAVY_CARD}; border: 1px solid {GRID}; border-left: 4px solid {TEAL};
  border-radius: 12px; padding: .7rem 1rem; }}
.pipeline {{ display: flex; flex-wrap: wrap; align-items: stretch; gap: .4rem; margin: .6rem 0 1rem 0; }}
.stage {{ flex: 1 1 140px; min-width: 130px; background: {NAVY_CARD}; border: 2px solid {GRID}; border-radius: 12px;
  padding: .55rem .7rem; text-align: center; opacity: .38; }}
.stage.on {{ opacity: 1; }}
.stage .t {{ font-size: .78rem; color: #9fb0cc; text-transform: uppercase; letter-spacing: .04em; }}
.stage .v {{ font-family: 'IBM Plex Mono', monospace; font-weight: 600; font-size: 1.05rem; margin-top: .15rem; }}
.stage.classical.on {{ border-color: {TEAL}; box-shadow: 0 0 12px rgba(20,184,166,.35); }}
.stage.quantum.on {{ border-color: {PURPLE}; box-shadow: 0 0 12px rgba(167,139,250,.35); }}
.arrow {{ align-self: center; color: #6b7a99; font-size: 1.3rem; }}
table.qt {{ border-collapse: collapse; width: 100%; font-family: 'IBM Plex Mono', monospace; font-size: .88rem; }}
table.qt th {{ text-align: center; padding: .35rem .5rem; color: #9fb0cc; border-bottom: 1px solid {GRID}; font-weight: 500; }}
table.qt td {{ text-align: center; padding: .3rem .5rem; border-bottom: 1px solid #16233f; }}
table.qt tr.dim td {{ opacity: .45; }}
.zb {{ background: rgba(20,184,166,.20); }} .xb {{ background: rgba(167,139,250,.22); }}
.match {{ color: #4ade80; font-weight: 600; }} .mismatch {{ background: rgba(214,69,69,.35); color: #fecaca; font-weight: 600; }}
.kept {{ color: #4ade80; }} .disc {{ color: #94a3b8; }} .eve {{ color: #f0a202; }}
.legend-dot {{ display:inline-block; width:.8rem; height:.8rem; border-radius:50%; margin-right:.35rem; vertical-align:middle; }}
</style>
"""


# ---------------------------------------------------------------- data and simulation helpers
@st.cache_data
def load_threat_probabilities() -> pd.DataFrame:
    """Saved random-forest probabilities (record, true_label, threat_probability)."""
    return pd.read_csv(RESULTS / "threat_probabilities.csv")


@st.cache_data
def load_sweep(name: str) -> pd.DataFrame:
    """Per-seed values saved by make_sweep_data.py (the same numbers the notebook produced)."""
    return pd.read_csv(RESULTS / f"sweep_{name}.csv")


@st.cache_data
def real_windows() -> dict:
    """The three 100-record windows used in the notebook (same seed, same order)."""
    data = load_threat_probabilities()
    rng = np.random.default_rng(SEED)
    return {name: float(build_window(data["threat_probability"].to_numpy(), data["true_label"].to_numpy(),
                                     share, THREAT_WINDOW_SIZE, rng).mean())
            for name, share in WINDOW_ATTACK_SHARES.items()}


@st.cache_data(show_spinner=False)
def run_one(threat_prob: float, noise: float, f: float, seed: int) -> dict:
    """One real BB84 simulation (cached, so the same inputs return instantly), plus the first qubits for the table.

    Runs in its own process with a timeout (see src/sim_worker.py); raises SimulationError if it fails.
    """
    return run_in_process(bb84_scenario, threat_prob, noise, f, N_QUBITS, QBER_SAMPLE_SIZE, SHOTS, seed, QUBIT_TABLE_ROWS)


@st.cache_data(show_spinner=False)
def run_dual(level: str, noise: float, f: float, fault: str, seed: int) -> dict:
    """One BB84 + E91 run on the same channel (or with an INJECTED fault on one protocol). Cached."""
    honest = Channel(noise, f, seed)
    e91_channel = None
    channel = honest
    if fault == "bb84":
        channel, e91_channel = injected_bb84_only_fault(honest, INJECTED_BB84_FAULT_NOISE)
    elif fault == "e91":
        channel, e91_channel = injected_e91_only_fault(honest, INJECTED_E91_FAULT_NOISE)
    return run_in_process(dual_decision, channel, level, N_QUBITS, QBER_SAMPLE_SIZE, SHOTS, E91_ROUNDS, e91_channel)


# ---------------------------------------------------------------- display helpers
VERDICT_STYLE = {"Pass": DECISION_STYLE["Accept"], "Marginal": DECISION_STYLE["Monitor"], "Fail": DECISION_STYLE["Reject"]}


def header() -> None:
    st.markdown(STYLE, unsafe_allow_html=True)
    st.markdown("<div class='hero'><div class='hero-title'>Threat-Aware Quantum-Secure Communication for Biomedical Networks</div>"
                "<div class='hero-sub'>Qiskit Fall Fest 2026 &nbsp;·&nbsp; Track 2: Quantum Cryptography and Communication "
                "&nbsp;·&nbsp; Team <b>Daily Limit Reached</b></div></div>", unsafe_allow_html=True)


def verdict_box(verdict: str) -> None:
    colour, text = VERDICT_STYLE[verdict]
    st.markdown(f"<div style='background:{colour};color:{text};padding:0.6rem;border-radius:10px;"
                f"text-align:center;font-size:1.6rem;font-weight:700'>{verdict}</div>", unsafe_allow_html=True)


def decision_box(decision: str) -> None:
    colour, text = DECISION_STYLE[decision]
    st.markdown(f"<div style='background:{colour};color:{text};padding:1.2rem;border-radius:12px;"
                f"text-align:center;font-size:2.6rem;font-weight:700'>{decision}</div>", unsafe_allow_html=True)


def pipeline(stages: list, decision: str | None = None) -> None:
    """Row of stage cards. stages = [(title, value, kind)], kind 'classical' (teal) or 'quantum' (purple).

    value None = not run yet (the card is dimmed). The last card is the decision, coloured like the decision.
    """
    cards = []
    for title, value, kind in stages:
        on = "on" if value is not None else ""
        shown = value if value is not None else "·"
        cards.append(f"<div class='stage {kind} {on}'><div class='t'>{title}</div><div class='v'>{shown}</div></div>")
    if decision is None:
        cards.append("<div class='stage'><div class='t'>Decision</div><div class='v'>·</div></div>")
    else:
        colour, text = DECISION_STYLE[decision]
        cards.append(f"<div class='stage on' style='border-color:{colour};background:{colour};color:{text};box-shadow:0 0 12px {colour}88'>"
                     f"<div class='t' style='color:{text}'>Decision</div><div class='v'>{decision}</div></div>")
    st.markdown(f"<div class='pipeline'>{"<div class='arrow'>→</div>".join(cards)}</div>", unsafe_allow_html=True)


def threshold_table(level: str) -> None:
    lim = BB84_THRESHOLDS[level]
    st.markdown(f"**{level} threat:** Accept if QBER < **{100 * lim['accept']:.0f}%**, "
                f"Reject if QBER > **{100 * lim['reject']:.0f}%**, otherwise Monitor.")
    table = pd.DataFrame(BB84_THRESHOLDS).T
    table = (100 * table).round(0).astype(int).astype(str) + "%"
    table.columns = ["Accept if QBER below", "Reject if QBER above"]
    table.index.name = "Threat level"
    st.table(table)


def qubit_table(trace: dict) -> None:
    """HTML table of the first qubits of the run, colour coded (real data from the run)."""
    basis = lambda b: ("<td class='zb'>Z</td>" if b == 0 else "<td class='xb'>X</td>")
    rows = []
    for i in range(len(trace["alice_bits"])):
        ab, abs_, bbs, bb = trace["alice_bits"][i], trace["alice_bases"][i], trace["bob_bases"][i], trace["bob_bits"][i]
        kept = abs_ == bbs   # sifting keeps positions where the bases match
        if kept:
            result = "<td class='match'>✓ match</td>" if ab == bb else "<td class='mismatch'>✗ mismatch</td>"
        else:
            result = "<td>—</td>"
        eve = "<td class='eve'>intercepted</td>" if trace["attacked"][i] else "<td>—</td>"
        rows.append(f"<tr class='{'' if kept else 'dim'}'><td>{i + 1}</td><td>{ab}</td>{basis(abs_)}{basis(bbs)}"
                    f"<td class='{'kept' if kept else 'disc'}'>{'Kept' if kept else 'Discarded'}</td><td>{bb}</td>{result}{eve}</tr>")
    head = ("<tr><th>Qubit</th><th>Alice bit</th><th>Alice basis</th><th>Bob basis</th><th>Sifting</th>"
            "<th>Bob bit</th><th>Alice vs Bob</th><th>Eve</th></tr>")
    st.markdown(f"<table class='qt'>{head}{''.join(rows)}</table>", unsafe_allow_html=True)
    st.caption("Real data from this run. Sifting keeps a qubit only when Alice's and Bob's bases are the same; "
               "only kept qubits are compared (a mismatch is an error). Discarded rows are dimmed. "
               "Basis colours: Z teal, X purple.")


# ---------------------------------------------------------------- interactive (Plotly) charts, all from saved real data
def style_fig(fig: go.Figure, title: str, xtitle: str, ytitle: str, height: int = 400) -> go.Figure:
    fig.update_layout(template="plotly_dark", title=title, xaxis_title=xtitle, yaxis_title=ytitle, height=height,
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(family="IBM Plex Sans, sans-serif"),
                      legend=dict(orientation="h", yanchor="top", y=-0.22, x=0), margin=dict(t=60, b=40))
    fig.update_xaxes(gridcolor=GRID)
    fig.update_yaxes(gridcolor=GRID)
    return fig


def sweep_fig(df: pd.DataFrame, xcol: str, ycol: str, scale: float, theory_fn, theory_label: str,
              title: str, xtitle: str, ytitle: str) -> go.Figure:
    """Mean ± standard deviation over seeds (ddof = 1) with the individual seeds faintly shown; labelled theory line."""
    g = df.groupby(xcol)[ycol].agg(["mean", "std", "count"]).reset_index()
    xs = np.linspace(g[xcol].min(), g[xcol].max(), 100)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=scale * theory_fn(xs), mode="lines", name=theory_label,
                             line=dict(dash="dash", color="#9ca3af"), hovertemplate="theory: %{y:.2f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=df[xcol], y=scale * df[ycol], mode="markers", name="individual seeds",
                             marker=dict(color=PURPLE, size=5, opacity=0.28), hovertemplate="seed value: %{y:.2f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=g[xcol], y=scale * g["mean"], mode="markers", name=f"measured (mean ± std, {int(g['count'].iloc[0])} seeds)",
                             marker=dict(color=TEAL, size=10), error_y=dict(type="data", array=scale * g["std"], visible=True, color=TEAL),
                             customdata=np.stack([scale * g["std"]], axis=-1),
                             hovertemplate="mean: %{y:.2f}<br>std: %{customdata[0]:.2f}<extra></extra>"))
    return style_fig(fig, title, xtitle, ytitle)


def binary_entropy(q: np.ndarray) -> np.ndarray:
    q = np.clip(q, 1e-12, 1 - 1e-12)
    return -q * np.log2(q) - (1 - q) * np.log2(1 - q)


def key_rate_fig() -> go.Figure:
    """Theory only: usable key fraction 1 - 2h(Q), same grid as the notebook."""
    q = np.linspace(0, 0.20, 2001)
    key = np.maximum(0, 1 - 2 * binary_entropy(q))
    zero_q = q[np.argmax(key == 0)]   # first Q where the theory curve is zero
    fig = go.Figure(go.Scatter(x=100 * q, y=key, mode="lines", name="theory: 1 − 2h(Q)", line=dict(color=PURPLE),
                               hovertemplate="Q = %{x:.2f}%<br>theory key fraction = %{y:.3f}<extra></extra>"))
    fig.add_vline(x=100 * zero_q, line_dash="dash", line_color=RED,
                  annotation_text=f"theory reaches zero at Q ≈ {100 * zero_q:.1f}%", annotation_position="top right")
    return style_fig(fig, "Theoretical usable key fraction vs QBER (theory only)", "QBER Q (%)", "Usable key fraction (theory, asymptotic)")


def decision_map_fig() -> go.Figure:
    """For each threat level, which decision every QBER value gets (from decide_bb84, same grid as the notebook)."""
    q_grid = np.linspace(0, 0.30, 3001)
    fig = go.Figure()
    for lvl in ("Low", "Medium", "High"):
        decisions = np.array([decide_bb84(q, lvl) for q in q_grid])
        for d in ("Accept", "Monitor", "Reject"):
            mask = decisions == d
            start, width = 100 * q_grid[mask][0], 100 * (q_grid[1] - q_grid[0]) * mask.sum()
            fig.add_trace(go.Bar(y=[lvl], x=[width], base=[start], orientation="h", name=d, legendgroup=d,
                                 showlegend=(lvl == "Low"), marker_color=DECISION_STYLE[d][0], text=d, textposition="inside",
                                 insidetextanchor="middle", textfont=dict(color=DECISION_STYLE[d][1]),
                                 hovertemplate=f"{lvl} threat: {d}<br>QBER {start:.0f}% to {start + width:.0f}%<extra></extra>"))
    fig.update_layout(barmode="overlay")
    fig = style_fig(fig, "Decision map: threat level vs QBER", "QBER (%)", "Threat level", height=330)
    fig.update_yaxes(categoryorder="array", categoryarray=["High", "Medium", "Low"])
    return fig


def s_vs_f_fig() -> go.Figure:
    """S vs attack fraction f from the saved 20-seed data, with the labelled theory line and the classical bound."""
    df = load_sweep("s_vs_f")
    s_max = 2 * np.sqrt(2)
    fig = sweep_fig(df, "f", "s", 1.0, lambda x: s_max * (1 - x / 2), "theory: 2.83 × (1 − f/2)",
                    "E91: Bell score S vs eavesdropper attack fraction (no noise)",
                    "Eve attack fraction f (share of rounds intercepted)", "CHSH score S")
    fig.add_hline(y=2.0, line_dash="dash", line_color=RED, annotation_text="classical bound S = 2", annotation_position="bottom left")
    return fig


# ---------------------------------------------------------------- pages
def page_overview() -> None:
    st.info("**One-line pitch:** A network-threat classifier tells a simulated BB84 quantum key exchange how strict "
            "to be, so the same quantum error rate can lead to Accept, Monitor or Reject depending on how hostile "
            "the network looks.")

    st.subheader("The problem")
    st.markdown(
        "Hospitals and labs exchange sensitive patient data, and today the keys protecting it rely on RSA, ECC or "
        "Diffie-Hellman. A large quantum computer running Shor's algorithm could break these. Attackers can "
        "*harvest now, decrypt later*, and medical records stay sensitive for decades.\n\n"
        "We see two gaps: intrusion detection spots malicious network activity but is not linked to how keys are "
        "exchanged, and a quantum key exchange measures how disturbed its channel is but does not know whether "
        "the surrounding network is under attack. **Our goal is to link the two.**")

    st.subheader("How it works")
    st.graphviz_chart(f"""
    digraph {{
      rankdir=LR; bgcolor="transparent";
      node [shape=box, style="rounded,filled", fontname="Helvetica", fontcolor="#06201c", color="transparent"];
      edge [color="#9ca3af", fontcolor="#9ca3af", fontname="Helvetica"];
      data [label="Network records\\n(NSL-KDD)", fillcolor="{TEAL}"];
      clf  [label="Threat classifier\\n(random forest)", fillcolor="{TEAL}"];
      prob [label="Threat probability\\nLow / Medium / High", fillcolor="{TEAL}"];
      bb84 [label="BB84 simulation (Qiskit)\\nnoise + optional eavesdropper", fillcolor="{PURPLE}", fontcolor="#1b1233"];
      qber [label="QBER", fillcolor="{PURPLE}", fontcolor="#1b1233"];
      rule [label="Decision rules", fillcolor="#f0a202", fontcolor="#2a1c00"];
      out  [label="Accept / Monitor / Reject", fillcolor="#2e9e5b", fontcolor="white"];
      data -> clf -> prob; bb84 -> qber; qber -> rule; prob -> rule [label=" sets thresholds"]; rule -> out;
    }}""")
    st.caption("Teal = classical / machine learning. Purple = quantum (simulated).")
    st.markdown(
        "The classifier's threat probability **does not change the quantum physics**. It only changes how the "
        "quantum result (the QBER, the share of disagreeing bits) is *interpreted*: higher threat means stricter limits.")

    left, right = st.columns(2)
    with left:
        st.subheader("What it does")
        st.markdown("- Decides whether a quantum-agreed key is safe to use.\n"
                    "- Combines two pieces of evidence: network threat (machine learning) and channel disturbance (QBER).\n"
                    "- Outputs **Accept**, **Monitor** or **Reject**.")
    with right:
        st.subheader("What it does not do")
        st.markdown("- Encrypt any data.\n- Check whether messages were altered.\n"
                    "- Produce a final usable key (no error correction or privacy amplification).\n"
                    "- Use real quantum hardware or real photons: everything is simulated.")
    st.caption("Use the sidebar to try the live demo, see our results, and read the limitations. "
               "We do not claim quantum advantage.")


def page_demo() -> None:
    st.header("Live demo")
    st.write("Set the network threat and the channel conditions, then run one **real** BB84 simulation "
             f"({N_QUBITS} qubits, {QBER_SAMPLE_SIZE} sampled bits) on Qiskit's Aer simulator.")

    windows = real_windows()
    source_options = ["Set it with the slider"] + [f"Real 100-record window: {n} (average {p:.3f})" for n, p in windows.items()]
    source = st.radio("Where does the threat probability come from?", source_options)
    if source == source_options[0]:
        threat_prob = st.slider("Threat probability (0 = harmless, 1 = hostile)", 0.0, 1.0, 0.10, 0.01)
    else:
        threat_prob = list(windows.values())[source_options.index(source) - 1]
        st.caption("A window of 100 real test records, built the same way as in our notebook; "
                   "the threat probability is the random forest's average over the window.")
    c1, c2, c3 = st.columns(3)
    noise = c1.slider("Channel noise level", 0.0, 0.2, 0.0, 0.01, help="Depolarizing error probability; a measured bit flips with probability noise / 2.")
    f = c2.slider("Eve's attack fraction f", 0.0, 1.0, 0.0, 0.05, help="Share of qubits an intercept-resend eavesdropper measures.")
    seed = c3.number_input("Random seed", 0, 10_000, SEED, help="Change it to see how the QBER wobbles from run to run.")

    level = threat_level(threat_prob)
    st.markdown(f"**Threat probability {threat_prob:.3f} gives threat level: {level}**")

    if st.button("Run BB84 simulation", type="primary"):
        with st.spinner("Running the quantum simulation..."):
            try:
                st.session_state["demo_result"] = (run_one(threat_prob, noise, f, int(seed)), noise, f, int(seed))
            except SimulationError as error:
                st.session_state.pop("demo_result", None)
                st.error(str(error))

    saved = st.session_state.get("demo_result")
    if saved:
        result, r_noise, r_f, r_seed = saved
        pipeline([("1 · Classifier", f"threat prob {result['threat_prob']:.3f}", "classical"),
                  ("2 · Threat level", result["threat_level"], "classical"),
                  ("3 · BB84 simulation", f"noise {r_noise} · f {r_f}", "quantum"),
                  ("4 · QBER", f"{100 * result['qber']:.2f}%", "quantum")], result["decision"])
        st.caption(f"Result for: threat {result['threat_prob']:.3f}, noise {r_noise}, f = {r_f}, seed {r_seed}")
        a, b, c = st.columns(3)
        a.metric("Threat level", result["threat_level"])
        b.metric("QBER", f"{100 * result['qber']:.2f}%",
                 help=f"{result['mismatches']} mismatches in {result['sample_size']} sampled bits")
        c.markdown("**Decision**")
        with c:
            decision_box(result["decision"])
        lim = BB84_THRESHOLDS[result["threat_level"]]
        st.write(f"The QBER is {100 * result['qber']:.2f}% ({result['mismatches']} of {result['sample_size']} sampled bits "
                 f"disagreed). At **{result['threat_level']}** threat, Accept needs QBER below {100 * lim['accept']:.0f}% "
                 f"and Reject starts above {100 * lim['reject']:.0f}%.")
        st.caption("With 300 sampled bits the QBER wobbles by a few percentage points from run to run. "
                   "A weak attacker and a noisy channel can give the same QBER, which is why the threat level matters.")

        st.subheader(f"The first {QUBIT_TABLE_ROWS} qubits of this run")
        qubit_table(result["trace"])
        if result["trace"]["qber"] == result["qber"]:
            st.caption("Consistency check: repeating the run's steps with the same seed gives the same QBER as the card above.")
        else:
            st.warning("The per-qubit table's QBER differs from the card; please report this.")
    else:
        pipeline([("1 · Classifier", None, "classical"), ("2 · Threat level", None, "classical"),
                  ("3 · BB84 simulation", None, "quantum"), ("4 · QBER", None, "quantum")])
        st.caption("Press the button to run the simulation; each stage lights up as it contributes.")

    st.subheader(f"Threshold table (chosen level: {level})")
    threshold_table(level)


def page_results() -> None:
    st.header("Results")
    st.write("Everything on this page was produced by our own code and saved in `results/`. "
             "Standard-deviation error bars use 20 seeds. Charts are interactive: hover for values, click legend entries to hide lines.")

    st.subheader("1. Threat classifier (test set)")
    metrics = pd.read_csv(RESULTS / "metrics.csv").set_index("model").round(4)
    st.dataframe(metrics)
    st.image(str(RESULTS / "confusion_matrix.png"), caption="Confusion matrices on the NSL-KDD test set")
    st.caption("The test set has 17 attack types that never appear in training, so lower test scores are expected. "
               "Recall is only about 0.61, so many attacks look harmless to the classifier.")
    data = load_threat_probabilities()
    bins = np.linspace(0, 1, 11)
    labels = [f"{a:.1f}-{b:.1f}" for a, b in zip(bins[:-1], bins[1:])]
    hist = go.Figure()
    for name, label, colour in (("normal records", 0, TEAL), ("attack records", 1, "#fb7185")):
        counts = np.histogram(data.loc[data["true_label"] == label, "threat_probability"], bins=bins)[0]
        hist.add_trace(go.Bar(x=labels, y=counts, name=name, marker_color=colour))
    hist.update_layout(barmode="group")
    st.plotly_chart(style_fig(hist, "Threat probabilities of the 22,544 test records", "Random-forest threat probability",
                              "Number of test records"), width="stretch")

    st.subheader("2. BB84 simulation checks")
    a, b = st.columns(2)
    a.plotly_chart(sweep_fig(load_sweep("qber_vs_f"), "f", "qber", 100, lambda x: 0.25 * x, "theory (0.25 × f)",
                             "QBER vs eavesdropper attack fraction (no noise)", "Eve attack fraction f", "QBER (%)"),
                   width="stretch")
    b.plotly_chart(sweep_fig(load_sweep("qber_vs_noise"), "noise_level", "qber", 100, lambda x: x / 2, "theory (noise level / 2)",
                             "QBER vs channel noise (no eavesdropper)", "Depolarizing noise level", "QBER (%)"),
                   width="stretch")
    c, d = st.columns(2)
    c.plotly_chart(key_rate_fig(), width="stretch")
    d.plotly_chart(decision_map_fig(), width="stretch")

    st.subheader("3. Scenario table (3 chosen windows x 4 channels)")
    st.write("Each window is 100 test records built on purpose with a chosen share of real attacks; its threat level is "
             "the random forest's average probability. Each scenario is one BB84 run (seed 42).")
    sc = pd.read_csv(RESULTS / "scenarios.csv")
    sc["QBER (%)"] = (100 * sc["qber"]).round(2)
    sc = sc.rename(columns={"avg_threat_prob": "avg threat prob", "noise_level": "noise", "threat_level": "threat level"})
    st.dataframe(sc[["scenario", "avg threat prob", "noise", "f", "threat level", "QBER (%)", "decision"]], hide_index=True)
    st.success("Same QBER, different decision: on the noisy channel (QBER 5.00%) the quiet-traffic window (Low) "
               "is Accepted, while the mixed and attack-heavy windows (Medium) are only Monitored.")
    st.warning("No real window reached the High threat level (the attack-heavy window averaged 0.545, Medium). "
               "The classifier's low recall caps the window threat level.")

    st.subheader("4. What-if at High threat (HYPOTHETICAL)")
    st.error("Hypothetical: this table was NOT produced by a real window. It shows what the same measured QBERs would "
             "be decided as if the threat level were High. Bins and data were not changed.")
    wi = pd.read_csv(RESULTS / "scenarios_whatif_high.csv")
    wi = wi.rename(columns={"threat_level": "real threat level", "decision": "real decision",
                            "decision_if_High": "decision if High (hypothetical)", "qber_pct": "QBER (%)"})
    st.dataframe(wi[["scenario", "QBER (%)", "real threat level", "real decision", "decision if High (hypothetical)"]],
                 hide_index=True)


def page_e91() -> None:
    st.header("E91 cross-check")
    st.write("BB84 produces a QBER; a simplified **E91-style** protocol (Bell pairs and the CHSH test) produces a Bell score "
             "**S** on the **same simulated channel**. Each gets a verdict from a 95% interval (Pass / Marginal / Fail), and a "
             "cross-check matrix combines both verdicts with the threat level. E91 is an independent *diagnostic*, not a stronger key.")
    c1, c2, c3 = st.columns(3)
    level = c1.select_slider("Threat level", ["Low", "Medium", "High"], value="Low")
    noise = c2.slider("Channel noise level", 0.0, 0.2, 0.0, 0.01)
    f = c3.slider("Eve's attack fraction f", 0.0, 1.0, 0.0, 0.05)
    fault_label = st.radio("Inject a fault into ONE protocol? (INJECTED, artificial: not a real attack)",
                           ["None (both protocols see the same honest channel)",
                            "INJECTED fault in BB84 only (artificial)", "INJECTED fault in E91 only (artificial)"])
    fault = {0: "none", 1: "bb84", 2: "e91"}[["None (both protocols see the same honest channel)",
                                             "INJECTED fault in BB84 only (artificial)",
                                             "INJECTED fault in E91 only (artificial)"].index(fault_label)]
    if fault != "none":
        st.warning("**INJECTED, ARTIFICIAL fault.** It adds extra noise to one protocol only "
                   f"(BB84-only: noise {INJECTED_BB84_FAULT_NOISE}; E91-only: noise {INJECTED_E91_FAULT_NOISE}; the faulty protocol's "
                   "noise setting is replaced by this value) so the other protocol still sees the honest channel. "
                   "It exists only to show the ANOMALY rows of the matrix and is not a real attack.")
    seed = st.number_input("Random seed", 0, 10_000, SEED, key="e91_seed")

    if st.button("Run BB84 + E91", type="primary"):
        with st.spinner("Running both simulations..."):
            try:
                st.session_state["e91_result"] = (run_dual(level, noise, f, fault, int(seed)), level, fault)
            except SimulationError as error:
                st.session_state.pop("e91_result", None)
                st.error(str(error))

    saved = st.session_state.get("e91_result")
    if saved:
        res, r_level, r_fault = saved
        pipeline([("1 · Threat level", r_level, "classical"),
                  ("2 · BB84 + E91", "same channel" if r_fault == "none" else "INJECTED fault", "quantum"),
                  ("3 · QBER and S", f"{100 * res['qber']:.2f}% · S {res['s']:.2f}", "quantum"),
                  ("4 · Verdicts", f"{res['bb84_verdict']} / {res['e91_verdict']}", "quantum")], res["decision"])
        st.divider()
        m1, m2, m3 = st.columns(3)
        m1.metric("Threat level", r_level)
        m2.metric("QBER", f"{100 * res['qber']:.2f}%", help=f"{res['mismatches']} of {res['sample_size']} sampled bits")
        m3.metric("Bell score S", f"{res['s']:.3f}", help=f"± {res['s_se']:.3f} standard error; 2.83 is the ideal maximum, 2 the classical bound")
        a, b, c = st.columns(3)
        with a:
            st.markdown("**BB84 verdict**")
            verdict_box(res["bb84_verdict"])
            st.caption(f"QBER {100 * res['qber']:.2f}% ({res['mismatches']} of {res['sample_size']} sampled bits)")
        with b:
            st.markdown("**E91 verdict**")
            verdict_box(res["e91_verdict"])
            st.caption(f"S = {res['s']:.3f} ± {res['s_se']:.3f} (2.83 is the ideal maximum, 2 the classical bound)")
        with c:
            st.markdown(f"**Final decision at {r_level} threat**")
            decision_box(res["decision"])
        if res["anomaly"]:
            injected = " This case used an INJECTED, artificial fault; it is not a real attack." if r_fault != "none" else ""
            st.error(f"ANOMALY: the two protocols disagree (one Passes, the other Fails).{injected} "
                     "Possible causes are hypotheses, not proof: a problem specific to one protocol's apparatus, or an attack "
                     "that affects the two protocols differently.")
        if res["decision"] == "Monitor":
            st.info("Monitor means: rerun the failing or marginal protocol with more samples.")
        st.caption("One run each: 2000 qubits and 300 sampled bits for BB84, 2000 rounds for E91. Change the seed to see the wobble.")
    else:
        pipeline([("1 · Threat level", None, "classical"), ("2 · BB84 + E91", None, "quantum"),
                  ("3 · QBER and S", None, "quantum"), ("4 · Verdicts", None, "quantum")])
        st.caption("Press the button to run both simulations; each stage lights up as it contributes.")

    st.subheader("Thresholds used")
    t1, t2 = st.columns(2)
    lim_b, lim_e = BB84_THRESHOLDS[level], E91_THRESHOLDS[level]
    t1.markdown(f"**BB84 at {level} threat:** Pass if the 95% interval's upper bound is below {100 * lim_b['accept']:.0f}%; "
                f"Fail if its lower bound is above {100 * lim_b['reject']:.0f}%; otherwise Marginal.")
    t2.markdown(f"**E91 at {level} threat:** Pass if S − 2·SE ≥ {lim_e['accept']}; Fail if S + 2·SE ≤ {lim_e['reject']}; otherwise Marginal.")

    st.subheader("S vs eavesdropper attack fraction (our 20-seed results)")
    st.plotly_chart(s_vs_f_fig(), width="stretch")
    st.caption("Measured S (mean ± standard deviation over 20 seeds) against the theory line; the dashed red line is the classical bound S = 2.")
    st.subheader("Important limitations of the E91 layer")
    st.markdown(
        "- E91 is equivalent to BB84 for key security (Bennett, Brassard and Mermin), so it is an **independent diagnostic, not a stronger key**.\n"
        "- S above 2 does **not** give device-independent security in our setup.\n"
        "- Both protocols run on the **same simulated channel**, so their evidence is correlated, not fully independent.\n"
        "- ANOMALY disagreements here come from **injected faults**, not from observed natural behaviour; any cause of a disagreement is a hypothesis, not proof.\n"
        "- Our E91 is a **simplified \"E91-style\"** version (four CHSH angle pairs plus matched key rounds), not a full implementation.\n"
        "- With 95% intervals at our sample sizes, the dual-protocol mode is **more conservative** than BB84 alone: more Monitor (rerun) outcomes.")


def page_limitations() -> None:
    st.header("Limitations")
    st.write("We want to be clear about what this project does **not** do:")
    st.markdown(
        "- **Simulation only:** no real photons, detectors or quantum hardware.\n"
        "- **No error correction or privacy amplification:** we estimate whether a secure key is possible; we do not produce a final key.\n"
        "- **NSL-KDD is general intrusion data** built from simulated traffic, not healthcare-specific network traffic.\n"
        "- **QBER alone cannot separate noise from an attacker.** Both cause errors, so the threat context sets how much error is tolerated.\n"
        "- **The classifier's low recall caps the window threat level.** The random forest misses about 4 in 10 attacks on the test set "
        "(recall 0.6094), so even a window with 90% real attacks only reached an average probability of 0.545 (Medium); no window reached High. "
        "A calibration check of the probabilities (planned extension) would show whether the bins should move.\n"
        "- **A weak attacker can slip through.** The 9.33% QBER at f = 0.3 in our scenario table comes from a single seed-42 run. "
        "Averaged over 20 seeds the QBER at f = 0.3 was 7.60% (standard deviation 1.40 points), close to the theory value of 7.5%, "
        "and that mean would be Accepted at Low threat. Of the 20 single runs, 14 would be Accepted and 6 Monitored at Low.\n"
        "- **BB84 needs an authenticated classical channel.** QKD complements post-quantum cryptography and does not replace it.\n"
        "- **No quantum advantage is claimed.**")
    st.subheader("Not built")
    st.markdown("Fixed-vs-adaptive comparison, fake-backend noise, per-attack-family results, threshold-aware attacker, "
                "calibration check and the timeline demo are planned extensions and are **not built**. "
                "The E91 cross-check and the confidence-interval verdicts are built; see the E91 cross-check page for their limitations.")
    st.caption("BB84 and random forests are standard techniques, and machine learning for detecting attacks on QKD already exists. "
               "Our contribution is the integration: using network-level threat to set the QKD decision rules.")


# ---------------------------------------------------------------- navigation
PAGES = {"Overview": page_overview, "Live demo": page_demo, "Results": page_results, "E91 cross-check": page_e91,
         "Limitations": page_limitations}
header()
st.sidebar.title("Navigation")
choice = st.sidebar.radio("Go to", list(PAGES), label_visibility="collapsed")
st.sidebar.markdown(f"<span class='legend-dot' style='background:{TEAL}'></span>Classical / machine learning<br>"
                    f"<span class='legend-dot' style='background:{PURPLE}'></span>Quantum (simulated)", unsafe_allow_html=True)
st.sidebar.caption("Simulation only. Team Daily Limit Reached.")
PAGES[choice]()
