# PixelForge KG Evaluation Pipeline

Measure how much the `understand-anything` knowledge graph improves LLM code
understanding. Each coding task is answered twice by DeepSeek — once with source files
only and once with source + KG structural metadata — then scored with
RAGAS metrics. Tasks are randomly shuffled (and optionally sampled) so
each run produces different results.

---

## Pipeline Overview

```
generate_deepseek_tasks.py  ───►  deepseek_tasks_output.json
                                       │
                                       ▼
                              evaluate_deepseek_ragas.py
                                       │
                                       ▼
                              deepseek_ragas_results.json  +  .html
```

### 1. Generate — `generate_deepseek_tasks.py`

Reads the knowledge graph (built by `understand-anything`), then for each task:
- **with_kg** — sends the task + source code + KG structural metadata to DeepSeek
- **with_source** — sends the task + source files only (no KG metadata)

Tasks are randomly shuffled each run. Use `--sample N` to run a random
subset of N tasks.

Output: `deepseek_tasks_output.json` (written to the `ragas/` directory)

### 2. Evaluate — `evaluate_deepseek_ragas.py`

Scores each `(question, response, context, reference)` quadruple with RAGAS:

| Metric | What it measures | Default threshold |
|---|---|---|
| Faithfulness | Is the response factually supported by the context? | ≥ 0.70 |
| Context Precision | Are relevant context chunks ranked first? | ≥ 0.50 |
| Context Recall | Were all relevant context chunks retrieved? | ≥ 0.50 |
| Answer Relevancy | How relevant is the response to the question? | ≥ 0.70 |

Output: `deepseek_ragas_results.json` + auto-generated HTML report.

---

## Usage

### Prerequisites

```bash
pip install openai ragas
```

Requires a DeepSeek API key (or any OpenAI-compatible endpoint).

### Full pipeline (generate → evaluate)

```bash
cd pixelforge

# 1. Set your API key
export DEEPSEEK_API_KEY="sk-..."

# 2. Generate LLM responses (run all tasks, or use --sample 2 for a quick run)
python3.12 .understand-anything/ragas/generate_deepseek_tasks.py
python3.12 .understand-anything/ragas/generate_deepseek_tasks.py --sample 2

# 3. Evaluate with RAGAS (auto-generates HTML report)
python3.12 .understand-anything/ragas/evaluate_deepseek_ragas.py \
    --input .understand-anything/ragas/deepseek_tasks_output.json
```

### Evaluate only (if responses already generated)

```bash
python3.12 .understand-anything/ragas/evaluate_deepseek_ragas.py \
    --input .understand-anything/ragas/deepseek_tasks_output.json
```

---

## Tasks

Defined inline in `generate_deepseek_tasks.py` as the `TASKS` list. Each task
specifies:

| Field | Purpose |
|---|---|
| `id` | Unique identifier |
| `category` | Difficulty (`hard`, `very_hard`) |
| `user_input` | The question or design task for the LLM |
| `source_files` | Files that contain the relevant code |
| `reference` | Ground-truth answer used by Context Precision/Recall |
| `type_ids` | KG node IDs linking the task to the knowledge graph |

### Writing new tasks

Add a new dict to the `TASKS` list. Point `source_files` at the relevant code
and `type_ids` at the corresponding KG nodes (file, function, class, type, or
const IDs from the knowledge graph).

---

## Environment Variables

| Variable | Default | Purpose |
|---|---|---|
| `DEEPSEEK_API_KEY` | *(required)* | API key for DeepSeek |
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com` | OpenAI-compatible endpoint |
| `DEEPSEEK_MODEL` | `deepseek-chat` | Model for task generation + RAGAS scoring |
| `DEEPSEEK_EMBED_MODEL` | *(unset)* | Embedding model for Answer Relevancy (skip if unset) |
| `OUTPUT_PATH` | `deepseek_tasks_output.json` | Where task responses are written |
| `RAGAS_LLM_MAX_TOKENS` | `16384` | Max tokens per RAGAS scoring call |
| `RETRY_DELAY` | `10` | Seconds to wait after a DeepSeek API error |

---

## File Layout

```
.understand-anything/
  knowledge-graph.json        ← built by understand-anything pipeline
  ragas/
    README.md
    generate_deepseek_tasks.py     ← step 1: generate responses
    evaluate_deepseek_ragas.py     ← step 2: RAGAS scoring + HTML report
```

Output files (`deepseek_tasks_output.json`, `deepseek_ragas_results.json`,
`deepseek_ragas_results.html`) are written to the project root by default.

---

## Interpreting Results

- **Faithfulness** is the most important metric for this pipeline — it tells you
  whether the KG context actually helps the LLM produce factually accurate code
  answers.
- **Context Precision** and **Context Recall** reflect whether the right files
  were included in the KG context for each task.
- **Answer Relevancy** requires an embedding model; it's optional.
- The HTML report shows per-metric scores, per-case breakdowns with response
  and reference views, and category filters.
