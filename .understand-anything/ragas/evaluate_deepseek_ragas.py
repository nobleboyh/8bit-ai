#!/usr/bin/env python3
"""
evaluate_deepseek_ragas.py
-------------------------
Score previously-generated LLM responses using RAGAS metrics (Faithfulness,
Context Precision, Context Recall, Answer Relevancy) through a DeepSeek
OpenAI-compatible endpoint.

Usage:
  export DEEPSEEK_API_KEY=...
  python3.12 evaluate_deepseek_ragas.py --input deepseek_tasks_output.json

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
DEFAULT_THRESHOLDS = {
    "faithfulness": 0.70,
    "context_precision": 0.50,
    "context_recall": 0.50,
    "answer_relevancy": 0.70,
}


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


def evaluate_failures(scores: dict, thresholds: dict) -> list[str]:
    failures = []
    for metric_name, min_score in thresholds.items():
        if metric_name not in scores:
            continue
        score = scores[metric_name]
        if score is None:
            failures.append(f"{metric_name}: unavailable")
        elif isinstance(score, (int, float)) and score < min_score:
            failures.append(f"{metric_name}: {score:.3f} < {min_score:.3f}")
    return failures


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
    timeout: float | None,
    thresholds: dict,
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
        failures = evaluate_failures(scores, thresholds)
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
                "passed": not failures,
                "failures": failures,
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

    failed = [result for result in results if not result["passed"]]
    print(f"Passed: {len(results) - len(failed)}/{len(results)}")
    for result in failed:
        print(f"  FAIL {result['id']}: {', '.join(result['failures'])}")


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
    parser.add_argument("--min-faithfulness", type=float, default=DEFAULT_THRESHOLDS["faithfulness"])
    parser.add_argument("--min-context-precision", type=float, default=DEFAULT_THRESHOLDS["context_precision"])
    parser.add_argument("--min-context-recall", type=float, default=DEFAULT_THRESHOLDS["context_recall"])
    parser.add_argument("--min-answer-relevancy", type=float, default=DEFAULT_THRESHOLDS["answer_relevancy"])
    args = parser.parse_args()
    thresholds = {
        "faithfulness": args.min_faithfulness,
        "context_precision": args.min_context_precision,
        "context_recall": args.min_context_recall,
        "answer_relevancy": args.min_answer_relevancy,
    }
    if not args.input:
        parser.error("--input is required")
    output_path = Path(args.output)
    asyncio.run(run(Path(args.input), output_path, args.timeout, thresholds, token=args.token))


if __name__ == "__main__":
    main()
