# CLAUDE.md — Thematic Analysis Tool

## What This Is

A web-based tool for automated thematic analysis of customer interview transcripts. Built for non-technical user researchers who paste transcripts and review AI-generated qualitative analysis through a browser UI.

Linear ticket: 0DIN-1370. Extracted from the odin-ml susfactor monorepo.

## Running

```bash
uv sync
uv run thematic-analysis   # opens browser to localhost:5111
```

## Architecture

Flask single-page app. Entry point: `src/thematic_analysis/app.py:main()`.

### Modules

| Module | Purpose |
|--------|---------|
| `app.py` | Flask backend — all API routes, SSE streaming, state management |
| `analysis.py` | OpenAI SDK wrapper — `send_message()` (terminal), `stream_message()` (SSE generator). Only sends `reasoning_effort` for models that support it (gpt-5.x, o1, o3, o4). |
| `config.py` | `AnalysisConfig` dataclass, `load_config()`, `generate_config()`, `TeamMember` dataclass |
| `prompts.py` | `parse_prompts()` splits markdown by `# N-` headers. `inject_placeholders()` replaces `{{MODERATOR_NAME}}`, `{{TEAM_MEMBERS}}`, `{{RESEARCH_QUESTIONS}}`, `{{BUSINESS_CONTEXT}}` |
| `steps.py` | Dynamic step building. `build_steps()` creates N coding steps (one per transcript) + 1 merge step + 6 analysis steps. `Step` dataclass has `step_type` ("coding"/"merge"/"analysis") and `transcript_index`. |
| `merge.py` | `merge_code_lists()` — extracts numbered code lists from coding outputs, deduplicates (exact, case-insensitive). No LLM call. |
| `resume.py` | Separate conversation histories: `conversation_coding_{N}.json` per transcript, `conversation_analysis.json` for stages 2-7. `determine_resume_point()` takes dynamic step list. |
| `verification.py` | Verbatim quote verification. `verify_verbatims_iter()` yields per-quote results (SSE streaming). Exact match first (fast), then fuzzy match with `difflib.SequenceMatcher` + character-overlap pre-filter + `quick_ratio()` pre-filter. |
| `cli.py` | Original CLI (kept for dev/debug, not user-facing). Entry point is `app.py`. |
| `templates/index.html` | Single-page app: API key setup → project setup → transcript management → analysis (streaming + review) → outputs |

### Step Flow

For N transcripts, steps are:
1. `01a-codes-{participant}.md` through `01{letter}-codes-{participant}.md` — per-transcript coding (independent conversations)
2. `01-merged-codes.md` — programmatic dedup (no LLM, only if N > 1)
3. `02-axial-focus-coding.md` through `07-reporting.md` — shared conversation seeded with full coding outputs

### API Routes

| Route | Method | Purpose |
|-------|--------|---------|
| `/` | GET | Serve SPA |
| `/api/check-key` | GET | Check if API key configured |
| `/api/save-key` | POST | Save API key to `~/.thematic-analysis/.env` |
| `/api/projects` | GET | List existing projects with progress |
| `/api/setup` | POST | Create project from form data (incl. multiple transcripts, note-takers) |
| `/api/add-transcript` | POST | Add transcript to existing project |
| `/api/start` | POST | Load project, build steps, check resume |
| `/api/status` | GET | Current step, progress, step list |
| `/api/stream` | GET (SSE) | Stream current step's LLM response (or run merge programmatically) |
| `/api/verify` | GET (SSE) | Verify verbatim quotes with per-quote progress |
| `/api/reject-quotes` | POST | Strip rejected quotes from last response |
| `/api/decision` | POST | User review: continue/retry/quit |
| `/api/outputs` | GET | List completed output files |
| `/api/outputs/<file>` | GET | Get output file contents |
| `/api/download-zip` | GET | Download all outputs as zip |

### Config Format (TOML)

```toml
[settings]
model = "gpt-5.4"
reasoning_effort = "high"
moderator_name = "Kate Silverstein"

[context]
research_questions = """..."""
business_context = """..."""

[[team]]
name = "Kate Silverstein"
role = "moderator"

[[team]]
name = "Stephen Golub"
role = "note-taker"

[[transcripts]]
path = "./transcripts/alice-transcript.txt"
participant = "Alice"
```

## Dependencies

flask, openai, rich, python-dotenv (+ tomllib from stdlib). No torch/transformers.

## What's Not Built Yet

1. **PyInstaller desktop packaging** — `.app` bundle so users double-click to launch
2. **Google OAuth** — deferred until after acceptance testing
3. **No git commits yet** — repo was initialized but nothing committed
