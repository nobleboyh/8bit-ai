#!/usr/bin/env python3
"""
extract_opencode_sessions.py
---------------------------
Extract real conversation pairs from opencode's SQLite database and format
them as RAGAS evaluation cases. This lets you evaluate the quality of
opencode's actual responses instead of using predefined synthetic tasks.

Workflow:
  1. List recent opencode sessions (shows parent/child relationships)
  2. Pick one or more sessions to evaluate
  3. Extract all user → assistant message pairs + project context
  4. Output as RAGAS evaluation JSON (merged across sessions)
  5. (Optionally) run the full evaluation pipeline

Usage:
  # List recent sessions
  python3 extract_opencode_sessions.py list [--limit 10]

  # Extract one session as RAGAS cases
  python3 extract_opencode_sessions.py extract <session_id> [--output cases.json]

  # Extract multiple sessions (merged into one output)
  python3 extract_opencode_sessions.py extract <session_id> [<session_id> ...] --output cases.json

  # Extract session + all its children (entire conversation tree)
  python3 extract_opencode_sessions.py extract <session_id> --with-children --output cases.json

  # Extract + run full RAGAS evaluation pipeline
  python3 extract_opencode_sessions.py eval <session_id> [<session_id> ...] [--output-dir ./eval-output]
"""

import argparse
import json
import os
import sqlite3
import subprocess
import sys
import textwrap
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DB_PATH = os.path.expanduser("~/.local/share/opencode/opencode.db")
RAGAS_DIR = Path(__file__).parent.resolve()


# ── Database helpers ──────────────────────────────────────────────────

def get_db() -> sqlite3.Connection:
    if not os.path.isfile(DB_PATH):
        raise SystemExit(f"Error: opencode database not found at {DB_PATH}")
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def db_get(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
    return conn.execute(sql, params).fetchall()


def db_one(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> sqlite3.Row | None:
    return conn.execute(sql, params).fetchone()


# ── Session listing ───────────────────────────────────────────────────

def list_sessions(limit: int = 10, tree: bool = False):
    conn = get_db()

    if tree:
        # Build a tree view: top-level sessions, then indented children
        rows = db_get(
            conn,
            """SELECT s.id, s.title, s.agent, s.model, s.parent_id,
                      s.tokens_input, s.tokens_output, s.tokens_reasoning,
                      datetime(s.time_created / 1000, 'unixepoch') as created,
                      s.directory
               FROM session s
               ORDER BY s.time_created DESC
               LIMIT ?""",
            (limit * 3,),
        )
        children_by_parent: dict[str, list] = {}
        top_level = []
        for r in rows:
            entry = dict(r)
            if r["parent_id"]:
                children_by_parent.setdefault(r["parent_id"], []).append(entry)
            else:
                top_level.append(entry)

        if not top_level:
            print("No top-level sessions found.")
            conn.close()
            return

        header = f"{'#':<4} {'Session ID':<42} {'Created':<20} {'Agent':<12} {'Tokens':<10} {'Title'}"
        sep = "-" * 130
        print(f"{'Tree view (parent → children)':^130}")
        print(header)
        print(sep)
        idx = 0
        for r in top_level[:limit]:
            idx += 1
            title = r["title"] or "(no title)"
            if len(title) > 55:
                title = title[:52] + "..."
            mid = json.loads(r["model"]).get("id", "?") if r["model"] else "?"
            total_tokens = (r["tokens_input"] or 0) + (r["tokens_output"] or 0)
            print(
                f"{idx:<4} {r['id']:<42} {r['created']:<20} {r['agent']:<12} "
                f"{total_tokens:<10,} {title}"
            )
            print(f"{'':4} {'':42} model: {mid}")
            for child in children_by_parent.get(r["id"], []):
                ctitle = child["title"] or "(no title)"
                if len(ctitle) > 55:
                    ctitle = ctitle[:52] + "..."
                cmid = json.loads(child["model"]).get("id", "?") if child["model"] else "?"
                ctotal = (child["tokens_input"] or 0) + (child["tokens_output"] or 0)
                print(f"{'':4} {'':4}└─ {child['id']:<36} {child['created']:<20} {child['agent']:<12} {ctotal:<10,} {ctitle}")
                print(f"{'':4} {'':8}model: {cmid}")
            print()
        conn.close()
        return

    rows = db_get(
        conn,
        """SELECT s.id, s.title, s.agent, s.model, s.parent_id,
                  s.tokens_input, s.tokens_output, s.tokens_reasoning,
                  datetime(s.time_created / 1000, 'unixepoch') as created,
                  s.directory
           FROM session s
           ORDER BY s.time_created DESC
           LIMIT ?""",
        (limit,),
    )
    conn.close()

    if not rows:
        print("No sessions found.")
        return

    header = f"{'#':<4} {'Session ID':<42} {'Created':<20} {'Agent':<12} {'Tokens In':<10} {'Tokens Out':<11} {'Parent ID':<42} {'Title'}"
    print(f"{'':>4} {'─' * 170}")
    print(header)
    print(f"{'':>4} {'─' * 170}")
    for i, r in enumerate(rows, 1):
        title = r["title"] or "(no title)"
        if len(title) > 40:
            title = title[:37] + "..."
        mid = json.loads(r["model"]).get("id", "?") if r["model"] else "?"
        parent = r["parent_id"] or ""
        if len(parent) > 41:
            parent = parent[:38] + "..."
        print(
            f"{i:<4} {r['id']:<42} {r['created']:<20} {r['agent']:<12} "
            f"{r['tokens_input']:<10,} {r['tokens_output']:<11,} {parent:<42} {title}"
        )
        print(f"{'':4} {'':42} {'':20} {'':12} {'':10} {'':11} {'':42}model: {mid}, dir: {r['directory'] or '?'}")
        print()


# ── Session extraction ────────────────────────────────────────────────

def get_project_path(conn: sqlite3.Connection, session_id: str) -> str | None:
    row = db_one(conn, "SELECT directory FROM session WHERE id = ?", (session_id,))
    if row and row["directory"]:
        return row["directory"]
    row = db_one(
        conn,
        """SELECT p.worktree
           FROM session s
           JOIN project p ON p.id = s.project_id
           WHERE s.id = ?""",
        (session_id,),
    )
    return row["worktree"] if row else None


def get_git_context(project_path: str) -> dict[str, Any]:
    ctx: dict[str, Any] = {}
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=10, cwd=project_path,
        )
        if result.returncode == 0:
            ctx["commit_hash"] = result.stdout.strip()
    except Exception:
        pass
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True, text=True, timeout=10, cwd=project_path,
        )
        if result.returncode == 0:
            ctx["branch"] = result.stdout.strip()
    except Exception:
        pass
    try:
        result = subprocess.run(
            ["git", "status", "--short"],
            capture_output=True, text=True, timeout=10, cwd=project_path,
        )
        if result.returncode == 0:
            ctx["dirty_files"] = result.stdout.count("\n")
    except Exception:
        pass
    return ctx


def get_conversation_pairs(conn: sqlite3.Connection, session_id: str) -> list[dict]:
    """Extract user→assistant message pairs from a session.

    An assistant response may span multiple messages (tool calls, reasoning,
    text output). All assistant messages after a user message (until the next
    user message or end of session) are grouped into one response.

    Each pair: {user_msg_id, assistant_msg_ids, user_time, assistant_time, tokens}
    """
    messages = db_get(
        conn,
        """SELECT m.id, m.time_created,
                  json_extract(m.data, '$.role') as role,
                  json_extract(m.data, '$.tokens') as tokens_json
           FROM message m
           WHERE m.session_id = ?
           ORDER BY m.time_created ASC""",
        (session_id,),
    )

    # Build messages in order, grouping user→assistant sequences
    pairs = []
    current_user = None
    current_assistant_ids: list[str] = []

    for msg in messages:
        role = msg["role"]
        if role == "user":
            # Save previous pair if exists
            if current_user is not None and current_assistant_ids:
                pairs.append({
                    "user_msg_id": current_user["msg_id"],
                    "user_time": current_user["time_created"],
                    "assistant_msg_ids": current_assistant_ids,
                    "assistant_time": current_user["assistant_end_time"],
                    "tokens": current_user["tokens"],
                })
            current_user = {
                "msg_id": msg["id"],
                "time_created": msg["time_created"],
                "assistant_end_time": None,
                "tokens": {},
            }
            current_assistant_ids = []
        elif role == "assistant":
            if current_user is not None:
                current_assistant_ids.append(msg["id"])
                current_user["assistant_end_time"] = msg["time_created"]
                # Accumulate tokens from assistant messages
                tokens = {}
                if msg["tokens_json"]:
                    try:
                        tokens = json.loads(msg["tokens_json"])
                    except json.JSONDecodeError:
                        pass
                for k, v in tokens.items():
                    if k == "cache":
                        continue
                    current_user["tokens"][k] = current_user["tokens"].get(k, 0) + (v if isinstance(v, (int, float)) else 0)

    # Save final pair if there's an unpaired user message with responses
    if current_user is not None and current_assistant_ids:
        pairs.append({
            "user_msg_id": current_user["msg_id"],
            "user_time": current_user["time_created"],
            "assistant_msg_ids": current_assistant_ids,
            "assistant_time": current_user["assistant_end_time"],
            "tokens": current_user["tokens"],
        })

    return pairs


def get_part_text(conn: sqlite3.Connection, message_id: str, part_type: str = "text") -> str:
    rows = db_get(
        conn,
        """SELECT json_extract(p.data, '$.text') as text
           FROM part p
           WHERE p.message_id = ?
             AND json_extract(p.data, '$.type') = ?
           ORDER BY p.time_created ASC""",
        (message_id, part_type),
    )
    parts = [r["text"] for r in rows if r["text"]]
    return "\n".join(parts)


def get_read_files(conn: sqlite3.Connection, assistant_msg_ids: list[str]) -> list[tuple[str, str]]:
    """Extract files read by the agent during a turn from read tool calls.

    Returns deduplicated (filepath, content) tuples, keeping the longest
    content per file (covers offset-based partial reads).
    """
    if not assistant_msg_ids:
        return []

    placeholders = ",".join("?" for _ in assistant_msg_ids)
    rows = db_get(
        conn,
        f"""SELECT json_extract(p.data, '$.state.input.filePath') as filepath,
                   json_extract(p.data, '$.state.output') as content
            FROM part p
            WHERE p.message_id IN ({placeholders})
              AND json_extract(p.data, '$.type') = 'tool'
              AND json_extract(p.data, '$.tool') = 'read'
              AND json_extract(p.data, '$.state.output') IS NOT NULL
            ORDER BY p.time_created ASC""",
        tuple(assistant_msg_ids),
    )

    files: dict[str, str] = {}
    for r in rows:
        fp = r["filepath"]
        content = r["content"]
        if not fp or not content:
            continue
        if fp not in files or len(content) > len(files[fp]):
            files[fp] = content

    MAX_CHARS = 30000
    result = []
    for fp, content in files.items():
        if len(content) > MAX_CHARS:
            content = content[:MAX_CHARS] + "\n...(truncated)"
        result.append((fp, content))
    return result


def extract_session(session_id: str, session_dir: str | None = None) -> dict[str, Any]:
    conn = get_db()

    session_row = db_one(
        conn,
        """SELECT id, title, agent, model,
                  tokens_input, tokens_output, tokens_reasoning,
                  datetime(time_created / 1000, 'unixepoch') as created
           FROM session WHERE id = ?""",
        (session_id,),
    )
    if not session_row:
        conn.close()
        raise SystemExit(f"Error: session not found: {session_id}")

    pairs = get_conversation_pairs(conn, session_id)
    if not pairs:
        conn.close()
        print(f"Warning: no user→assistant pairs found in session {session_id}")
        return {"session": dict(session_row), "cases": []}

    # Get project context
    project_path = session_dir or get_project_path(conn, session_id)
    git_ctx = get_git_context(project_path) if project_path else {}

    def _get_text_from_msgs(msg_ids: list[str], part_type: str) -> str:
        parts = []
        for mid in msg_ids:
            t = get_part_text(conn, mid, part_type)
            if t:
                parts.append(t)
        return "\n".join(parts)

    # Build cases
    cases = []
    for idx, pair in enumerate(pairs):
        user_input = get_part_text(conn, pair["user_msg_id"], "text")
        response = _get_text_from_msgs(pair["assistant_msg_ids"], "text")
        reasoning = _get_text_from_msgs(pair["assistant_msg_ids"], "reasoning")

        if not user_input.strip():
            continue

        # Build context string from project state
        context_parts = []
        if git_ctx:
            parts = []
            if git_ctx.get("branch"):
                parts.append(f"git branch: {git_ctx['branch']}")
            if git_ctx.get("commit_hash"):
                parts.append(f"git commit: {git_ctx['commit_hash']}")
            if "dirty_files" in git_ctx:
                parts.append(f"dirty files: {git_ctx['dirty_files']}")
            if parts:
                context_parts.append("=== Git State ===\n" + "\n".join(parts))

        # Include conversation history as context if this isn't the first turn
        if idx > 0:
            history = []
            for prev_idx in range(idx):
                prev_input = get_part_text(conn, pairs[prev_idx]["user_msg_id"], "text")
                prev_resp = _get_text_from_msgs(pairs[prev_idx]["assistant_msg_ids"], "text")
                if prev_input.strip():
                    history.append(f"User: {prev_input.strip()[:300]}")
                if prev_resp.strip():
                    history.append(f"Assistant: {prev_resp.strip()[:300]}")
            if history:
                context_parts.append("=== Conversation History ===\n" + "\n".join(history))

        # Include files the agent actually read during this turn
        read_files = get_read_files(conn, pair["assistant_msg_ids"])
        for fp, content in read_files:
            context_parts.append(f"=== File: {fp} ===\n{content}")

        retrieved_contexts = context_parts if context_parts else ["(no additional context captured)"]

        # Determine category based on user input length / reasoning
        if reasoning:
            cat = "complex" if len(reasoning) > 500 else "standard"
        else:
            cat = "standard"

        tokens = pair.get("tokens", {})
        total_tokens = tokens.get("total", 0) or (tokens.get("input", 0) + tokens.get("output", 0))

        case = {
            "id": f"{session_id}__turn_{idx + 1}",
            "category": cat,
            "context_type": "opencode_session",
            "user_input": user_input.strip(),
            "response": response.strip(),
            "retrieved_contexts": retrieved_contexts,
            "reasoning": reasoning.strip() if reasoning else None,
            "usage": {
                "prompt_tokens": tokens.get("input", 0),
                "completion_tokens": tokens.get("output", 0),
                "reasoning_tokens": tokens.get("reasoning", 0),
                "total_tokens": total_tokens,
            },
        }
        cases.append(case)

    conn.close()

    # Compute totals
    total_prompt = sum(c["usage"]["prompt_tokens"] for c in cases)
    total_completion = sum(c["usage"]["completion_tokens"] for c in cases)
    total = sum(c["usage"]["total_tokens"] for c in cases)

    return {
        "session": {
            "id": session_id,
            "title": session_row["title"],
            "agent": session_row["agent"],
            "created": session_row["created"],
            "git": git_ctx,
            "project_path": project_path,
        },
        "total_usage": {
            "prompt_tokens": total_prompt,
            "completion_tokens": total_completion,
            "total_tokens": total,
        },
        "cases": cases,
    }


# ── Run evaluation pipeline ───────────────────────────────────────────

def run_evaluation(cases_path: Path, output_dir: Path):
    """Run evaluate_deepseek_ragas.py (auto-generates HTML report)."""
    os.environ.setdefault("DEEPSEEK_API_KEY", "")
    if not os.environ.get("DEEPSEEK_API_KEY"):
        print("Warning: DEEPSEEK_API_KEY is not set. Evaluation will fail.")

    output_dir.mkdir(parents=True, exist_ok=True)
    results_path = output_dir / "ragas_results.json"

    print(f"\n{'='*60}")
    print(f"RAGAS evaluation")
    print(f"  Input:  {cases_path}")
    print(f"  Output: {results_path}")
    print(f"  HTML:   {results_path.with_suffix('.html')}")
    print(f"{'='*60}")
    eval_script = RAGAS_DIR / "evaluate_deepseek_ragas.py"
    result = subprocess.run(
        [sys.executable, str(eval_script), "--input", str(cases_path), "--output", str(results_path)],
        capture_output=False,
    )
    if result.returncode == 0:
        print(f"\nDone! Open the report:")
        print(f"  open {results_path.with_suffix('.html')}")
    else:
        print(f"Evaluation failed (exit code {result.returncode})")


# ── CLI ───────────────────────────────────────────────────────────────

def cmd_list(args):
    list_sessions(args.limit, tree=args.tree)


def get_child_session_ids(conn: sqlite3.Connection, session_id: str) -> list[str]:
    """Recursively collect all descendant session IDs."""
    children = []
    queue = [session_id]
    seen = {session_id}
    while queue:
        pid = queue.pop(0)
        rows = db_get(conn, "SELECT id FROM session WHERE parent_id = ?", (pid,))
        for r in rows:
            if r["id"] not in seen:
                seen.add(r["id"])
                children.append(r["id"])
                queue.append(r["id"])
    return children


def resolve_session_ids(session_ids: list[str], with_children: bool = False) -> list[str]:
    """Resolve session IDs, optionally expanding to include children."""
    if not with_children:
        return session_ids
    conn = get_db()
    resolved = list(session_ids)
    for sid in session_ids:
        resolved.extend(get_child_session_ids(conn, sid))
    conn.close()
    # Deduplicate while preserving order
    seen = set()
    return [s for s in resolved if not (s in seen or seen.add(s))]


def cmd_extract(args):
    output_path = Path(args.output) if args.output else Path("opencode_ragas_cases.json")
    session_ids = resolve_session_ids(args.session_ids, args.with_children)
    all_cases = []
    all_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    sessions_meta = []
    errors = []

    for sid in session_ids:
        try:
            data = extract_session(sid, args.dir)
            if data.get("cases"):
                all_cases.extend(data["cases"])
                for k in all_usage:
                    all_usage[k] += data["total_usage"].get(k, 0)
                sessions_meta.append({
                    "id": data["session"]["id"],
                    "title": data["session"]["title"],
                    "agent": data["session"]["agent"],
                    "cases": len(data["cases"]),
                })
        except SystemExit as e:
            errors.append(str(e))

    if not all_cases:
        print("No conversation pairs found across any session. Nothing to write.")
        if errors:
            for e in errors:
                print(f"  Error: {e}")
        sys.exit(1)

    merged = {
        "sessions": sessions_meta,
        "total_usage": all_usage,
        "cases": all_cases,
    }
    output_path.write_text(json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8")
    total_turns = len(all_cases)
    total_tok = all_usage["total_tokens"]
    print(f"Extracted {total_turns} conversation turn(s) from {len(sessions_meta)} session(s)")
    for sm in sessions_meta:
        print(f"  {sm['id']}: {sm['title']} ({sm['cases']} turns, {sm['agent']})")
    print(f"Total tokens: {total_tok:,}")
    print(f"Written to:   {output_path}")
    if errors:
        print(f"\nErrors ({len(errors)}):")
        for e in errors:
            print(f"  {e}")


def cmd_eval(args):
    output_dir = Path(args.output_dir) if args.output_dir else Path("opencode_eval_output")
    output_dir.mkdir(parents=True, exist_ok=True)
    cases_path = output_dir / "opencode_ragas_cases.json"

    session_ids = resolve_session_ids(args.session_ids, args.with_children)
    all_cases = []
    all_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    sessions_meta = []
    errors = []

    for sid in session_ids:
        try:
            data = extract_session(sid, args.dir)
            if data.get("cases"):
                all_cases.extend(data["cases"])
                for k in all_usage:
                    all_usage[k] += data["total_usage"].get(k, 0)
                sessions_meta.append({
                    "id": data["session"]["id"],
                    "title": data["session"]["title"],
                    "agent": data["session"]["agent"],
                    "cases": len(data["cases"]),
                })
        except SystemExit as e:
            errors.append(str(e))

    if not all_cases:
        print("No conversation pairs found across any session. Nothing to evaluate.")
        if errors:
            for e in errors:
                print(f"  Error: {e}")
        sys.exit(1)

    merged = {
        "sessions": sessions_meta,
        "total_usage": all_usage,
        "cases": all_cases,
    }
    cases_path.write_text(json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8")
    total_turns = len(all_cases)
    total_tok = all_usage["total_tokens"]
    print(f"Extracted {total_turns} conversation turn(s) from {len(sessions_meta)} session(s)")
    for sm in sessions_meta:
        print(f"  {sm['id']}: {sm['title']} ({sm['cases']} turns, {sm['agent']})")
    print(f"Total tokens: {total_tok:,}")
    if errors:
        print(f"\nErrors ({len(errors)}):")
        for e in errors:
            print(f"  {e}")
    run_evaluation(cases_path, output_dir)


# ── Enrich: generate reference answers ────────────────────────────────

REFERENCE_SYSTEM_PROMPT = (
    "You are a senior software engineer. Given a question and project context, "
    "produce the definitive answer. Reference specific files, functions, and "
    "code patterns from the context. Do not add meta-commentary about the "
    "answer itself — just provide the correct answer."
)


def call_deepseek_for_reference(
    client: Any, model: str, user_input: str, contexts: list[str]
) -> tuple[str, dict]:
    context_str = "\n\n".join(
        str(ctx) for ctx in contexts if ctx
    )
    prompt = (
        f"Question: {user_input}\n\n"
        f"Context available to the agent:\n"
        f"{'─' * 60}\n"
        f"{context_str}\n"
        f"{'─' * 60}\n\n"
        f"Write a comprehensive, accurate answer to the question based on the "
        f"context above. This answer will be used as ground truth for evaluating "
        f"AI response quality, so be thorough and precise."
    )

    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": REFERENCE_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        max_tokens=4096,
    )
    usage = {
        "prompt_tokens": resp.usage.prompt_tokens if resp.usage else 0,
        "completion_tokens": resp.usage.completion_tokens if resp.usage else 0,
        "total_tokens": resp.usage.total_tokens if resp.usage else 0,
    }
    return resp.choices[0].message.content, usage


def cmd_enrich(args):
    """Generate reference answers for extracted session cases using DeepSeek."""
    try:
        from openai import OpenAI
    except ImportError:
        raise SystemExit("Missing dependency: openai. Install with: pip install openai")

    input_path = Path(args.input)
    output_path = Path(args.output) if args.output else input_path

    with input_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    cases = data.get("cases", [data] if isinstance(data, dict) else data)
    if not cases:
        print("No cases found in input file.")
        sys.exit(1)

    api_key = args.token or os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise SystemExit(
            "DEEPSEEK_API_KEY is required. Set the env var or pass --token."
        )

    base_url = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    model = os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-flash")
    client = OpenAI(api_key=api_key, base_url=base_url)

    total_gen_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    enriched = 0
    skipped = 0

    for idx, case in enumerate(cases):
        if case.get("reference"):
            print(f"  [{idx + 1}/{len(cases)}] {case['id']}: has reference, skipping")
            skipped += 1
            continue

        user_input = case.get("user_input", "")
        contexts = case.get("retrieved_contexts", [])
        if not user_input.strip():
            print(f"  [{idx + 1}/{len(cases)}] {case['id']}: empty user_input, skipping")
            skipped += 1
            continue

        print(f"  [{idx + 1}/{len(cases)}] {case['id']}: generating reference...")
        try:
            reference, usage = call_deepseek_for_reference(
                client, model, user_input, contexts
            )
            case["reference"] = reference
            for k in total_gen_usage:
                total_gen_usage[k] += usage.get(k, 0)
            enriched += 1
        except Exception as e:
            print(f"    ERROR: {e}", file=sys.stderr)
            case["reference"] = f"[reference generation failed: {e}]"

    # Merge usage tracking
    if isinstance(data, dict) and "total_usage" in data and enriched:
        existing = data["total_usage"]
        data["total_usage"] = {
            "prompt_tokens": existing.get("prompt_tokens", 0) + total_gen_usage["prompt_tokens"],
            "completion_tokens": existing.get("completion_tokens", 0) + total_gen_usage["completion_tokens"],
            "total_tokens": existing.get("total_tokens", 0) + total_gen_usage["total_tokens"],
        }
    elif enriched:
        data["total_usage"] = total_gen_usage

    output_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    total = len(cases)
    print(f"\nEnriched {enriched} case(s), skipped {skipped} of {total}")
    print(f"Reference generation tokens: {total_gen_usage}")
    print(f"Written to: {output_path}")
    if total_gen_usage["total_tokens"] > 0 and enriched > 0:
        avg = total_gen_usage["total_tokens"] / enriched
        print(f"Average tokens per reference: {avg:.0f}")
    print(f"\nNow run: python3 evaluate_deepseek_ragas.py --input {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Extract opencode sessions for RAGAS evaluation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              # List recent sessions
              %(prog)s list

              # List sessions as parent/child tree
              %(prog)s list --tree

              # Extract a session as JSON
              %(prog)s extract ses_abc123 --output my_cases.json

              # Extract multiple sessions (merged)
              %(prog)s extract ses_abc123 ses_def456 --output merged_cases.json

              # Extract session + all its child sessions
              %(prog)s extract ses_abc123 --with-children --output full_tree.json

              # Extract + run full evaluation for multiple sessions
              %(prog)s eval ses_abc123 ses_def456 --output-dir ./eval-results

              # Eval a session with all its children
              %(prog)s eval ses_abc123 --with-children --output-dir ./eval-results

              # Enrich extracted cases with LLM-generated reference answers
              %(prog)s enrich opencode_ragas_cases.json --output enriched_cases.json
        """),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # list
    p_list = sub.add_parser("list", help="List recent opencode sessions")
    p_list.add_argument("--limit", type=int, default=10, help="Number of sessions to show")
    p_list.add_argument("--tree", action="store_true", help="Show parent/child hierarchy")

    # extract
    p_extract = sub.add_parser("extract", help="Extract conversation pairs as RAGAS cases JSON (one or more sessions)")
    p_extract.add_argument("session_ids", nargs="+", help="Session ID(s) from the list command")
    p_extract.add_argument("--output", help="Output JSON path (default: opencode_ragas_cases.json)")
    p_extract.add_argument("--dir", help="Project directory (for git context; auto-detected if omitted)")
    p_extract.add_argument("--with-children", action="store_true", help="Recursively include child sessions")

    # eval
    p_eval = sub.add_parser("eval", help="Extract + run full RAGAS evaluation pipeline (one or more sessions)")
    p_eval.add_argument("session_ids", nargs="+", help="Session ID(s) from the list command")
    p_eval.add_argument("--output-dir", help="Directory for evaluation output (default: ./opencode_eval_output)")
    p_eval.add_argument("--dir", help="Project directory (for git context; auto-detected if omitted)")
    p_eval.add_argument("--with-children", action="store_true", help="Recursively include child sessions")

    # enrich
    p_enrich = sub.add_parser("enrich", help="Add LLM-generated reference answers to extracted cases so all 4 RAGAS metrics can run")
    p_enrich.add_argument("input", help="Path to extracted cases JSON (output of 'extract' command)")
    p_enrich.add_argument("--output", help="Output path (default: overwrites input)")
    p_enrich.add_argument("--token", help="DeepSeek API token (falls back to DEEPSEEK_API_KEY env var)")

    args = parser.parse_args()

    if args.command == "list":
        cmd_list(args)
    elif args.command == "extract":
        cmd_extract(args)
    elif args.command == "eval":
        cmd_eval(args)
    elif args.command == "enrich":
        cmd_enrich(args)


if __name__ == "__main__":
    main()
