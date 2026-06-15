#!/usr/bin/env python3
"""
generate_deepseek_tasks.py
-------------------------
Define PixelForge coding tasks (hard / very_hard), call DeepSeek to generate
responses with source-only or full KG context, and produce a JSON file
compatible with evaluate_deepseek_ragas.py.

Each task is evaluated in TWO modes:
  - with_source: context includes the relevant source files (no KG)
  - with_kg:     context includes source files + KG structural metadata

Usage:
  export DEEPSEEK_API_KEY="sk-..."
  python3.12 generate_deepseek_tasks.py [--sample N] [--run-understand] [--force]

  --sample N        Run a random subset of N tasks (default: all)
  --run-understand  Run the understand-anything pipeline before LLM calls
  --force           Force full rebuild of the knowledge graph (implies --run-understand)

Output:
  deepseek_tasks_output.json   ← ready for evaluate_deepseek_ragas.py
"""

import json
import os
import random
import subprocess
import sys
import tempfile
import time
from pathlib import Path

try:
    from openai import OpenAI
except ImportError as e:
    raise SystemExit(f"Missing dependency: {e}. Install with: pip install openai")


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
RAGAS_DIR = Path(__file__).resolve().parent
KG_PATH = PROJECT_ROOT / ".understand-anything" / "knowledge-graph.json"
KG_INTERMEDIATE = PROJECT_ROOT / ".understand-anything" / "intermediate"

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-flash")
OUTPUT_PATH = os.environ.get("OUTPUT_PATH", str(RAGAS_DIR / "deepseek_tasks_output.json"))
RETRY_DELAY = int(os.environ.get("RETRY_DELAY", "10"))

# ---------------------------------------------------------------------------
# Understand-anything plugin resolution (mirrors SKILL.md Phase 0 logic)
# ---------------------------------------------------------------------------
PLUGIN_ROOT_CANDIDATES = [
    os.environ.get("CLAUD_CODE_PLUGIN_ROOT"),
    os.environ.get("CLAUDE_PLUGIN_ROOT"),
    str(Path.home() / ".understand-anything-plugin"),
    str(Path.home() / ".opencode" / "understand-anything" / "understand-anything-plugin"),
    str(Path.home() / "understand-anything" / "understand-anything-plugin"),
]

# Resolve via the skill symlink (~/.agents/skills/understand -> plugin repo)
_SKILL_PATH = Path.home() / ".agents" / "skills" / "understand"
if _SKILL_PATH.exists() and _SKILL_PATH.is_symlink():
    _resolved = _SKILL_PATH.resolve()
    # skills/understand/ -> plugin root is parent of skills/
    PLUGIN_ROOT_CANDIDATES.insert(0, str(_resolved.parent.parent))


PLUGIN_ROOT: Path | None = None
for candidate in PLUGIN_ROOT_CANDIDATES:
    if candidate and Path(candidate).exists():
        pkg = Path(candidate) / "package.json"
        ws = Path(candidate) / "pnpm-workspace.yaml"
        if pkg.exists() and ws.exists():
            PLUGIN_ROOT = Path(candidate)
            break

SYSTEM_PROMPT = (
    "You are a senior TypeScript/React engineer maintaining the PixelForge codebase. "
    "Answer each coding task concisely and precisely. Reference specific files, "
    "types, functions, and patterns from the provided context. "
    "Do NOT add commentary beyond what is asked."
)


def read_source(relative_path: str) -> str:
    path = PROJECT_ROOT / relative_path
    if not path.exists():
        return f"# File not found: {relative_path}"
    return path.read_text(encoding="utf-8")


def load_knowledge_graph() -> dict:
    if not KG_PATH.exists():
        print(f"Warning: knowledge graph not found at {KG_PATH}", file=sys.stderr)
        return {"nodes": [], "edges": [], "layers": []}
    with KG_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Understand-anything pipeline integration
# ---------------------------------------------------------------------------

def _ensure_plugin_built() -> None:
    """Build @understand-anything/core if dist/ does not exist."""
    core_dist = PLUGIN_ROOT / "packages" / "core" / "dist" / "index.js"
    if core_dist.exists():
        return
    print("Building @understand-anything/core...")
    result = subprocess.run(
        ["pnpm", "install", "--frozen-lockfile"],
        cwd=str(PLUGIN_ROOT),
        capture_output=True, text=True, timeout=120,
    )
    if result.returncode != 0:
        result = subprocess.run(
            ["pnpm", "install"],
            cwd=str(PLUGIN_ROOT),
            capture_output=True, text=True, timeout=120,
        )
    if result.returncode != 0:
        raise RuntimeError(f"pnpm install failed:\n{result.stderr}")
    result = subprocess.run(
        ["pnpm", "--filter", "@understand-anything/core", "build"],
        cwd=str(PLUGIN_ROOT),
        capture_output=True, text=True, timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(f"pnpm build failed:\n{result.stderr}")
    print("  done.")


def _run_scan_project(project_root: Path) -> dict:
    """Run scan-project.mjs to get the file inventory with language & category."""
    output = tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, dir=KG_INTERMEDIATE
    )
    output_path = output.name
    output.close()

    scanner = PLUGIN_ROOT / "skills" / "understand" / "scan-project.mjs"
    result = subprocess.run(
        ["node", str(scanner), str(project_root), output_path],
        capture_output=True, text=True, timeout=300,
    )
    if result.returncode != 0:
        raise RuntimeError(f"scan-project.mjs failed:\n{result.stderr}")

    with open(output_path, "r") as f:
        data = json.load(f)
    Path(output_path).unlink(missing_ok=True)
    return data


def _get_file_metadata(task_files: list[str], scan_result: dict) -> list[dict]:
    """Look up language, sizeLines, fileCategory for each task source file."""
    files_by_path = {f["path"]: f for f in scan_result.get("files", [])}
    batch = []
    for rel_path in task_files:
        meta = files_by_path.get(rel_path)
        if meta:
            batch.append({
                "path": rel_path,
                "language": meta["language"],
                "sizeLines": meta["sizeLines"],
                "fileCategory": meta["fileCategory"],
            })
        else:
            # Fallback: minimal entry for files not in scan result
            ext = Path(rel_path).suffix
            lang_map = {".ts": "typescript", ".tsx": "typescriptreact", ".js": "javascript",
                        ".json": "json", ".yaml": "yaml", ".md": "markdown"}
            batch.append({
                "path": rel_path,
                "language": lang_map.get(ext, "unknown"),
                "sizeLines": 0,
                "fileCategory": "code" if ext in (".ts", ".tsx", ".js") else "config",
            })
    return batch


def _run_extract_structure(
    plugin_root: Path, project_root: Path, batch_files: list[dict]
) -> dict:
    """Run extract-structure.mjs on a batch of files to get structural data."""
    input_data = {
        "projectRoot": str(project_root),
        "batchFiles": batch_files,
        "batchImportData": {},
    }

    input_file = tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, dir=KG_INTERMEDIATE
    )
    json.dump(input_data, input_file)
    input_path = input_file.name
    input_file.close()

    output_file = tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, dir=KG_INTERMEDIATE
    )
    output_path = output_file.name
    output_file.close()

    extractor = plugin_root / "skills" / "understand" / "extract-structure.mjs"
    result = subprocess.run(
        ["node", str(extractor), input_path, output_path],
        capture_output=True, text=True, timeout=120,
    )
    Path(input_path).unlink(missing_ok=True)

    if result.returncode != 0:
        Path(output_path).unlink(missing_ok=True)
        raise RuntimeError(f"extract-structure.mjs failed:\n{result.stderr}")

    with open(output_path, "r") as f:
        data = json.load(f)
    Path(output_path).unlink(missing_ok=True)
    return data


def _build_kg_from_extraction(extraction: dict, project_name: str) -> dict:
    """Build a knowledge-graph JSON from extract-structure.mjs results."""
    nodes = []
    edges = []
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    for res in extraction.get("results", []):
        file_path = res["path"]
        file_id = f"file:{file_path}"

        # File node
        file_node = {
            "id": file_id,
            "type": "file",
            "name": Path(file_path).name,
            "filePath": file_path,
            "summary": f"{res.get('language', 'unknown')} file ({res.get('fileCategory', 'code')})",
            "tags": [res.get("language", "unknown"), res.get("fileCategory", "code")],
            "complexity": (
                "moderate" if res.get("metrics", {}).get("functionCount", 0) > 5
                else "simple"
            ),
            "properties": {
                "totalLines": res.get("totalLines", 0),
                "language": res.get("language", "unknown"),
                "fileCategory": res.get("fileCategory", "code"),
            },
        }
        nodes.append(file_node)

        metrics = res.get("metrics", {})

        # Function nodes
        for fn in res.get("functions", []):
            fn_id = f"function:{file_path}:{fn['name']}"
            nodes.append({
                "id": fn_id,
                "type": "function",
                "name": fn["name"],
                "filePath": file_path,
                "summary": f"Function {fn['name']} ({fn.get('startLine', '?')}-{fn.get('endLine', '?')})",
                "tags": ["function", res.get("language", "unknown")],
                "complexity": "moderate" if len(fn.get("params", [])) > 3 else "simple",
                "properties": {
                    "startLine": fn.get("startLine", 0),
                    "endLine": fn.get("endLine", 0),
                    "params": fn.get("params", []),
                },
            })
            edges.append({
                "source": file_id,
                "target": fn_id,
                "type": "contains",
                "direction": "directed",
                "weight": 1.0,
            })

        # Class nodes
        for cls in res.get("classes", []):
            cls_id = f"class:{file_path}:{cls['name']}"
            nodes.append({
                "id": cls_id,
                "type": "class",
                "name": cls["name"],
                "filePath": file_path,
                "summary": f"Class {cls['name']} ({cls.get('startLine', '?')}-{cls.get('endLine', '?')})",
                "tags": ["class", res.get("language", "unknown")],
                "complexity": "moderate" if len(cls.get("methods", [])) > 5 else "simple",
                "properties": {
                    "startLine": cls.get("startLine", 0),
                    "endLine": cls.get("endLine", 0),
                    "methods": cls.get("methods", []),
                    "properties": cls.get("properties", []),
                },
            })
            edges.append({
                "source": file_id,
                "target": cls_id,
                "type": "contains",
                "direction": "directed",
                "weight": 1.0,
            })
            # Link class methods to the class node
            for method in cls.get("methods", []):
                method_name = method if isinstance(method, str) else method.get("name", str(method))
                method_id = f"function:{file_path}:{method_name}"
                # Only add edge if the method node exists (created above)
                edges.append({
                    "source": cls_id,
                    "target": method_id,
                    "type": "contains",
                    "direction": "directed",
                    "weight": 1.0,
                })

        # Export edges between file and its exports
        for exp in res.get("exports", []):
            exp_name = exp["name"]
            export_target = f"function:{file_path}:{exp_name}"
            # Check if this name matches a known function/class
            all_ids = {n["id"] for n in nodes}
            if export_target in all_ids:
                edges.append({
                    "source": file_id,
                    "target": export_target,
                    "type": "exports",
                    "direction": "directed",
                    "weight": 0.8,
                })

        # Call graph edges
        for call in res.get("callGraph", []):
            caller = f"function:{file_path}:{call['caller']}"
            callee_file = call.get("calleeFile", file_path)
            callee = f"function:{callee_file}:{call['callee']}"
            edges.append({
                "source": caller,
                "target": callee,
                "type": "calls",
                "direction": "directed",
                "weight": 0.8,
            })

    # Layer: auto-assign based on file path patterns
    layer_map: dict[str, dict] = {}
    for node in nodes:
        if node["type"] != "file":
            continue
        fp = node.get("filePath", "")
        if fp.startswith("src/types/"):
            layer_name = "Types & Schemas"
        elif fp.startswith("src/services/"):
            layer_name = "Services"
        elif fp.startswith("src/components/"):
            layer_name = "Components"
        elif fp.startswith("src/hooks/"):
            layer_name = "Hooks"
        elif fp.startswith("src/utils/"):
            layer_name = "Utilities"
        else:
            layer_name = "Core"

        if layer_name not in layer_map:
            lid = f"layer:{layer_name.lower().replace(' & ', '-').replace(' ', '-')}"
            layer_map[layer_name] = {
                "id": lid,
                "name": layer_name,
                "description": f"Auto-assigned layer for {layer_name.lower()} files",
                "nodeIds": [],
            }
        layer_map[layer_name]["nodeIds"].append(node["id"])

    layers = list(layer_map.values())

    git_hash = _get_git_hash()

    return {
        "version": "1.0.0",
        "project": {
            "name": project_name,
            "languages": ["typescript", "typescriptreact"],
            "frameworks": ["react"],
            "description": f"PixelForge codebase ({len(nodes)} nodes extracted)",
            "analyzedAt": now,
            "gitCommitHash": git_hash,
        },
        "nodes": nodes,
        "edges": edges,
        "layers": layers,
        "tour": [
            {
                "order": 1,
                "title": "Type Definitions",
                "description": "Core type definitions for the pixel generation system",
                "nodeIds": [n["id"] for n in nodes if n.get("filePath", "").startswith("src/types/")],
            },
            {
                "order": 2,
                "title": "Services & Providers",
                "description": "LLM provider implementations and response parsing",
                "nodeIds": [n["id"] for n in nodes if n.get("filePath", "").startswith("src/services/")],
            },
        ],
    }


def _get_git_hash() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(PROJECT_ROOT),
            capture_output=True, text=True, timeout=10,
        )
        return result.stdout.strip()
    except Exception:
        return "unknown"


def _collect_task_source_files(tasks: list[dict]) -> list[str]:
    """Get all unique source files referenced across tasks."""
    seen: set[str] = set()
    for task in tasks:
        for f in task.get("source_files", []):
            seen.add(f)
    return sorted(seen)


def run_understand_pipeline(tasks: list[dict], force: bool = False) -> dict:
    """Run the understand-anything pipeline and return a knowledge graph.

    Steps:
      1. Ensure plugin is built
      2. Run scan-project.mjs to get file inventory
      3. Collect task-relevant source files
      4. Run extract-structure.mjs to get structural data
      5. Build and save knowledge graph
    """
    project_name = PROJECT_ROOT.name

    if PLUGIN_ROOT is None:
        print("WARNING: understand-anything plugin not found.", file=sys.stderr)
        print("Falling back to source-file-based context.", file=sys.stderr)
        return {"nodes": [], "edges": [], "layers": []}

    KG_INTERMEDIATE.mkdir(parents=True, exist_ok=True)

    # Step 1: ensure plugin is built
    try:
        _ensure_plugin_built()
    except RuntimeError as e:
        print(f"WARNING: Plugin build failed: {e}", file=sys.stderr)
        print("Falling back to source-based context.", file=sys.stderr)
        return {"nodes": [], "edges": [], "layers": []}

    # Step 2: scan project
    if force or not KG_PATH.exists():
        print("  Scanning project files...")
        try:
            scan_result = _run_scan_project(PROJECT_ROOT)
            total = scan_result.get("totalFiles", 0)
            filtered = scan_result.get("filteredByIgnore", 0)
            print(f"    Found {total} files ({filtered} filtered by .understandignore)")
        except RuntimeError as e:
            print(f"  WARNING: Project scan failed: {e}", file=sys.stderr)
            scan_result = None
    else:
        scan_result = None
        print("  Using existing knowledge graph (use --force to rescan)")

    # Step 3: collect task-relevant source files
    task_files = _collect_task_source_files(tasks)
    print(f"  Task-relevant files: {len(task_files)}")

    # Step 4: get file metadata and run extract-structure
    if scan_result:
        file_batch = _get_file_metadata(task_files, scan_result)
    else:
        file_batch = _get_file_metadata(task_files, {"files": []})

    print(f"  Extracting structure from {len(file_batch)} files...")
    try:
        extraction = _run_extract_structure(PLUGIN_ROOT, PROJECT_ROOT, file_batch)
        analyzed = extraction.get("filesAnalyzed", 0)
        skipped = extraction.get("filesSkipped", [])
        print(f"    Analyzed: {analyzed}, Skipped: {len(skipped)}")
        if skipped:
            for s in skipped:
                print(f"      - {s}")
    except RuntimeError as e:
        print(f"  WARNING: Structure extraction failed: {e}", file=sys.stderr)
        print("  Falling back to source-based context.", file=sys.stderr)
        return {"nodes": [], "edges": [], "layers": []}

    # Step 5: build knowledge graph
    print("  Building knowledge graph...")
    kg = _build_kg_from_extraction(extraction, project_name)
    node_count = len(kg["nodes"])
    edge_count = len(kg["edges"])
    print(f"    Nodes: {node_count}, Edges: {edge_count}")

    # Save to KG_PATH
    KG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with KG_PATH.open("w", encoding="utf-8") as f:
        json.dump(kg, f, indent=2, ensure_ascii=False)
    print(f"    Saved: {KG_PATH}")

    return kg


def _file_of(node_id: str) -> str:
    """Extract relative file path from a KG node ID like 'function:src/hooks/foo.ts:bar'."""
    parts = node_id.split(":", 2)
    if len(parts) >= 2:
        return parts[1]
    return node_id


def _is_cross_file(source: str, target: str) -> bool:
    return _file_of(source) != _file_of(target)


def build_kg_context(task: dict, kg: dict) -> str:
    source_files: set[str] = set(task["source_files"])
    relevant_ids: set[str] = set()
    for rel_path in source_files:
        relevant_ids.add(f"file:{rel_path}")
    for tid in task.get("type_ids", []):
        relevant_ids.add(tid)
        if tid.startswith("function:") or tid.startswith("class:"):
            parts = tid.split(":", 2)
            if len(parts) == 3:
                relevant_ids.add(f"file:{parts[1]}")

    sections = []

    # ── Section 1: Full source code of each relevant file ──
    sections.append("=== SOURCE FILES ===")
    for fp in sorted(source_files):
        sections.append(f"--- {fp} ---\n{read_source(fp)}")

    # ── Section 2: Concise structure index (line ranges for key symbols) ──
    index_lines: list[str] = []
    for node in kg.get("nodes", []):
        if node.get("id", "") not in relevant_ids:
            continue
        t = node.get("type", "")
        if t == "file":
            continue  # source section already covers files
        name = node.get("name", "")
        fp = node.get("filePath", "")
        props = node.get("properties", {})
        start = props.get("startLine", "")
        end = props.get("endLine", "")
        line_range = f":{start}-{end}" if start and end else ""
        if name and fp:
            index_lines.append(f"  {name}{'()' if t == 'function' else ''}  {fp}{line_range}")

    if index_lines:
        sections.append("=== STRUCTURE (line ranges) ===")
        sections.extend(index_lines)

    # ── Section 3: Cross-file edges only (skip intra-file noise) ──
    xfile_edges: list[str] = []
    for edge in kg.get("edges", []):
        source = edge.get("source", "")
        target = edge.get("target", "")
        if (source in relevant_ids or target in relevant_ids) and _is_cross_file(source, target):
            xfile_edges.append(
                f"  {edge.get('type', 'related')}: {source} -> {target}"
            )

    if xfile_edges:
        sections.append("=== CROSS-FILE RELATIONSHIPS ===")
        sections.extend(xfile_edges)

    return "\n".join(sections)


TASKS = [
    # ── LEVEL 3: Cross-module / multi-file edit (hard) ──────────────────────
    {
        "id": "complex-add-groq-provider",
        "category": "hard",
        "user_input": (
            "Add a new Groq LLM provider to PixelForge. Groq uses OpenAI-compatible "
            "/v1/chat/completions but with different defaults. Walk through every "
            "file needing change and describe exact modifications."
        ),
        "source_files": [
            "src/types/pixelmap.ts",
            "src/services/llmClient.ts",
            "src/services/OpenAIProvider.ts",
            "src/components/ProviderSelect/ProviderSelect.tsx",
        ],
        "type_ids": [
            "function:src/services/llmClient.ts:generate",
            "class:src/services/OpenAIProvider.ts:OpenAIProvider",
        ],
        "reference": (
            "1. pixelmap.ts: Add 'groq' to LLMProviderType union. "
            "Add Groq preset to PROVIDER_PRESETS: apiUrl 'https://api.groq.com/openai', "
            "model 'llama-3.3-70b-versatile'.\n"
            "2. Create src/services/GroqProvider.ts following OpenAIProvider pattern.\n"
            "3. llmClient.ts: Import GroqProvider, add 'groq' dispatch case.\n"
            "4. ProviderSelect.tsx: No change if presets drive options; otherwise add Groq.\n"
            "5. Add GroqProvider.test.ts following existing test patterns."
        ),
    },
    {
        "id": "complex-history-feature",
        "category": "hard",
        "user_input": (
            "Design a generation history feature that saves previous avatars to "
            "localStorage and allows re-downloading. List all files to create/modify "
            "and describe each change."
        ),
        "source_files": [
            "src/hooks/usePixelGeneration.ts",
            "src/types/pixelmap.ts",
            "src/components/ViewerShell/ViewerShell.tsx",
            "src/App.tsx",
        ],
        "type_ids": [
            "function:src/hooks/usePixelGeneration.ts:usePixelGeneration",
            "function:src/components/ViewerShell/ViewerShell.tsx:ViewerShell",
        ],
        "reference": (
            "New type: GenerationRecord { id, pixelMap, prompt, type, timestamp } in pixelmap.ts.\n"
            "New hook: useGenerationHistory() with addRecord/getRecords/clearRecords, "
            "stored in localStorage.\n"
            "Modify usePixelGeneration: on success, call addRecord().\n"
            "Modify ViewerShell: accept history prop, render thumbnails with re-download.\n"
            "Modify App.tsx: wire useGenerationHistory, pass to ViewerShell.\n"
            "Add 'HISTORY' section with scrollable thumbnails, Clear history button."
        ),
    },
    # ── LEVEL 4: Advanced cross-cutting concern (very_hard) ─────────────────
    {
        "id": "advanced-response-caching",
        "category": "very_hard",
        "user_input": (
            "Design a client-side response caching layer that caches LLM responses "
            "by prompt+type hash to avoid re-generating identical avatars. "
            "Describe cache invalidation, storage limits, and all file changes."
        ),
        "source_files": [
            "src/hooks/usePixelGeneration.ts",
            "src/types/pixelmap.ts",
        ],
        "type_ids": [
            "function:src/hooks/usePixelGeneration.ts:usePixelGeneration",
        ],
        "reference": (
            "Create useResponseCache hook: caches PixelMapResponse keyed by "
            "hash(prompt + providerType + model). localStorage with max 50 entries, "
            "LRU eviction. Each entry has timestamp.\n"
            "Modify usePixelGeneration: check cache before generate(). "
            "On hit, return cached. On miss, store result on success.\n"
            "Add 'bypass-cache' to PixelGenRequest for regeneration.\n"
            "Auto-expire entries >24h. Add 'Clear cache' UI button. "
            "Handle QuotaExceededError by clearing oldest entries."
        ),
    },
]


def build_context_from_source(task: dict) -> str:
    parts = []
    for rel_path in task["source_files"]:
        content = read_source(rel_path)
        parts.append(f"=== {rel_path} ===\n{content}")
    return "\n\n".join(parts)


def call_deepseek(user_input: str, context: str, context_type: str) -> tuple[str, dict]:
    if context_type == "with_kg":
        preamble = (
            "Below is the source code and knowledge-graph structural metadata "
            "for the PixelForge codebase."
        )
    else:
        preamble = (
            "Below is the source code for the relevant PixelForge files."
        )
    prompt = (
        f"{preamble}\n"
        f"---\n{context}\n---\n\n"
        f"Task: {user_input}\n\n"
        "Provide your answer based on the context above."
    )

    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
    resp = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
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


def parse_args(argv: list[str]) -> tuple[bool, bool, int]:
    run_understand = False
    force = False
    sample = 0
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg in ("--help", "-h"):
            print(__doc__)
            sys.exit(0)
        if arg == "--run-understand":
            run_understand = True
        elif arg == "--force":
            run_understand = True
            force = True
        elif arg == "--sample" and i + 1 < len(argv):
            i += 1
            sample = int(argv[i])
        i += 1
    return run_understand, force, sample


def main(argv: list[str] | None = None) -> None:
    if argv is None:
        argv = sys.argv[1:]

    if not DEEPSEEK_API_KEY:
        print("ERROR: DEEPSEEK_API_KEY is required.", file=sys.stderr)
        sys.exit(1)

    run_understand, force, sample_n = parse_args(argv)

    # Decide whether to run the understand pipeline
    kg_exists = KG_PATH.exists()
    should_run = run_understand or force or not kg_exists

    if should_run:
        print("=" * 60)
        print("Phase 0: Understand-Anything pipeline")
        print("=" * 60)
        kg = run_understand_pipeline(TASKS, force=force)
        print("=" * 60)
        print()
    else:
        print("Knowledge graph exists (use --run-understand to refresh)")
        kg = load_knowledge_graph()

    kg_node_count = len(kg.get("nodes", []))
    kg_edge_count = len(kg.get("edges", []))

    print(f"DeepSeek model   : {DEEPSEEK_MODEL}")
    print(f"DeepSeek endpoint: {DEEPSEEK_BASE_URL}")
    print(f"Output path      : {OUTPUT_PATH}")
    print(f"Project root     : {PROJECT_ROOT}")
    print(f"Knowledge graph  : {kg_node_count} nodes, {kg_edge_count} edges")
    print()

    # Randomise tasks so each run gets a different order
    tasks = list(TASKS)
    random.shuffle(tasks)
    if sample_n > 0:
        tasks = tasks[:sample_n]
        print(f"Random sample: {len(tasks)} task(s)\n")

    output_cases = []
    total_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    context_types = ["with_source", "with_kg"]
    task_count = len(tasks)
    for idx, task in enumerate(tasks):
        for context_type in context_types:
            case_id = f"{task['id']}__{context_type}"
            print(f"[{idx + 1}/{task_count}] {case_id}  ({task['category']})")
            sys.stdout.flush()

            if context_type == "with_kg":
                context = build_kg_context(task, kg)
                context_label = "source + kg structure"
            else:
                context = build_context_from_source(task)
                context_label = "source only"

            retrieved_contexts = [context] if context else [task["user_input"]]
            context_preview = (
                context[:200].replace("\n", " | ") if context else "(none)"
            )
            print(f"  context ({context_label}, {len(context)} chars): {context_preview}...")

            try:
                response, usage = call_deepseek(task["user_input"], context, context_type)
            except Exception as e:
                print(f"  ERROR: {e}", file=sys.stderr)
                response = f"[DeepSeek API error: {e}]"
                usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
                time.sleep(RETRY_DELAY)

            for k in total_usage:
                total_usage[k] += usage[k]

            time.sleep(2)

            output_cases.append({
                "id": case_id,
                "category": task["category"],
                "context_type": context_type,
                "user_input": task["user_input"],
                "response": response,
                "retrieved_contexts": retrieved_contexts,
                "reference": task["reference"],
                "usage": usage,
            })
            print(f"  response: {response[:120].replace(chr(10), ' ')}...")

    output = {
        "total_usage": total_usage,
        "cases": output_cases,
    }
    output_path = Path(OUTPUT_PATH)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\nWrote {len(output_cases)} case(s) to {output_path}")
    print(f"Total token usage: {total_usage}")
    print(f"Evaluate with: python3.12 .understand-anything/ragas/evaluate_deepseek_ragas.py --input {output_path}")


if __name__ == "__main__":
    main()
