#!/usr/bin/env python3
"""
generate_compare_html.py
------------------------
Generate compare_results.html from the two output JSON files:
  - deepseek_tasks_output.json   (full task data, responses, usage)
  - deepseek_ragas_results.json  (RAGAS evaluation scores)

Usage:
  python3 generate_compare_html.py [--tasks deepseek_tasks_output.json] \\
                                   [--scores deepseek_ragas_results.json] \\
                                   [--output compare_results.html]
"""

import argparse
import json
from pathlib import Path


def esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def fmt(score: float | None) -> str:
    if score is None:
        return "N/A"
    return f"{score:.3f}"


def fmt_pct(score: float | None) -> str:
    if score is None:
        return "N/A"
    return f"{score * 100:.1f}%"


def bar_width(score: float | None) -> str:
    if score is None:
        return "0"
    return f"{min(score, 1.0) * 100:.0f}"


METRIC_LABELS = {
    "faithfulness": "Faithfulness",
    "context_precision": "Context Precision",
    "context_recall": "Context Recall",
    "answer_relevancy": "Answer Relevancy",
}

METRIC_THRESHOLDS = {
    "faithfulness": 0.7,
    "context_precision": 0.7,
    "context_recall": 0.6,
    "answer_relevancy": 0.7,
}


def score_color(score: float | None, threshold: float) -> str:
    if score is None:
        return "red"
    if score >= threshold:
        return "green"
    if score >= threshold * 0.6:
        return "yellow"
    return "red"


def load_data(tasks_path: Path, scores_path: Path) -> tuple[dict, dict, list[dict]]:
    with tasks_path.open("r") as f:
        tasks_data = json.load(f)
    with scores_path.open("r") as f:
        scores_data = json.load(f)

    tasks_by_id: dict[str, dict] = {}
    for case in tasks_data.get("cases", []):
        tasks_by_id[case["id"]] = case

    results = scores_data.get("results", [])
    return tasks_data, scores_data, results


def build_html(tasks_data: dict, scores_data: dict, results: list[dict], args) -> str:
    usage = scores_data.get("total_usage", {})
    total = len(results)

    # All metrics that have scores
    metric_names = []
    for r in results:
        for k, v in r["scores"].items():
            if v is not None and k not in metric_names:
                metric_names.append(k)

    def avg_score(name: str, items: list[dict]) -> float | None:
        vals = [r["scores"].get(name) for r in items if r["scores"].get(name) is not None]
        return sum(vals) / len(vals) if vals else None

    by_ctx: dict[str, list[dict]] = {}
    by_cat: dict[str, list[dict]] = {}
    for r in results:
        by_ctx.setdefault(r.get("context_type", "unknown"), []).append(r)
        by_cat.setdefault(r.get("category", "unknown"), []).append(r)

    # --- HTML Builder ---
    _parts: list[str] = []

    def w(s: str = ""):
        _parts.append(s)

    w("<!DOCTYPE html>")
    w('<html lang="en">')
    w("<head>")
    w('<meta charset="UTF-8">')
    w('<meta name="viewport" content="width=device-width, initial-scale=1.0">')
    w("<title>PixelForge KG Evaluation — with_source vs with_kg</title>")
    w("<style>")
    w("""  :root {
    --bg: #0d1117;
    --surface: #161b22;
    --surface2: #21262d;
    --border: #30363d;
    --accent: #f78166;
    --kg: #7c5cfc;
    --no-kg: #8b949e;
    --green: #3fb950;
    --yellow: #d29922;
    --red: #f85149;
    --text: #e6edf3;
    --text-dim: #8b949e;
    --radius: 8px;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif;
    background: var(--bg);
    color: var(--text);
    padding: 24px;
    line-height: 1.6;
    max-width: 1200px;
    margin: 0 auto;
  }
  h1 { font-size: 1.6rem; font-weight: 600; margin-bottom: 4px; display: flex; align-items: center; gap: 10px; }
  h1 .sub { font-size: 1rem; font-weight: 400; color: var(--text-dim); }
  .subtitle { color: var(--text-dim); font-size: 0.85rem; margin-bottom: 24px; }
  h2 { font-size: 1.1rem; font-weight: 600; margin-bottom: 14px; margin-top: 32px; display: flex; align-items: center; gap: 8px; }
  h2:first-of-type { margin-top: 0; }
  h3 { font-size: 0.9rem; font-weight: 600; margin-bottom: 10px; }
  .legend {
    display: flex; gap: 16px; flex-wrap: wrap;
    background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius);
    padding: 12px 16px; margin-bottom: 20px; font-size: 0.8rem;
  }
  .legend-item { display: flex; align-items: center; gap: 6px; }
  .legend-dot { width: 12px; height: 12px; border-radius: 3px; display: inline-block; }
  .legend-dot.kg { background: var(--kg); }
  .legend-dot.no { background: var(--no-kg); }
  .legend-dot.green { background: var(--green); }
  .legend-dot.red { background: var(--red); }
  .legend-dot.yellow { background: var(--yellow); }
  .ctx-badge {
    font-size: 0.58rem;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    padding: 2px 6px;
    border-radius: 3px;
    font-weight: 600;
    flex-shrink: 0;
  }
  .ctx-badge.kg { background: var(--kg); color: #fff; }
  .ctx-badge.source { background: var(--no-kg); color: #fff; }
  .stats-row { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 24px; }
  .stat-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 16px 20px;
    flex: 1;
    min-width: 140px;
  }
  .stat-card .label {
    font-size: 0.7rem;
    text-transform: uppercase;
    color: var(--text-dim);
    letter-spacing: 0.5px;
    margin-bottom: 8px;
  }
  .stat-card .stat-row { display: flex; align-items: baseline; gap: 12px; }
  .stat-card .stat-row .pair { display: flex; flex-direction: column; }
  .stat-card .value { font-size: 1.5rem; font-weight: 700; }
  .stat-card .value .label-inline { font-size: 0.65rem; font-weight: 400; color: var(--text-dim); margin-left: 4px; }
  .value.green { color: var(--green); }
  .value.yellow { color: var(--yellow); }
  .value.red { color: var(--red); }
  .value.kg-color { color: var(--kg); }
  .value.no-color { color: var(--no-kg); }
  .explain-box {
    background: var(--surface);
    border: 1px solid var(--border);
    border-left: 3px solid var(--kg);
    border-radius: var(--radius);
    padding: 14px 18px;
    margin-bottom: 20px;
    font-size: 0.85rem;
    line-height: 1.7;
  }
  .explain-box strong { color: var(--kg); }
  .explain-box .no-strong { color: var(--no-kg); }
  .comparison-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; margin-bottom: 24px; }
  @media (max-width: 900px) { .comparison-grid { grid-template-columns: 1fr 1fr; } }
  @media (max-width: 600px) { .comparison-grid { grid-template-columns: 1fr; } }
  .metric-table-wrap {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 14px;
    overflow-x: auto;
  }
  .metric-table-wrap h3 {
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 10px; font-size: 0.85rem;
  }
  .metric-table-wrap h3 .desc { font-size: 0.7rem; font-weight: 400; color: var(--text-dim); }
  .metric-table-wrap h3 .col-headers { display: flex; gap: 8px; font-size: 0.7rem; color: var(--text-dim); }
  .col-kg { color: var(--kg); font-weight: 600; }
  .col-no { color: var(--no-kg); font-weight: 600; }
  table { width: 100%; border-collapse: collapse; font-size: 0.78rem; }
  th, td { padding: 6px 8px; text-align: left; border-bottom: 1px solid var(--border); }
  th { font-size: 0.65rem; text-transform: uppercase; color: var(--text-dim); letter-spacing: 0.4px; font-weight: 600; }
  tr:last-child td { border-bottom: none; }
  td.task-name { max-width: 140px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  td.score-cell { white-space: nowrap; text-align: right; }
  .bar-bg { display: inline-block; width: 50px; height: 10px; background: var(--surface2); border-radius: 3px; vertical-align: middle; margin-right: 6px; overflow: hidden; }
  .bar-fill { height: 100%; border-radius: 3px; min-width: 2px; }
  .bar-fill.kg-bar { background: var(--kg); }
  .bar-fill.no-bar { background: var(--no-kg); }
  .score-green { color: var(--green); font-weight: 600; }
  .score-yellow { color: var(--yellow); font-weight: 600; }
  .score-red { color: var(--red); font-weight: 600; }
  .task-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    margin-bottom: 10px;
    overflow: hidden;
  }
  .task-header {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 12px 16px;
    cursor: pointer;
    user-select: none;
  }
  .task-header:hover { background: rgba(255,255,255,0.02); }
  .task-header .toggle {
    color: var(--text-dim); font-size: 0.75rem; width: 18px; text-align: center;
    flex-shrink: 0;
  }
  .task-header .cat {
    font-size: 0.62rem;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    background: var(--surface2);
    padding: 2px 7px;
    border-radius: 4px;
    color: var(--text-dim);
    flex-shrink: 0;
  }
  .task-header .q { flex: 1; font-size: 0.82rem; }
  .task-header .mini-scores { display: flex; gap: 10px; font-size: 0.7rem; flex-shrink: 0; }
  .task-header .mini-scores .ms { text-align: center; min-width: 50px; }
  .task-header .mini-scores .ms .mv { font-weight: 600; }
  .task-body { display: none; padding: 0 16px 16px; border-top: 1px solid var(--border); }
  .task-body.open { display: block; }
  .score-summary {
    display: flex; gap: 24px; flex-wrap: wrap;
    padding: 12px 0; font-size: 0.78rem;
  }
  .score-summary .ss-item { display: flex; flex-direction: column; gap: 2px; }
  .score-summary .ss-item .ss-label { font-size: 0.65rem; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.3px; }
  .score-summary .ss-item .ss-row { display: flex; gap: 10px; align-items: center; }
  .score-summary .ss-item .ss-row .kg-val { color: var(--kg); font-weight: 600; }
  .score-summary .ss-item .ss-row .no-val { color: var(--no-kg); font-weight: 600; }
  .score-summary .ss-item .ss-row .arrow { color: var(--text-dim); margin: 0 4px; }
  .score-summary .ss-item .ss-row .delta.positive { color: var(--green); }
  .score-summary .ss-item .ss-row .delta.negative { color: var(--red); }
  .score-summary .ss-item .ss-row .delta.neutral { color: var(--text-dim); }
  .response-compare { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 8px; }
  @media (max-width: 700px) { .response-compare { grid-template-columns: 1fr; } }
  .resp-box {
    background: #0d1117;
    border-radius: 6px;
    padding: 12px;
    font-size: 0.74rem;
    max-height: 320px;
    overflow-y: auto;
    white-space: pre-wrap;
    font-family: 'SF Mono', 'Cascadia Code', 'Consolas', 'Liberation Mono', monospace;
    line-height: 1.45;
  }
  .resp-box .label {
    display: block;
    font-size: 0.62rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 8px;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', sans-serif;
    font-weight: 600;
  }
  .resp-box.kg { border-left: 3px solid var(--kg); }
  .resp-box.kg .label { color: var(--kg); }
  .resp-box.source { border-left: 3px solid var(--no-kg); }
  .resp-box.source .label { color: var(--no-kg); }
  .ref-box {
    background: #0d1b2a;
    border: 1px solid #1a3a2a;
    border-radius: 6px;
    padding: 12px;
    font-size: 0.74rem;
    margin-top: 12px;
    white-space: pre-wrap;
    font-family: 'SF Mono', 'Cascadia Code', 'Consolas', 'Liberation Mono', monospace;
    line-height: 1.45;
  }
  .ref-box .label {
    display: block;
    font-size: 0.62rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: var(--green);
    margin-bottom: 6px;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', sans-serif;
    font-weight: 600;
  }
  .filter-bar {
    display: flex;
    gap: 6px;
    margin-bottom: 14px;
    flex-wrap: wrap;
  }
  .filter-btn {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 5px 13px;
    font-size: 0.72rem;
    color: var(--text);
    cursor: pointer;
    transition: all 0.15s;
  }
  .filter-btn:hover { border-color: var(--accent); }
  .filter-btn.active { background: var(--kg); border-color: var(--kg); color: #fff; }
  .filter-btn.active.all { background: var(--accent); border-color: var(--accent); }
  [data-tip] { position: relative; cursor: help; border-bottom: 1px dashed var(--text-dim); }
  [data-tip]:hover::after {
    content: attr(data-tip);
    position: absolute;
    bottom: calc(100% + 6px);
    left: 50%;
    transform: translateX(-50%);
    background: #1a1a2e;
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 0.7rem;
    white-space: nowrap;
    color: var(--text);
    font-weight: 400;
    z-index: 100;
    box-shadow: 0 4px 12px rgba(0,0,0,0.4);
    pointer-events: none;
  }
  @media (max-width: 600px) { [data-tip]:hover::after { white-space: normal; max-width: 260px; } }
  .tooltip-icon { display: inline-flex; align-items: center; justify-content: center; width: 14px; height: 14px; border-radius: 50%; background: var(--surface2); color: var(--text-dim); font-size: 0.6rem; font-weight: 700; cursor: help; margin-left: 4px; vertical-align: middle; line-height: 14px; }
  .token-section { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 16px 20px; margin-bottom: 24px; }
  .token-section h3 { margin-bottom: 12px; font-size: 0.85rem; }
  .token-grid { display: flex; gap: 20px; flex-wrap: wrap; }
  .token-item { display: flex; flex-direction: column; gap: 2px; }
  .token-item .tl { font-size: 0.65rem; text-transform: uppercase; color: var(--text-dim); letter-spacing: 0.4px; }
  .token-item .tv { font-size: 1rem; font-weight: 600; font-variant-numeric: tabular-nums; }
  .token-item .tv.kg-color { color: var(--kg); }
  .token-item .tv.no-color { color: var(--no-kg); }
  .token-item .tv.total { color: var(--accent); }
  .token-item .tv-sub { font-size: 0.65rem; color: var(--text-dim); margin-top: 1px; }
  .token-per-case { font-size: 0.72rem; margin-top: 4px; padding: 6px 0; }
  .token-per-case .tpc-row { display: flex; gap: 16px; flex-wrap: wrap; align-items: center; }
  .token-per-case .tpc-row .tpc-item { display: flex; align-items: center; gap: 4px; }
  .token-per-case .tpc-row .tpc-item .tpc-val { font-weight: 600; }
  .token-per-case .tpc-row .tpc-item .tpc-val.kg-color { color: var(--kg); }
  .token-per-case .tpc-row .tpc-item .tpc-val.no-color { color: var(--no-kg); }
  .task-tokens { font-size: 0.68rem; color: var(--text-dim); display: flex; gap: 10px; padding: 8px 0 4px; border-top: 1px solid var(--border); margin-top: 8px; }
  .task-tokens .tt-item { display: flex; align-items: center; gap: 3px; }
  .task-tokens .tt-item .tt-l { color: var(--text-dim); }
  .task-tokens .tt-item .tt-v { font-weight: 600; }
  .task-tokens .tt-item .tt-v.kg-c { color: var(--kg); }
  .task-tokens .tt-item .tt-v.no-c { color: var(--no-kg); }
  .mt-8 { margin-top: 8px; }
  .mb-8 { margin-bottom: 8px; }
  .text-dim { color: var(--text-dim); }
  .text-sm { font-size: 0.75rem; }
</style>""")
    w("</head>")
    w("<body>")

    # Header
    w('<h1>PixelForge <span class="sub">\u2014 KG-Aided Evaluation</span></h1>')
    w('<div class="subtitle">')
    w('  Comparing DeepSeek answer quality <strong style="color:var(--kg)">with KG</strong> vs <strong style="color:var(--no-kg)">source-only</strong>')
    w('  context on %d PixelForge coding tasks' % (total // 2))
    w("</div>")

    # Legend
    w('<div class="legend">')
    w('<span class="legend-item"><span class="legend-dot kg"></span> With KG \u2014 source + knowledge-graph structural metadata</span>')
    w('<span class="legend-item"><span class="legend-dot no"></span> Source Only \u2014 source files without KG metadata</span>')
    w('<span class="legend-item"><span class="legend-dot green"></span> Passed (score \u2265 threshold)</span>')
    w('<span class="legend-item"><span class="legend-dot red"></span> Failed (score &lt; threshold)</span>')
    w("</div>")

    # Stats
    w('<div class="stats-row">')
    w('  <div class="stat-card"><div class="label">Total Cases</div><div class="value">%d</div></div>' % total)
    w("</div>")

    # Explanation
    w('<div class="explain-box">')
    w("The RAGAS metrics measure different aspects of LLM response quality: ")
    w("<strong>Faithfulness</strong> checks whether the response is factually supported by the provided context. ")
    w("<strong>Context Precision</strong> measures whether relevant context chunks appear higher in the ranking. ")
    w("<strong>Context Recall</strong> measures whether all relevant context chunks were retrieved. ")
    w("Each metric is scored from 0 to 1. ")
    w("<strong style='color:var(--kg)'>KG-aided</strong> responses include source code + knowledge-graph structural metadata, ")
    w('while <strong class="no-strong">source-only</strong> responses include source files without KG metadata.')
    w("</div>")

    # Metric averages
    w("<h2>Metric Averages</h2>")
    w('<div class="stats-row">')
    for m in metric_names:
        avg = avg_score(m, results)
        w('  <div class="stat-card"><div class="label">%s</div><div class="value">%s</div></div>' % (METRIC_LABELS.get(m, m), fmt_pct(avg)))
    w("</div>")

    # Per-metric comparison tables
    w("<h2>Per-Metric Comparison</h2>")
    w('<div class="comparison-grid">')
    for m in metric_names:
        source_list = sorted(
            [(r, r["scores"].get(m)) for r in by_ctx.get("with_source", [])],
            key=lambda x: x[0]["id"],
        )
        kg_list = sorted(
            [(r, r["scores"].get(m)) for r in by_ctx.get("with_kg", [])],
            key=lambda x: x[0]["id"],
        )

        w('<div class="metric-table-wrap">')
        w('<h3><span>%s</span></h3>' % METRIC_LABELS.get(m, m))
        w('<table><tr><th>Task</th><th class="col-kg">With KG</th><th class="col-no">Source Only</th></tr>')

        for (wr, wsc), (or_, osc) in zip(kg_list, source_list):
            # task name
            tn = wr["id"].replace("__with_kg", "").replace("__with_source", "").replace("basic-", "").replace("intermediate-", "").replace("complex-", "").replace("advanced-", "").replace("very_hard-", "").replace("hard-", "")
            w('<tr><td class="task-name" title="%s">%s</td>' % (esc(wr["user_input"][:120]), esc(tn)))
            w('<td class="score-cell"><span class="bar-bg"><span class="bar-fill kg-bar" style="width:%s%%"></span></span><span>%s</span></td>' % (bar_width(wsc), fmt(wsc)))
            w('<td class="score-cell"><span class="bar-bg"><span class="bar-fill no-bar" style="width:%s%%"></span></span><span>%s</span></td>' % (bar_width(osc), fmt(osc)))
            w("</tr>")
        w("</table></div>")
    w("</div>")

    # Context type comparison
    w("<h2>Context Type Comparison</h2>")
    source_list_ctx = by_ctx.get("with_source", [])
    kg_list_ctx = by_ctx.get("with_kg", [])
    if source_list_ctx and kg_list_ctx:
        w('<table><tr><th>Metric</th><th class="col-no">Source Only</th><th class="col-kg">With KG</th><th>Delta</th></tr>')
        for m in metric_names:
            sv = [r["scores"].get(m) for r in source_list_ctx if r["scores"].get(m) is not None]
            kv = [r["scores"].get(m) for r in kg_list_ctx if r["scores"].get(m) is not None]
            aw = sum(sv) / len(sv) if sv else None
            ak = sum(kv) / len(kv) if kv else None
            if aw is not None and ak is not None:
                delta = ak - aw
                d_cls = "positive" if delta > 0 else ("negative" if delta < 0 else "neutral")
                d_str = '<span class="delta %s">%s%+.3f</span>' % (d_cls, "" if delta == 0 else "", delta)
            else:
                d_str = "<span class='neutral'>N/A</span>"
            w("<tr><td><strong>%s</strong></td><td class='no-val'>%s</td><td class='kg-val'>%s</td><td>%s</td></tr>" % (METRIC_LABELS.get(m, m), fmt(aw), fmt(ak), d_str))
        w("</table>")
    else:
        w('<p class="text-dim">No context-type comparison available.</p>')

    # Category breakdown
    w("<h2>Category Breakdown</h2>")
    if by_cat:
        w("<table><tr><th>Category</th><th>Total</th>")
        for m in metric_names:
            w("<th>%s avg</th>" % METRIC_LABELS.get(m, m))
        w("</tr>")
        for cat, items in sorted(by_cat.items()):
            w("<tr><td><strong>%s</strong></td><td>%d</td>" % (esc(cat), len(items)))
            for m in metric_names:
                vals = [r["scores"].get(m) for r in items if r["scores"].get(m) is not None]
                avg = sum(vals) / len(vals) if vals else None
                w("<td>%s</td>" % fmt(avg))
            w("</tr>")
        w("</table>")
    else:
        w('<p class="text-dim">No category data available.</p>')

    # Token Usage
    w("<h2>Token Usage</h2>")
    w('<div class="token-section">')
    w("<h3>Evaluation (RAGAS scoring)</h3>")
    w('<div class="token-grid">')
    for k in ("prompt_tokens", "completion_tokens", "total_tokens"):
        v = usage.get(k, 0)
        w('  <div class="token-item"><span class="tv total">%s</span><span class="tl">%s</span></div>' % (f"{v:,}", k))
    w("</div>")

    # Per-case token usage from tasks output
    tasks_cases = tasks_data.get("cases", [])
    kg_tokens = [c["usage"]["total_tokens"] for c in tasks_cases if c.get("context_type") == "with_kg"]
    src_tokens = [c["usage"]["total_tokens"] for c in tasks_cases if c.get("context_type") == "with_source"]
    if kg_tokens or src_tokens:
        w('<div class="token-per-case">')
        w("<h3>Task generation (DeepSeek calls)</h3>")
        w('<div class="tpc-row">')
        if kg_tokens:
            avg_kg = sum(kg_tokens) / len(kg_tokens)
            w('<span class="tpc-item"><span class="tpc-val kg-color">%s</span> avg/task with KG</span>' % f"{avg_kg:,.0f}")
        if src_tokens:
            avg_src = sum(src_tokens) / len(src_tokens)
            w('<span class="tpc-item"><span class="tpc-val no-color">%s</span> avg/task source-only</span>' % f"{avg_src:,.0f}")
        w("</div></div>")
    w("</div>")

    # Task detail cards
    w("<h2>Task Details</h2>")
    w('<div class="filter-bar">')
    cats = sorted(set(r.get("category", "unknown") for r in results))
    w('<button class="filter-btn active all" data-filter="all">All</button>')
    for cat in cats:
        w('<button class="filter-btn" data-filter="%s">%s</button>' % (esc(cat), esc(cat)))
    w('</div>')

    tasks_by_id = {}
    for case in tasks_data.get("cases", []):
        tasks_by_id[case["id"]] = case

    for r in sorted(results, key=lambda x: x["id"]):
        tid = r["id"]
        task = tasks_by_id.get(tid, {})

        scores = r["scores"]
        current_ctx = "with_kg" if "_with_kg" in tid else "with_source"
        ctx_badge = '<span class="ctx-badge kg">With KG</span>' if current_ctx == "with_kg" else '<span class="ctx-badge source">Source Only</span>'
        w('<div class="task-card" data-category="%s" data-ctx="%s">' % (esc(r.get("category", "")), current_ctx))
        w('<div class="task-header" onclick="toggleTask(this)">')
        w('<span class="toggle">\u25b6</span>')
        w('%s' % ctx_badge)
        w('<span class="cat">%s</span>' % esc(r.get("category", "")))
        w('<span class="q">%s</span>' % esc(r["user_input"][:120]))
        w('<span class="mini-scores">')
        for m in metric_names:
            sc = scores.get(m)
            c = score_color(sc, METRIC_THRESHOLDS.get(m, 0.5))
            w('<span class="ms"><span class="mv score-%s">%s</span><br><span class="text-dim text-sm">%s</span></span>' % (c, fmt(sc), METRIC_LABELS.get(m, m).split()[-1].lower()))
        w("</span></div>")

        w('<div class="task-body">')

        # Score summary
        w('<div class="score-summary">')
        for m in metric_names:
            sc = scores.get(m)
            w('<div class="ss-item">')
            w('<span class="ss-label">%s</span>' % METRIC_LABELS.get(m, m))
            w('<span class="ss-row"><span style="font-size:1.1em;font-weight:700">%s</span></span>' % fmt(sc))
            w('</div>')
        w("</div>")

        # Tokens for this case
        task_usage = task.get("usage", {})
        if task_usage:
            w('<div class="task-tokens">')
            for k in ("prompt_tokens", "completion_tokens", "total_tokens"):
                v = task_usage.get(k, 0)
                w('<span class="tt-item"><span class="tt-l">%s</span> <span class="tt-v">%s</span></span>' % (k.replace("_", " "), f"{v:,}"))
            w("</div>")

        # Response comparison
        current_ctx = "with_kg" if "_with_kg" in tid else "with_source"
        other_ctx = "with_source" if current_ctx == "with_kg" else "with_kg"
        other_id = tid.replace(current_ctx, other_ctx)
        other_task = tasks_by_id.get(other_id)

        def resp_panel(ctx: str, src_task: dict | None, fallback: str) -> str:
            label = "Source Only" if ctx == "with_source" else "With KG"
            css_cls = "source" if ctx == "with_source" else "kg"
            text = src_task.get("response", fallback) if src_task else fallback
            return '<div class="resp-box %s"><span class="label">%s</span>%s</div>' % (css_cls, label, esc(text[:2000]))

        w('<div class="response-compare">')
        w(resp_panel(other_ctx, other_task, ""))
        w(resp_panel(current_ctx, task, task.get("response", "")))
        w("</div>")

        # Reference
        ref = r.get("reference", "")
        if ref:
            w('<div class="ref-box"><span class="label">Reference Answer</span>%s</div>' % esc(ref))

        w("</div></div>")

    # JS
    w("<script>")
    w("""
function toggleTask(header) {
  var body = header.nextElementSibling;
  var toggle = header.querySelector('.toggle');
  if (body.classList.contains('open')) {
    body.classList.remove('open');
    toggle.textContent = '\\u25b6';
  } else {
    body.classList.add('open');
    toggle.textContent = '\\u25bc';
  }
}

document.querySelectorAll('.filter-btn').forEach(function(btn) {
  btn.addEventListener('click', function() {
    var filter = this.getAttribute('data-filter');
    document.querySelectorAll('.filter-btn').forEach(function(b) { b.classList.remove('active'); });
    this.classList.add('active');
    document.querySelectorAll('.task-card').forEach(function(card) {
      if (filter === 'all') {
        card.style.display = '';
      } else {
        card.style.display = card.getAttribute('data-category') === filter ? '' : 'none';
      }
    });
  });
});
""")
    w("</script>")
    w("</body></html>")

    return "\n".join(_parts)


def main():
    parser = argparse.ArgumentParser(description="Generate compare_results.html from evaluation JSON files.")
    parser.add_argument("--tasks", default=".understand-anything/ragas/deepseek_tasks_output.json", help="Path to tasks output JSON")
    parser.add_argument("--scores", default=".understand-anything/ragas/deepseek_ragas_results.json", help="Path to RAGAS scores JSON")
    parser.add_argument("--output", default=".understand-anything/ragas/compare_results.html", help="Output HTML path")
    args = parser.parse_args()

    tasks_path = Path(args.tasks)
    scores_path = Path(args.scores)

    if not tasks_path.exists():
        raise SystemExit(f"Error: tasks file not found: {tasks_path}")
    if not scores_path.exists():
        raise SystemExit(f"Error: scores file not found: {scores_path}")

    tasks_data, scores_data, results = load_data(tasks_path, scores_path)
    print(f"Loaded {len(results)} results from {scores_path.name}")
    print(f"Loaded {len(tasks_data.get('cases', []))} task cases from {tasks_path.name}")

    html = build_html(tasks_data, scores_data, results, args)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    print(f"Wrote {len(html):,} bytes to {output_path}")


if __name__ == "__main__":
    main()
