"""Standalone verification of variable tracker execution logic (no Streamlit)."""

import json
import textwrap

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

TRACE_STEPS = [
    {"line": 1},
    {"line": 7},
    {"line": 9},
]

TRACKED_VARS = ["posts", "results", "post", "ctr", "top"]


def _script_code_up_to_line(end_line):
    return "\n".join(
        code for lineno, code in SCRIPT_LINES
        if lineno <= end_line and code.strip()
    )


def _user_vars(namespace):
    return {k: v for k, v in namespace.items() if not k.startswith("__")}


def execute_until_line(end_line, loop_iterations=None):
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
    if step_index >= len(TRACE_STEPS):
        return execute_until_line(13)

    line = TRACE_STEPS[step_index]["line"]
    if line == 9:
        return execute_until_line(9, loop_iterations=1)
    if line == 1:
        return execute_until_line(5)
    return execute_until_line(line)


def format_variable_for_display(value, max_compact_len=80):
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


def main():
    for step_index in range(len(TRACE_STEPS) + 1):
        vars_at_step = get_variables_for_trace_step(step_index)
        label = (
            f"step {step_index} (complete)"
            if step_index >= len(TRACE_STEPS)
            else f"step {step_index} line {TRACE_STEPS[step_index]['line']}"
        )
        print(f"\n=== {label} ===")
        for name in TRACKED_VARS:
            if name in vars_at_step:
                compact, _ = format_variable_for_display(vars_at_step[name])
                print(f"  {name}: {compact}")
            else:
                print(f"  {name}: not yet defined")

    step0 = get_variables_for_trace_step(0)
    assert "posts" in step0 and len(step0["posts"]) == 3
    assert "results" not in step0

    step1 = get_variables_for_trace_step(1)
    assert step1["results"] == []

    step2 = get_variables_for_trace_step(2)
    assert step2["ctr"] == 6.4
    assert step2["post"]["title"] == "How I hit 1M upvotes"
    assert step2["results"] == []

    final = get_variables_for_trace_step(len(TRACE_STEPS))
    assert final["top"]["title"] == "Guide to SEO in 2025"
    print("\n✓ All assertions passed")


if __name__ == "__main__":
    main()
