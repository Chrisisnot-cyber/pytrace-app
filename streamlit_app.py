import streamlit as st
import datetime

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PyTrace",
    page_icon="🔍",
    layout="centered",
)

# ── Module 1 script (CTR calculation) ────────────────────────────────────────
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
    1:  "📦 Define a list of post dictionaries",
    7:  "📋 Empty list to collect results",
    8:  "🔁 Loop over each post",
    9:  "🧮 Calculate click-through rate (%)",
    10: "➕ Append result dict to list",
    12: "🏆 Find the post with the highest CTR",
    13: "📣 Print the winner",
}

# ── Session state initialisation ──────────────────────────────────────────────
if "phase" not in st.session_state:
    st.session_state.phase = "identify"   # identify → orient → (trace next)
if "learner" not in st.session_state:
    st.session_state.learner = ""
if "start_time" not in st.session_state:
    st.session_state.start_time = None

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
        placeholder="e.g. Alex, PM-042, or leave as Anonymous",
        max_chars=40,
    )
    col1, col2 = st.columns([1, 3])
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
    st.markdown(f"👋 Hi **{learner}** — let's start.")
    st.markdown(
        """
        ### Step 1 of 4 · Orient

        Read the script below in full.  
        Don't worry about every detail yet — just build a rough mental map:
        - What data does the script start with?
        - What is it trying to compute?
        - Where does the output come from?

        Annotations on the right will guide you.
        """
    )
    st.divider()

    # Render the script with annotations
    st.markdown("#### 📄 `ctr_calculator.py`")
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
                st.markdown(f"<small style='color:#aaa'>{annotation}</small>",
                            unsafe_allow_html=True)

    st.divider()
    st.markdown(
        """
        **Before you continue, ask yourself:**  
        1. What is stored in `posts`?  
        2. What does `ctr` measure?  
        3. What will `print()` output?

        *(You don't need to answer these aloud — they're warm-up prompts.)*
        """
    )
    st.info("Once you feel oriented, click the button below to begin tracing line by line.")

    if st.button("▶  Start Tracing", type="primary"):
        st.session_state.phase = "trace"   # next phase — to be built
        st.rerun()

# ── PHASE: TRACE (placeholder — coming next) ──────────────────────────────────
elif st.session_state.phase == "trace":
    st.title("🔍 PyTrace — Module 1")
    st.info("⚙️ The Trace phase is coming in the next build. Stay tuned!")
    if st.button("← Back to Orient"):
        st.session_state.phase = "orient"
        st.rerun()
