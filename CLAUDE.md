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

flask, openai, rich, python-dotenv, rapidfuzz, tiktoken (+ tomllib from stdlib). No torch/transformers.

## Building for Distribution

Produces a macOS `.app` bundle (arm64) that non-technical users can double-click to launch.

### Build

```bash
bash scripts/build-macos.sh
```

This runs four steps: installs deps (including PyInstaller), pre-downloads tiktoken encoding data, runs PyInstaller, and verifies the bundle. Output: `dist/Thematic Analysis.app` (~48MB).

### Build files

| File | Purpose |
|------|---------|
| `thematic-analysis.spec` | PyInstaller spec — data files, hidden imports, `.app` BUNDLE config |
| `scripts/pyinstaller_entry.py` | Entry point — sets `TIKTOKEN_CACHE_DIR`, calls `main()` |
| `scripts/download_tiktoken_data.py` | Build-time helper — pre-downloads tiktoken BPE encodings to `build/tiktoken_cache/` |
| `scripts/build-macos.sh` | One-command build script |

### Frozen-mode path resolution

Both `app.py` and `config.py` use `getattr(sys, "frozen", False)` to detect PyInstaller bundles:
- Templates: `sys._MEIPASS / "thematic_analysis" / "templates"` (in `app.py:_get_template_folder()`)
- Default prompts: `sys._MEIPASS / "prompts" / "default-prompts.md"` (in `config.py:_default_prompts_path()`)
- Base dir for projects: `~/.thematic-analysis/` (in `app.py:_base_dir()`)

### Distributing to coworkers

1. Zip the app:
   ```bash
   cd dist
   zip -r "Thematic-Analysis-0.1.0-mac-arm64.zip" "Thematic Analysis.app"
   ```
2. Share the zip via Slack, Google Drive, etc.
3. Recipients: unzip, optionally drag to `/Applications`, then **right-click > Open** on first launch (required because the app is unsigned — Gatekeeper blocks unsigned apps on double-click, but right-click > Open bypasses this once).

### Limitations

- **Unsigned** — first launch requires right-click > Open. Code signing + notarization needs an Apple Developer account ($99/year).
- **arm64 only** — Intel Macs need a separate build on x86_64 hardware.
- **No auto-update** — ship a new zip for each version.

## What's Not Built Yet

1. **Google OAuth** — deferred until after acceptance testing
2. **Code signing / notarization** — requires Apple Developer account
3. **No git commits yet** — repo was initialized but nothing committed
