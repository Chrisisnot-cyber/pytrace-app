
import json
import textwrap
import streamlit as st
import datetime
import google.generativeai as genai

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PyTrace",
    page_icon="🔍",
    layout="centered",
)

# ── Gemini API setup ──────────────────────────────────────────────────────────
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("GEMINI_API_KEY not found in secrets. AI hints will not work.")

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

# ── Trace steps (line, variable to predict, correct answer, hint context) ─────
TRACE_STEPS = [
    {
        "line": 1,
        "prompt": "After line 1 runs, what is the value of `posts`?",
        "answer": "a list of 3 dictionaries",
        "check": lambda v: "list" in v.lower() and "3" in v,
    },
    {
        "line": 7,
        "prompt": "After line 7 runs, what is the value of `results`?",
        "answer": "an empty list []",
        "check": lambda v: "empty" in v.lower() or "[]" in v,
    },
    {
        "line": 9,
        "prompt": "In the first loop iteration (post 'How I hit 1M upvotes'), what is `ctr` after line 9?",
        "answer": "6.4",
        "check": lambda v: "6.4" in v or "6.40" in v,
    },
]

PREDICTION_OPTIONS = [
    "A — It prints the post title and its CTR percentage, e.g. 'Top post: How I hit 1M upvotes — CTR 6.4%'",
    "B — It prints a list of all three posts ranked by CTR",
    "C — It prints the raw number of clicks for the most-clicked post",
    "D — I'm not sure yet — I need to trace through the code first",
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
if "trace_step" not in st.session_state:
    st.session_state.trace_step = 0  # current step index
if "trace_attempts" not in st.session_state:
    st.session_state.trace_attempts = []  # history of attempts
if "hint_shown" not in st.session_state:
    st.session_state.hint_shown = False

TRACKED_VARS = ["posts", "results", "post", "ctr", "top"]
MAX_COMPACT_VALUE_LEN = 80


def _script_code_up_to_line(end_line):
    return "\n".join(
        code for lineno, code in SCRIPT_LINES
        if lineno <= end_line and code.strip()
    )


def _user_vars(namespace):
    return {k: v for k, v in namespace.items() if not k.startswith("__")}


def execute_until_line(end_line, loop_iterations=None):
    """Execute the traced script up to end_line and return user-defined variables."""
    namespace = {"__builtins__": __builtins__}
    loop_start = 8

    if end_line >= loop_start and loop_iterations is not None:
        exec(_script_code_up_to_line(loop_start - 1), namespace)
        body_code = textwrap.dedent("\n".join(
            code for lineno, code in SCRIPT_LINES
            if loop_start < lineno <= end_line and code.strip()
        ))
        for i, post in enumerate(namespace["posts"]):
            if i >= loop_iterations:
                break
            namespace["post"] = post
            exec(body_code, namespace)
        return _user_vars(namespace)

    if end_line == 1:
        end_line = 5

    max_line = max(lineno for lineno, _ in SCRIPT_LINES)
    for try_through in range(end_line, max_line + 1):
        code = _script_code_up_to_line(try_through)
        try:
            compile(code, "<pytrace>", "exec")
        except SyntaxError:
            continue
        exec(code, namespace)
        break

    return _user_vars(namespace)


def get_variables_for_trace_step(step_index):
    """Return variable values at the pedagogical checkpoint for a trace step."""
    if step_index >= len(TRACE_STEPS):
        return execute_until_line(13)

    line = TRACE_STEPS[step_index]["line"]
    if line == 9:
        return execute_until_line(9, loop_iterations=1)
    if line == 1:
        return execute_until_line(5)
    return execute_until_line(line)


def format_variable_for_display(value, max_compact_len=MAX_COMPACT_VALUE_LEN):
    """Format a Python value for the tracker table; return (compact, full_or_none)."""
    if isinstance(value, float):
        return str(round(value, 2)), None

    if isinstance(value, (list, dict)):
        compact = json.dumps(value, separators=(",", ":"))
        if len(compact) <= max_compact_len:
            return compact, None
        if isinstance(value, list):
            summary = f"list with {len(value)} items"
        else:
            summary = f"dict with {len(value)} keys"
        return summary, json.dumps(value, indent=2)

    val_str = repr(value)
    if len(val_str) <= max_compact_len:
        return val_str, None
    return val_str[:max_compact_len] + "...", val_str


def get_changed_variables(current_vars, previous_vars):
    changed = []
    for name in TRACKED_VARS:
        if name in current_vars and (
            name not in previous_vars or previous_vars[name] != current_vars[name]
        ):
            changed.append(name)
    return changed


# ── Helper: call Gemini for hint ──────────────────────────────────────────────
def get_gemini_hint(line_code, learner_answer, correct_answer, prompt_text):
    """Call Gemini to generate a scaffolded hint for an incorrect answer."""
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        system_prompt = f"""            You are a patient Python tutor helping a product manager learn to trace code.
The learner is tracing this line of code:
```python
{line_code}
```

Question: {prompt_text}
Learner's answer: "{learner_answer}"
Correct answer: {correct_answer}

Provide a short, scaffolded hint (1-2 sentences) that guides them toward the right answer WITHOUT giving it away directly. Use the Graesser escalation approach: start with a pump ("What do you think happens to X here?"), then a directional hint if needed.
"""
        response = model.generate_content(system_prompt)
        return response.text.strip()
    except Exception as e:
        return f"⚠️ Could not generate hint (API error: {str(e)}). Try again or ask for help."

# ══════════════════════════════════════════════════════════════════════════════
# PHASE: IDENTIFY
# ══════════════════════════════════════════════════════════════════════════════
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

# ══════════════════════════════════════════════════════════════════════════════
# PHASE: ORIENT
# ══════════════════════════════════════════════════════════════════════════════
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

# ══════════════════════════════════════════════════════════════════════════════
# PHASE: TRACE
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.phase == "trace":
    st.title("🔍 PyTrace — Module 1")
    st.caption(f"Step 2 of 4 · Trace  ·  Learner: {st.session_state.learner}")
    st.divider()

    # Show their Orient prediction as context ──────────────────────────────
    st.markdown("**Your prediction from Orient:**")
    st.info(st.session_state.prediction)
    st.markdown("Now let's trace through the code line by line to verify.")
    st.divider()

    # Dynamic variable state tracker ────────────────────────────────────────
    st.markdown("### 📊 Variable state tracker")
    st.caption("As we trace, we'll track what each variable holds at each step.")

    current_step = st.session_state.trace_step
    current_vars = get_variables_for_trace_step(current_step)
    previous_vars = (
        get_variables_for_trace_step(current_step - 1) if current_step > 0 else {}
    )
    changed_vars = get_changed_variables(current_vars, previous_vars)
    if changed_vars:
        st.caption(f"Changed since last step: {', '.join(changed_vars)}")

    var_table_data = []
    expanders = []
    for var_name in TRACKED_VARS:
        if var_name in current_vars:
            compact, full = format_variable_for_display(current_vars[var_name])
            display_value = compact
            if var_name in changed_vars:
                display_value = f"→ {compact}"
            var_table_data.append({"Variable": var_name, "Current Value": display_value})
            if full:
                expanders.append((var_name, full))
        else:
            var_table_data.append(
                {"Variable": var_name, "Current Value": "not yet defined"}
            )

    st.table(var_table_data)
    for var_name, full_value in expanders:
        with st.expander(f"Full value of `{var_name}`"):
            st.code(full_value, language="json")
    # Step-by-step prediction ───────────────────────────────────────────────
    if current_step < len(TRACE_STEPS):
        step = TRACE_STEPS[current_step]
        st.markdown(f"### Line {step['line']}")
        st.code(SCRIPT_LINES[step['line'] - 1][1], language="python")
        st.markdown(step['prompt'])

        # Input form ────────────────────────────────────────────────────────
        answer = st.text_input("Your answer:", key=f"answer_{current_step}")

        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("Submit", type="primary", use_container_width=True):
                if not answer.strip():
                    st.warning("Please enter an answer.")
                else:
                    is_correct = step['check'](answer)
                    if is_correct:
                        st.success(f"✓ Correct! The answer is: {step['answer']}")
                        st.session_state.trace_step += 1
                        st.session_state.hint_shown = False
                        st.session_state.trace_attempts.append({
                            "step": current_step,
                            "answer": answer,
                            "correct": True,
                        })
                        st.rerun()
                    else:
                        # INCORRECT — call Gemini for hint ─────────────────
                        st.error("✗ Not quite. Let's get a hint.")
                        hint = get_gemini_hint(
                            SCRIPT_LINES[step['line'] - 1][1],
                            answer,
                            step['answer'],
                            step['prompt'],
                        )
                        st.info(f"💡 Hint: {hint}")
                        st.session_state.hint_shown = True
                        st.session_state.trace_attempts.append({
                            "step": current_step,
                            "answer": answer,
                            "correct": False,
                        })
    else:
        # All steps complete ────────────────────────────────────────────────
        st.success("🎉 You've completed the trace!")
        st.markdown(
            "You've walked through the entire script. Now you know "
            "exactly what it does — and you can verify your original prediction."
        )
        if st.button("Continue to Summary"):
            st.session_state.phase = "summary"
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PHASE: SUMMARY (placeholder)
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.phase == "summary":
    st.title("🔍 PyTrace — Module 1")
    st.caption(f"Step 4 of 4 · Summary  ·  Learner: {st.session_state.learner}")
    st.divider()
    st.markdown(
        """
        **Session complete!**

        Summary and CSV download will be built in the next increment.
        """
    )
    if st.button("← Back to Trace"):
        st.session_state.phase = "trace"
        st.rerun()
