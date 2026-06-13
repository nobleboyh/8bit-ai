#!/usr/bin/env python3
"""
evaluate_deepseek_ragas.py
-------------------------
Score previously-generated LLM responses using RAGAS metrics (Faithfulness,
Context Precision, Context Recall, Answer Relevancy) through a DeepSeek
OpenAI-compatible endpoint.

Usage:
  export DEEPSEEK_API_KEY=...
  python3.12 evaluate_deepseek_ragas.py --input .understand-anything/ragas/deepseek_tasks_output.json

Optional answer relevancy:
  export DEEPSEEK_EMBED_MODEL=<embedding-model-id>
  # If DeepSeek embedding endpoint/model is unavailable, answer_relevancy is skipped.
"""

import argparse
import asyncio
import json
import math
import os
import sys
import threading
from pathlib import Path


def _patch_langchain_vertexai() -> None:
    import types

    try:
        from langchain_google_vertexai import ChatVertexAI
    except ImportError:
        ChatVertexAI = None  # type: ignore

    stub = types.ModuleType("langchain_community.chat_models.vertexai")
    stub.ChatVertexAI = ChatVertexAI  # type: ignore
    sys.modules.setdefault("langchain_community.chat_models.vertexai", stub)

    try:
        from langchain_community.llms import VertexAI  # noqa: F401
    except ImportError:
        llms_stub = types.ModuleType("langchain_community.llms")
        llms_stub.VertexAI = None  # type: ignore
        sys.modules.setdefault("langchain_community.llms", llms_stub)


_patch_langchain_vertexai()

try:
    from openai import AsyncOpenAI
    from ragas.embeddings import embedding_factory
    from ragas.llms import llm_factory
    from ragas.metrics.collections import (
        AnswerRelevancy,
        ContextPrecision,
        ContextRecall,
        Faithfulness,
    )
    from ragas.run_config import RunConfig
except ImportError as e:
    raise SystemExit(f"Missing dependency: {e}")


class UsageTracker:
    """Thread-safe cumulative token usage tracker for AsyncOpenAI responses."""

    def __init__(self):
        self._lock = threading.Lock()
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.total_tokens = 0

    def add(self, usage) -> None:
        if usage is None:
            return
        with self._lock:
            self.prompt_tokens += usage.prompt_tokens or 0
            self.completion_tokens += usage.completion_tokens or 0
            self.total_tokens += usage.total_tokens or 0

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "prompt_tokens": self.prompt_tokens,
                "completion_tokens": self.completion_tokens,
                "total_tokens": self.total_tokens,
            }


class TrackingAsyncOpenAI(AsyncOpenAI):
    """Subclass of AsyncOpenAI that records token usage from every API response.

    Inheriting from AsyncOpenAI ensures isinstance(client, AsyncOpenAI) passes
    for RAGAS/instructor compatibility.
    """

    def __init__(self, *args, tracker: UsageTracker, **kwargs):
        super().__init__(*args, **kwargs)
        self._tracker = tracker
        self._patch_completions()
        self._patch_embeddings()

    def _patch_completions(self):
        completions = self.chat.completions
        orig_create = completions.create

        async def tracked_create(*args, **kwargs):
            resp = await orig_create(*args, **kwargs)
            self._tracker.add(resp.usage)
            return resp

        completions.create = tracked_create

    def _patch_embeddings(self):
        if not hasattr(self, "embeddings"):
            return
        embed = self.embeddings
        orig_create = embed.create

        async def tracked_create(*args, **kwargs):
            resp = await orig_create(*args, **kwargs)
            self._tracker.add(resp.usage)
            return resp

        embed.create = tracked_create


DEEPSEEK_BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-flash")
DEEPSEEK_EMBED_MODEL = os.environ.get("DEEPSEEK_EMBED_MODEL", "")
RAGAS_DIR = Path(__file__).resolve().parent
RAGAS_MAX_TOKENS = int(os.environ.get("RAGAS_LLM_MAX_TOKENS", "16384"))
RAGAS_SYSTEM_PROMPT = (
    "You are a strict RAGAS metric scorer. Return only the structured JSON object "
    "requested by the response schema. Do not include analysis, markdown, or prose."
)
def _as_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def _normalize_case(raw: dict, index: int) -> dict:
    user_input = raw.get("user_input") or raw.get("question") or raw.get("task")
    response = raw.get("response") or raw.get("answer")
    contexts = (
        raw.get("retrieved_contexts")
        if "retrieved_contexts" in raw
        else raw.get("contexts", raw.get("context"))
    )
    reference = raw.get("reference") or raw.get("ground_truth")

    missing = []
    if not user_input:
        missing.append("user_input/question")
    if not response:
        missing.append("response/answer")
    if contexts is None:
        missing.append("retrieved_contexts/contexts/context")
    if missing:
        raise ValueError(f"case #{index + 1} missing required field(s): {', '.join(missing)}")

    return {
        "id": raw.get("id") or raw.get("name") or f"case_{index + 1}",
        "user_input": str(user_input),
        "response": str(response),
        "retrieved_contexts": _as_list(contexts),
        "reference": str(reference) if reference is not None else None,
        "context_type": raw.get("context_type", "unknown"),
        "category": raw.get("category", "unknown"),
    }


def load_cases(path: Path) -> tuple[list[dict], str | None]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    token = None
    if isinstance(data, dict):
        token = data.get("token")
        if "cases" in data:
            data = data["cases"]
        else:
            data = [data]
    if not isinstance(data, list):
        raise ValueError("input JSON must be an object, a list, or an object with a 'cases' list")
    return [_normalize_case(item, idx) for idx, item in enumerate(data)], token


def build_deepseek_llm(api_key: str | None = None, tracker: UsageTracker | None = None):
    if not api_key:
        api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY is required")

    if tracker:
        client = TrackingAsyncOpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL, tracker=tracker)
    else:
        client = AsyncOpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL)
    return llm_factory(
        DEEPSEEK_MODEL,
        provider="openai",
        client=client,
        max_tokens=RAGAS_MAX_TOKENS,
        system_prompt=RAGAS_SYSTEM_PROMPT,
    )


def build_deepseek_embeddings(api_key: str | None = None, tracker: UsageTracker | None = None):
    if not DEEPSEEK_EMBED_MODEL:
        print(
            "  [INFO] DEEPSEEK_EMBED_MODEL is not set; skipping answer_relevancy.",
            file=sys.stderr,
        )
        return None

    if not api_key:
        api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        return None

    if tracker:
        client = TrackingAsyncOpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL, tracker=tracker)
    else:
        client = AsyncOpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL)
    return embedding_factory(
        provider="openai",
        model=DEEPSEEK_EMBED_MODEL,
        client=client,
    )


def _metric_value(result):
    value = getattr(result, "value", result)
    try:
        value = float(value)
    except (TypeError, ValueError):
        return value
    if math.isnan(value) or math.isinf(value):
        return None
    return value


async def score_case(case: dict, metrics: list, timeout: float | None) -> dict:
    scores = {}
    for metric in metrics:
        name = getattr(metric, "name", metric.__class__.__name__)
        print(f"  scoring {case['id']} / {name} ...")
        try:
            kwargs = {"user_input": case["user_input"]}
            if name == "faithfulness":
                kwargs.update(
                    {
                        "response": case["response"],
                        "retrieved_contexts": case["retrieved_contexts"],
                    }
                )
            elif name == "context_precision":
                if not case["reference"]:
                    scores[name] = None
                    continue
                kwargs.update(
                    {
                        "reference": case["reference"],
                        "retrieved_contexts": case["retrieved_contexts"],
                    }
                )
            elif name == "context_recall":
                if not case["reference"]:
                    scores[name] = None
                    continue
                kwargs.update(
                    {
                        "reference": case["reference"],
                        "retrieved_contexts": case["retrieved_contexts"],
                    }
                )
            elif name == "answer_relevancy":
                kwargs["response"] = case["response"]
            else:
                kwargs.update(
                    {
                        "response": case["response"],
                        "reference": case["reference"],
                        "retrieved_contexts": case["retrieved_contexts"],
                    }
                )

            result = await asyncio.wait_for(metric.ascore(**kwargs), timeout=timeout)
            scores[name] = _metric_value(result)
        except Exception as e:
            print(f"  [WARN] {case['id']} / {name} failed: {e}", file=sys.stderr)
            scores[name] = None
    return scores


async def run(
    input_path: Path,
    output_path: Path,
    report_path: Path | None,
    timeout: float | None,
    _thresholds: dict,
    token: str | None = None,
) -> None:
    cases, file_token = load_cases(input_path)
    token = token or file_token
    print(f"Loaded {len(cases)} case(s) from {input_path}")
    print(f"Using DeepSeek endpoint: {DEEPSEEK_BASE_URL}")
    print(f"Using DeepSeek model   : {DEEPSEEK_MODEL}")

    usage_tracker = UsageTracker()
    llm = build_deepseek_llm(api_key=token, tracker=usage_tracker)
    embeddings = build_deepseek_embeddings(api_key=token, tracker=usage_tracker)

    metrics = [
        Faithfulness(llm=llm),
        ContextPrecision(llm=llm),
        ContextRecall(llm=llm),
    ]
    if embeddings is not None:
        metrics.append(AnswerRelevancy(llm=llm, embeddings=embeddings))

    results = []
    for case in cases:
        scores = await score_case(case, metrics, timeout)
        results.append(
            {
                "id": case["id"],
                "user_input": case["user_input"],
                "reference": case["reference"],
                "response_preview": case["response"][:500],
                "context_count": len(case["retrieved_contexts"]),
                "context_type": case.get("context_type", "unknown"),
                "category": case.get("category", "unknown"),
                "scores": scores,
            }
        )

    total_usage = usage_tracker.snapshot()
    output = {
        "total_usage": total_usage,
        "results": results,
    }
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
    print(f"Results saved to {output_path}")
    print(f"Total token usage: {total_usage}")

    # Metric averages by context type
    by_ctx: dict[str, list[dict]] = {}
    for r in results:
        by_ctx.setdefault(r.get("context_type", "unknown"), []).append(r)

    metric_names = [k for k in results[0]["scores"] if results[0]["scores"][k] is not None]
    print("\nMetric averages:")
    for ctx, items in sorted(by_ctx.items()):
        print(f"  {ctx}:")
        for m in metric_names:
            vals = [r["scores"].get(m) for r in items if r["scores"].get(m) is not None]
            if vals:
                avg = sum(vals) / len(vals)
                print(f"    {m}: {avg:.3f}")

    # Generate HTML report
    if report_path:
        try:
            html = build_results_html(results, total_usage, input_path)
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(html, encoding="utf-8")
            print(f"HTML report saved to {report_path}")
        except Exception as e:
            print(f"  [WARN] HTML report generation failed: {e}", file=sys.stderr)


# ── HTML report builder ───────────────────────────────────────────────

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


def _esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _fmt(score: float | None) -> str:
    if score is None:
        return "N/A"
    return f"{score:.3f}"


def _fmt_pct(score: float | None) -> str:
    if score is None:
        return "N/A"
    return f"{score * 100:.1f}%"


def _bar_width(score: float | None) -> str:
    if score is None:
        return "0"
    return f"{min(score, 1.0) * 100:.0f}"


def _score_color(score: float | None, threshold: float) -> str:
    if score is None:
        return "red"
    if score >= threshold:
        return "green"
    if score >= threshold * 0.6:
        return "yellow"
    return "red"


def build_results_html(
    results: list[dict],
    total_usage: dict,
    input_path: Path,
) -> str:
    total = len(results)
    metric_names = []
    for r in results:
        for k, v in r["scores"].items():
            if v is not None and k not in metric_names:
                metric_names.append(k)

    def avg(name: str) -> float | None:
        vals = [r["scores"].get(name) for r in results if r["scores"].get(name) is not None]
        return sum(vals) / len(vals) if vals else None

    by_cat: dict[str, list[dict]] = {}
    for r in results:
        by_cat.setdefault(r.get("category", "unknown"), []).append(r)

    parts: list[str] = []
    def w(s: str = ""):
        parts.append(s)

    w("<!DOCTYPE html>")
    w('<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">')
    w(f"<title>RAGAS Evaluation Results — {total} case(s)</title>")
    w("<style>")
    w("""
:root {
  --bg: #0d1117; --surface: #161b22; --surface2: #21262d;
  --border: #30363d; --green: #3fb950; --yellow: #d29922;
  --red: #f85149; --text: #e6edf3; --text-dim: #8b949e;
  --accent: #f78166; --radius: 8px;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif;
  background: var(--bg); color: var(--text);
  padding: 24px; line-height: 1.6; max-width: 1000px; margin: 0 auto;
}
h1 { font-size: 1.4rem; font-weight: 600; margin-bottom: 4px; }
.subtitle { color: var(--text-dim); font-size: 0.85rem; margin-bottom: 20px; }
h2 { font-size: 1.1rem; font-weight: 600; margin: 28px 0 14px; }
.stats-row { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 20px; }
.stat-card {
  background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius);
  padding: 14px 18px; flex: 1; min-width: 120px;
}
.stat-card .label { font-size: 0.65rem; text-transform: uppercase; color: var(--text-dim); letter-spacing: 0.4px; margin-bottom: 6px; }
.stat-card .value { font-size: 1.4rem; font-weight: 700; }
.value.green { color: var(--green); }
.value.yellow { color: var(--yellow); }
.value.red { color: var(--red); }
.metric-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; margin-bottom: 24px; }
.metric-card {
  background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius);
  padding: 14px;
}
.metric-card .label { font-size: 0.7rem; color: var(--text-dim); margin-bottom: 6px; }
.metric-card .score { font-size: 1.25rem; font-weight: 700; }
.token-section {
  background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius);
  padding: 14px 18px; margin-bottom: 24px;
}
.token-section h3 { font-size: 0.85rem; margin-bottom: 10px; }
.token-grid { display: flex; gap: 20px; flex-wrap: wrap; }
.token-item { display: flex; flex-direction: column; gap: 2px; }
.token-item .tl { font-size: 0.65rem; text-transform: uppercase; color: var(--text-dim); letter-spacing: 0.4px; }
.token-item .tv { font-size: 1rem; font-weight: 600; font-variant-numeric: tabular-nums; }
.token-item .tv.total { color: var(--accent); }
.category-table {
  background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius);
  overflow: hidden; margin-bottom: 24px;
}
.category-table table { width: 100%; border-collapse: collapse; font-size: 0.82rem; }
.category-table th, .category-table td { padding: 8px 14px; text-align: left; border-bottom: 1px solid var(--border); }
.category-table th { font-size: 0.65rem; text-transform: uppercase; color: var(--text-dim); letter-spacing: 0.4px; font-weight: 600; background: var(--surface2); }
.task-card {
  background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius);
  margin-bottom: 10px; overflow: hidden;
}
.task-header {
  display: flex; align-items: center; gap: 10px;
  padding: 12px 16px; cursor: pointer; user-select: none;
}
.task-header:hover { background: rgba(255,255,255,0.02); }
.task-header .toggle { color: var(--text-dim); font-size: 0.75rem; width: 18px; text-align: center; flex-shrink: 0; }
.task-header .num { font-size: 0.7rem; color: var(--text-dim); flex-shrink: 0; min-width: 28px; }
.task-header .cat {
  font-size: 0.62rem; text-transform: uppercase; letter-spacing: 0.4px;
  background: var(--surface2); padding: 2px 7px; border-radius: 4px;
  color: var(--text-dim); flex-shrink: 0;
}
.task-header .q { flex: 1; font-size: 0.82rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.task-header .mini-scores { display: flex; gap: 10px; font-size: 0.7rem; flex-shrink: 0; }
.task-header .mini-scores .ms { text-align: center; min-width: 48px; }
.task-header .mini-scores .ms .mv { font-weight: 600; }
.score-green { color: var(--green); font-weight: 600; }
.score-yellow { color: var(--yellow); font-weight: 600; }
.score-red { color: var(--red); font-weight: 600; }
.task-body { display: none; padding: 0 16px 16px; border-top: 1px solid var(--border); }
.task-body.open { display: block; }
.score-summary { display: flex; gap: 20px; flex-wrap: wrap; padding: 12px 0; font-size: 0.82rem; }
.score-summary .ss-item { display: flex; flex-direction: column; gap: 2px; }
.score-summary .ss-item .ss-label { font-size: 0.65rem; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.3px; }
.resp-box {
  background: #0d1117; border-radius: 6px; padding: 12px;
  font-size: 0.74rem; max-height: 360px; overflow-y: auto;
  white-space: pre-wrap; font-family: 'SF Mono', 'Cascadia Code', 'Consolas', 'Liberation Mono', monospace;
  line-height: 1.45; margin-top: 8px; border-left: 3px solid var(--green);
}
.resp-box .label { display: block; font-size: 0.62rem; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', sans-serif; font-weight: 600; }
.ref-box {
  background: #0d1b2a; border: 1px solid #1a3a2a; border-radius: 6px; padding: 12px;
  font-size: 0.74rem; margin-top: 10px; white-space: pre-wrap;
  font-family: 'SF Mono', 'Cascadia Code', 'Consolas', 'Liberation Mono', monospace; line-height: 1.45;
}
.ref-box .label { display: block; font-size: 0.62rem; text-transform: uppercase; letter-spacing: 0.5px; color: var(--green); margin-bottom: 4px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', sans-serif; font-weight: 600; }
.filter-bar {
  display: flex; gap: 6px; margin-bottom: 14px; flex-wrap: wrap;
}
.filter-btn {
  background: var(--surface); border: 1px solid var(--border); border-radius: 20px;
  padding: 5px 13px; font-size: 0.72rem; color: var(--text); cursor: pointer; transition: all 0.15s;
}
.filter-btn:hover { border-color: var(--accent); }
.filter-btn.active { background: var(--accent); border-color: var(--accent); color: #fff; }
.filter-btn.active.all { background: var(--accent); border-color: var(--accent); }
.bar-bg { display: inline-block; width: 50px; height: 10px; background: var(--surface2); border-radius: 3px; vertical-align: middle; margin-right: 6px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 3px; min-width: 2px; background: var(--green); }
.bar-fill.yellow { background: var(--yellow); }
.bar-fill.red { background: var(--red); }
.text-dim { color: var(--text-dim); }
.text-sm { font-size: 0.75rem; }
""")
    w("</style></head><body>")

    # Header
    w(f'<h1>RAGAS Evaluation Results</h1>')
    w(f'<div class="subtitle">{total} case(s) from {input_path.name}</div>')

    # Summary stats
    w('<div class="stats-row">')
    w(f'<div class="stat-card"><div class="label">Total Cases</div><div class="value">{total}</div></div>')
    w(f'<div class="stat-card"><div class="label">Total Tokens</div><div class="value">{total_usage.get("total_tokens", 0):,}</div></div>')
    w('</div>')

    # Metric averages
    w('<h2>Metric Averages</h2>')
    w('<div class="metric-grid">')
    for m in metric_names:
        a = avg(m)
        c = _score_color(a, METRIC_THRESHOLDS.get(m, 0.5))
        w(f'<div class="metric-card"><div class="label">{METRIC_LABELS.get(m, m)}</div><div class="score {c}">{_fmt_pct(a)}</div></div>')
    w('</div>')

    # Token usage
    w('<h2>Token Usage</h2>')
    w('<div class="token-section">')
    w('<div class="token-grid">')
    for k in ("prompt_tokens", "completion_tokens", "total_tokens"):
        v = total_usage.get(k, 0)
        w(f'<div class="token-item"><span class="tv total">{v:,}</span><span class="tl">{k}</span></div>')
    w('</div></div>')

    # Category breakdown
    if len(by_cat) > 1:
        w('<h2>Category Breakdown</h2>')
        w('<div class="category-table"><table><tr><th>Category</th><th>Total</th>')
        for m in metric_names:
            w(f'<th>{METRIC_LABELS.get(m, m)}</th>')
        w('</tr>')
        for cat, items in sorted(by_cat.items()):
            w(f'<tr><td><strong>{_esc(cat)}</strong></td><td>{len(items)}</td>')
            for m in metric_names:
                vals = [r["scores"].get(m) for r in items if r["scores"].get(m) is not None]
                a = sum(vals) / len(vals) if vals else None
                w(f'<td>{_fmt(a)}</td>')
            w('</tr>')
        w('</table></div>')

    # Filter bar
    w('<h2>Case Details</h2>')
    cats = sorted(set(r.get("category", "unknown") for r in results))
    if len(cats) > 1:
        w('<div class="filter-bar">')
        w('<button class="filter-btn active all" data-filter="all">All</button>')
        for cat in cats:
            w(f'<button class="filter-btn" data-filter="{_esc(cat)}">{_esc(cat)}</button>')
        w('</div>')

    # Per-case cards
    for idx, r in enumerate(results):
        tid = r["id"]
        scores = r["scores"]
        w(f'<div class="task-card" data-category="{_esc(r.get("category", ""))}">')
        w('<div class="task-header" onclick="toggleTask(this)">')
        w(f'<span class="toggle">&#x25b6;</span>')
        w(f'<span class="num">{idx + 1}</span>')
        w(f'<span class="cat">{_esc(r.get("category", ""))}</span>')
        w(f'<span class="q">{_esc(r["user_input"][:180])}</span>')
        w('<span class="mini-scores">')
        for m in metric_names:
            sc = scores.get(m)
            c = _score_color(sc, METRIC_THRESHOLDS.get(m, 0.5))
            label_short = METRIC_LABELS.get(m, m).split()[-1].lower()
            w(f'<span class="ms"><span class="mv score-{c}">{_fmt(sc)}</span><br><span class="text-dim text-sm">{label_short}</span></span>')
        w('</span></div>')

        w('<div class="task-body">')

        # Score summary
        w('<div class="score-summary">')
        for m in metric_names:
            sc = scores.get(m)
            thresh = METRIC_THRESHOLDS.get(m, 0.5)
            c = _score_color(sc, thresh)
            w(f'<div class="ss-item"><span class="ss-label">{METRIC_LABELS.get(m, m)}</span><span style="font-size:1.1em;font-weight:700;color:var(--{c})">{_fmt(sc)}</span></div>')
        w('</div>')

        # Bar chart for each metric
        w('<div style="margin-bottom:10px">')
        for m in metric_names:
            sc = scores.get(m)
            bw = _bar_width(sc)
            thresh = METRIC_THRESHOLDS.get(m, 0.5)
            c = _score_color(sc, thresh)
            pct = thresh * 100
            w(f'<div style="display:flex;align-items:center;gap:8px;font-size:0.72rem;margin-bottom:4px">')
            w(f'<span style="min-width:100px;color:var(--text-dim)">{METRIC_LABELS.get(m, m)}</span>')
            w(f'<span class="bar-bg"><span class="bar-fill {c}" style="width:{bw}%"></span></span>')
            w(f'<span class="score-{c}" style="min-width:50px">{_fmt(sc)}</span>')
            w(f'</div>')
        w('</div>')

        # Response
        resp = r.get("response_preview", r.get("response", ""))
        w(f'<div class="resp-box"><span class="label">Response</span>{_esc(resp)}</div>')

        # Reference
        ref = r.get("reference", "")
        if ref and ref != "None":
            w(f'<div class="ref-box"><span class="label">Reference (ground truth)</span>{_esc(ref)}</div>')

        w('</div></div>')

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

    return "\n".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate returned LLM responses with RAGAS using DeepSeek via OpenAI SDK."
    )
    parser.add_argument("--input", default=None, help="Path to response cases JSON to evaluate.")
    parser.add_argument(
        "--output",
        default=str(RAGAS_DIR / "deepseek_ragas_results.json"),
        help="Path for scored output JSON.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=180,
        help="Per-metric timeout in seconds.",
    )
    parser.add_argument(
        "--token",
        default=None,
        help="DeepSeek API token. Falls back to DEEPSEEK_API_KEY env var or token in input JSON.",
    )
    parser.add_argument(
        "--report",
        default=None,
        help="Path for HTML report (default: same path as --output with .html extension). "
        "Pass --report '' to skip HTML generation.",
    )
    args = parser.parse_args()
    if not args.input:
        parser.error("--input is required")
    output_path = Path(args.output)
    if args.report is None:
        report_path = output_path.with_suffix(".html")
    elif args.report == "":
        report_path = None
    else:
        report_path = Path(args.report)
    asyncio.run(run(Path(args.input), output_path, report_path, args.timeout, {}, token=args.token))


if __name__ == "__main__":
    main()
