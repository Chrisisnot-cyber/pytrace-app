import streamlit as st
import datetime

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PyTrace",
    page_icon="🔍",
    layout="centered",
)

# ── Module 1 script (CTR calculation) ─────────────────────────────────────────
SCRIPT_LINES = [
    (1,  "posts = ["),
    (2,  "    {'title': 'How I hit 1M upvotes', 'impressions': 50000, 'clicks': 3200},"),
    (3,  "    {'title': 'My worst post ever',   'impressions': 12000, 'clicks':  180},"),
    (4,  "    {'title': 'Guide to SEO in 2025', 'impressions': 31000, 'clicks': 2170},"),
    (5,  "]"),
    (6,  ""),
    (7,  "results = []"),
    (8,  "for post in posts:"),
    (9,  "    ctr = post['clicks'] / post['impressions'] * 100"),
    (10, "    results.append({'title': post['title'], 'ctr': round(ctr, 2)})"),
    (11, ""),
    (12, "top = max(results, key=lambda r: r['ctr'])"),
    (13, "print(f\"Top post: {top['title']} — CTR {top['ctr']}%\")"),
]

SCRIPT_ANNOTATIONS = {
    1:  "📦 A list of 3 post dictionaries",
    7:  "📋 Empty list — will hold results",
    8:  "🔁 Loop over each post",
    9:  "🧮 CTR = clicks ÷ impressions × 100",
    10: "➕ Append {title, ctr} to results",
    12: "🏆 Find the highest CTR entry",
    13: "📣 Print the result",
}

# ── Multiple-choice prediction options ────────────────────────────────────────
# Three plausible interpretations — no wrong answers label in the UI.
# A = fully correct  B = partially correct  C = reasonable misconception
PREDICTION_OPTIONS = [
    "A — It prints the post title and its CTR percentage, e.g. 'Top post: How I hit 1M upvotes — CTR 6.4%'",
    "B — It prints a list of all three posts ranked by CTR",
    "C — It prints the raw number of clicks for the most-clicked post",
    "D — I\'m not sure yet — I need to trace through the code first",
]

# ── Session state initialisation ──────────────────────────────────────────────
if "phase" not in st.session_state:
    st.session_state.phase = "identify"
if "learner" not in st.session_state:
    st.session_state.learner = ""
if "start_time" not in st.session_state:
    st.session_state.start_time = None
if "prediction" not in st.session_state:
    st.session_state.prediction = None

# ── PHASE: IDENTIFY ───────────────────────────────────────────────────────────
if st.session_state.phase == "identify":
    st.title("🔍 PyTrace")
    st.subheader("Learn to read Python — one line at a time")
    st.markdown(
        """
        **What is PyTrace?**  
        A short, structured exercise that builds your ability to read and
        predict Python code — the same kind of code an AI assistant or an
        engineer might hand you.

        Each session takes ~10 minutes.  
        Module 1 · **CTR Calculator** · Fully guided
        """
    )
    st.divider()
    name = st.text_input(
        "Your name, nickname, or learner ID",
        placeholder="e.g. Alex, PM-042, or leave blank for Anonymous",
        max_chars=40,
    )
    col1, _ = st.columns([1, 3])
    with col1:
        if st.button("Begin →", type="primary", use_container_width=True):
            st.session_state.learner = name.strip() if name.strip() else "Anonymous"
            st.session_state.start_time = datetime.datetime.now().isoformat()
            st.session_state.phase = "orient"
            st.rerun()

# ── PHASE: ORIENT ─────────────────────────────────────────────────────────────
elif st.session_state.phase == "orient":
    learner = st.session_state.learner
    st.title("🔍 PyTrace — Module 1")
    st.caption(f"Step 1 of 4 · Orient  ·  Learner: {learner}")
    st.divider()

    # 1. SCENARIO INTRO ─────────────────────────────────────────────────────
    st.markdown("### 💼 The scenario")
    st.markdown(
        """
        You are a product manager at a social media company.  
        An engineer sends you this short Python script and says:

        > *"This finds our best-performing post by click-through rate.
        Run it before the Monday review."*

        Before you run it, you want to read it yourself and make sure
        it does what they say it does.
        """
    )

    # 2. THE SCRIPT ─────────────────────────────────────────────────────────
    st.markdown("### 📄 `ctr_calculator.py`")
    for lineno, code in SCRIPT_LINES:
        if not code.strip():
            st.markdown("&nbsp;", unsafe_allow_html=True)
            continue
        annotation = SCRIPT_ANNOTATIONS.get(lineno, "")
        col_code, col_ann = st.columns([3, 2])
        with col_code:
            st.code(f"{lineno:>2}  {code}", language="python")
        with col_ann:
            if annotation:
                st.markdown(
                    f"<small style='color:#aaa'>{annotation}</small>",
                    unsafe_allow_html=True,
                )

    st.divider()

    # 3. PREDICTION QUESTION ────────────────────────────────────────────────
    st.markdown("### 🧠 Your first prediction")
    st.markdown(
        "Read the script above, then answer this:  \n"
        "**What do you think line 13 will print when the script runs?**"
    )
    st.caption(
        "Pick whichever option feels closest. There are no wrong answers — "
        "this just captures where you are before we trace through it together."
    )

    choice = st.radio(
        label="Select one:",
        options=PREDICTION_OPTIONS,
        index=None,
        label_visibility="collapsed",
    )

    st.markdown("")
    btn_disabled = choice is None
    if st.button(
        "▶  Start Tracing",
        type="primary",
        disabled=btn_disabled,
    ):
        st.session_state.prediction = choice
        st.session_state.phase = "trace"
        st.rerun()

    if btn_disabled:
        st.caption("↑ Select an option above to continue.")

# ── PHASE: TRACE (placeholder — coming next) ──────────────────────────────────
elif st.session_state.phase == "trace":
    st.title("🔍 PyTrace — Module 1")
    st.caption(f"Step 2 of 4 · Trace  ·  Learner: {st.session_state.learner}")
    st.divider()
    st.markdown(f"""
    **Your prediction was captured:**  
    > {st.session_state.prediction}

    The Trace phase is coming in the next build.
    """)
    if st.button("← Back to Orient"):
        st.session_state.phase = "orient"
        st.rerun()
