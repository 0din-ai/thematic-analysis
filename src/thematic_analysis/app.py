"""Flask web UI for thematic analysis."""

from __future__ import annotations

import io
import json
import os
import sys
import webbrowser
import zipfile
from pathlib import Path
from threading import Timer

from dotenv import load_dotenv
from flask import Flask, Response, jsonify, render_template, request, send_file
from openai import OpenAI

import tiktoken

from .analysis import stream_message
from .config import (
    _save_transcript,
    generate_config,
    load_config,
)
from .merge import merge_code_lists
from .prompts import parse_prompts
from .resume import (
    determine_resume_point,
    load_conversation,
    save_conversation,
    save_stage_output,
)
from .steps import build_stage_files, build_steps
from .verification import (
    extract_quotes,
    format_registry_for_llm,
    format_verification_summary,
    load_verified_quotes,
    save_verified_quotes,
    strip_rejected_quotes,
    verify_verbatims,
    verify_verbatims_iter,
)

load_dotenv()

# Also check ~/.thematic-analysis/.env for desktop app users
_user_env = Path.home() / ".thematic-analysis" / ".env"
if _user_env.exists():
    load_dotenv(_user_env)


def _base_dir() -> Path:
    """Return the base directory for projects and data."""
    if getattr(sys, "frozen", False):
        d = Path.home() / ".thematic-analysis"
        d.mkdir(exist_ok=True)
        return d
    return Path(__file__).parent.parent.parent


def _get_template_folder() -> str:
    if getattr(sys, "frozen", False):
        return os.path.join(sys._MEIPASS, "thematic_analysis", "templates")
    return os.path.join(os.path.dirname(__file__), "templates")


app = Flask(__name__, template_folder=_get_template_folder())

# ---------------------------------------------------------------------------
# In-memory analysis state (single user)
# ---------------------------------------------------------------------------

_state: dict = {
    "config": None,              # AnalysisConfig
    "steps": None,               # list[Step]
    "step_index": 0,             # current step
    "coding_messages": {},       # {transcript_index: messages} — per-transcript
    "analysis_messages": [],     # shared messages for stages 2-7
    "last_response": "",         # last AI response (for retry)
    "streaming": False,
    "project_dir": None,         # Path
    "client": None,              # OpenAI
}


def _get_api_key() -> str | None:
    return os.getenv("OPENAI_API_KEY", "") or os.getenv("ODIN_OPENAI_API_KEY", "")


def _current_messages_for_step(step) -> list[dict]:
    """Get the appropriate message history for the current step type."""
    if step.step_type == "coding":
        ti = step.transcript_index
        return list(_state["coding_messages"].get(ti, []))
    else:
        return list(_state["analysis_messages"])


def _save_messages_for_step(step, messages: list[dict]) -> None:
    """Persist messages for the appropriate phase."""
    output_dir = _state["project_dir"] / "output"
    if step.step_type == "coding":
        ti = step.transcript_index
        _state["coding_messages"][ti] = messages
        save_conversation(output_dir, messages, phase="coding", transcript_index=ti)
    else:
        _state["analysis_messages"] = messages
        save_conversation(output_dir, messages, phase="analysis")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/check-key")
def check_key():
    key = _get_api_key()
    return jsonify({"has_key": bool(key)})


@app.route("/api/save-key", methods=["POST"])
def save_key():
    data = request.json
    key = data.get("key", "").strip()
    if not key:
        return jsonify({"error": "No key provided"}), 400

    env_dir = Path.home() / ".thematic-analysis"
    env_dir.mkdir(exist_ok=True)
    (env_dir / ".env").write_text(f"OPENAI_API_KEY={key}\n", encoding="utf-8")
    os.environ["OPENAI_API_KEY"] = key
    return jsonify({"ok": True})


@app.route("/api/projects")
def list_projects():
    projects_dir = _base_dir() / "projects"
    projects = []
    if projects_dir.exists():
        for d in sorted(projects_dir.iterdir()):
            config = d / "config.toml"
            if d.is_dir() and config.exists():
                # Load config to count transcripts and check progress
                try:
                    cfg = load_config(config)
                    stages = parse_prompts(cfg.prompts_file)
                    steps = build_steps(stages, cfg)
                    output_dir = d / "output"
                    completed = determine_resume_point(output_dir, steps)
                except Exception:
                    steps = []
                    completed = 0
                projects.append({
                    "name": d.name,
                    "path": str(d),
                    "completed": completed,
                    "total": len(steps),
                })
    return jsonify(projects)


@app.route("/api/setup", methods=["POST"])
def setup_project():
    """Create a new project from form data."""
    data = request.json
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "Project name is required"}), 400

    project_dir = _base_dir() / "projects" / name

    # Parse transcripts list: [{participant, text}, ...]
    transcripts_raw = data.get("transcripts", [])
    transcripts = [
        (t["participant"], t["text"])
        for t in transcripts_raw
        if t.get("participant", "").strip() and t.get("text", "").strip()
    ]

    # Parse note-takers list
    note_takers = [
        nt.strip() for nt in data.get("note_takers", [])
        if nt.strip()
    ]

    config_path = generate_config(
        project_dir,
        model=data.get("model", "gpt-5.4"),
        reasoning_effort=data.get("reasoning_effort", "high"),
        moderator_name=data.get("moderator_name", ""),
        research_questions=data.get("research_questions", ""),
        business_context=data.get("business_context", ""),
        transcripts=transcripts,
        note_takers=note_takers,
    )

    return jsonify({
        "ok": True,
        "project_dir": str(project_dir),
        "config_path": str(config_path),
    })


@app.route("/api/add-transcript", methods=["POST"])
def add_transcript():
    """Add a transcript to an existing project."""
    data = request.json
    project_dir = Path(data.get("project_dir", ""))
    participant = data.get("participant", "").strip()
    text = data.get("text", "").strip()

    if not participant or not text:
        return jsonify({"error": "Participant name and transcript text required"}), 400

    config_path = project_dir / "config.toml"
    if not config_path.exists():
        return jsonify({"error": "Project not found"}), 404

    # Save transcript file
    rel_path = _save_transcript(project_dir, participant, text)

    # Append to config
    entry = f'\n[[transcripts]]\npath = "{rel_path}"\nparticipant = "{participant}"\n'
    with open(config_path, "a", encoding="utf-8") as f:
        f.write(entry)

    return jsonify({"ok": True, "path": rel_path})


@app.route("/api/start", methods=["POST"])
def start_analysis():
    """Load a project and initialize analysis state."""
    data = request.json
    project_dir = Path(data.get("project_dir", ""))

    config_path = project_dir / "config.toml"
    if not config_path.exists():
        return jsonify({"error": f"Config not found: {config_path}"}), 404

    api_key = _get_api_key()
    if not api_key:
        return jsonify({"error": "API key not configured"}), 400

    config = load_config(config_path)

    if not config.transcripts:
        return jsonify({"error": "No transcripts configured. Add at least one."}), 400

    stages = parse_prompts(config.prompts_file)
    steps = build_steps(stages, config)

    output_dir = project_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    resume_point = determine_resume_point(output_dir, steps)

    # Load conversation histories
    coding_messages = {}
    for i in range(len(config.transcripts)):
        coding_messages[i] = load_conversation(
            output_dir, phase="coding", transcript_index=i
        )
    analysis_messages = load_conversation(output_dir, phase="analysis")

    _state.update({
        "config": config,
        "steps": steps,
        "step_index": resume_point,
        "coding_messages": coding_messages,
        "analysis_messages": analysis_messages,
        "last_response": "",
        "streaming": False,
        "project_dir": project_dir,
        "client": OpenAI(api_key=api_key, max_retries=3),
    })

    return jsonify({
        "ok": True,
        "total_steps": len(steps),
        "current_step": resume_point,
        "steps": [
            {
                "index": i,
                "title": s.title,
                "file_prefix": s.file_prefix,
                "filename": s.filename,
                "step_type": s.step_type,
                "participant": s.participant,
                "completed": i < resume_point,
            }
            for i, s in enumerate(steps)
        ],
    })


@app.route("/api/status")
def status():
    if _state["steps"] is None:
        return jsonify({"active": False})

    steps = _state["steps"]
    idx = _state["step_index"]

    return jsonify({
        "active": True,
        "total_steps": len(steps),
        "current_step": idx,
        "streaming": _state["streaming"],
        "complete": idx >= len(steps),
        "steps": [
            {
                "index": i,
                "title": s.title,
                "file_prefix": s.file_prefix,
                "filename": s.filename,
                "step_type": s.step_type,
                "participant": s.participant,
                "completed": i < idx,
            }
            for i, s in enumerate(steps)
        ],
    })


def _build_step_context(step, steps) -> tuple[list[dict], str]:
    """Build the full message history and prompt for a step.

    Returns (messages, prompt_content) reflecting what the LLM will
    actually receive, including any context injection.
    """
    output_dir = _state["project_dir"] / "output"
    messages = _current_messages_for_step(step)

    # First analysis step: inject coding outputs as context seed
    if step.step_type == "analysis" and not messages:
        coding_steps = [s for s in steps if s.step_type == "coding"]
        context_parts = []

        for cs in coding_steps:
            coding_file = output_dir / cs.filename
            if coding_file.exists():
                content = coding_file.read_text(encoding="utf-8")
                context_parts.append(
                    f"### Coding: {cs.participant}\n\n{content}"
                )

        merge_steps = [s for s in steps if s.step_type == "merge"]
        if merge_steps:
            merge_file = output_dir / merge_steps[0].filename
            if merge_file.exists():
                context_parts.append(
                    "### Merged Code List\n\n"
                    + merge_file.read_text(encoding="utf-8")
                )

        if context_parts:
            full_context = "\n\n---\n\n".join(context_parts)
            messages = [{
                "role": "user",
                "content": (
                    "Here are the complete coding outputs from our open "
                    "coding phase, including all codes and their associated "
                    "verbatim quotes from each transcript. Use these as the "
                    "foundation for the following analysis stages.\n\n"
                    + full_context
                ),
            }, {
                "role": "assistant",
                "content": (
                    "I've reviewed the complete coding outputs with all "
                    "codes and verbatim quotes. I'm ready to proceed "
                    "with the next stage of analysis."
                ),
            }]

    # Inject verified quotes registry for all analysis steps
    prompt_content = step.prompt
    if step.step_type == "analysis":
        registry = load_verified_quotes(output_dir)
        if registry["quotes"]:
            registry_text = format_registry_for_llm(registry)
            prompt_content = (
                prompt_content
                + "\n\n---\n\n"
                "## Verified Quotes\n\n"
                "Below is the registry of verified verbatim quotes from "
                "the coding phase. When including quotes in your analysis, "
                "you MUST select from this list. Do not paraphrase, modify, "
                "or create new quotes.\n\n"
                + registry_text
            )

    return messages, prompt_content


@app.route("/api/step-prompt")
def step_prompt():
    """Return the prompt text for a given step (or the current step)."""
    if _state["steps"] is None:
        return jsonify({"error": "No analysis active"}), 400

    idx = request.args.get("index", _state["step_index"], type=int)
    if idx < 0 or idx >= len(_state["steps"]):
        return jsonify({"error": "Invalid step index"}), 400

    step = _state["steps"][idx]
    if step.step_type == "merge":
        prompt = (
            "This step merges code lists programmatically — no AI prompt "
            "is used. Duplicate codes across transcripts are combined "
            "automatically."
        )
    else:
        _messages, prompt = _build_step_context(step, _state["steps"])

    return jsonify({
        "prompt": prompt,
        "step_type": step.step_type,
        "title": step.title,
    })


@app.route("/api/step-history")
def step_history():
    """Return the conversation history for a given step."""
    if _state["steps"] is None:
        return jsonify({"error": "No analysis active"}), 400

    idx = request.args.get("index", _state["step_index"], type=int)
    if idx < 0 or idx >= len(_state["steps"]):
        return jsonify({"error": "Invalid step index"}), 400

    step = _state["steps"][idx]
    messages, _prompt = _build_step_context(step, _state["steps"])
    return jsonify({"messages": messages})


@app.route("/api/stream")
def stream():
    """SSE endpoint — stream the current step's AI response.

    For merge steps, runs programmatically (no LLM call).
    For coding/analysis steps, streams from OpenAI.
    """
    if _state["steps"] is None or _state["config"] is None:
        return jsonify({"error": "No analysis active"}), 400

    idx = _state["step_index"]
    steps = _state["steps"]

    if idx >= len(steps):
        return jsonify({"error": "Analysis already complete"}), 400

    step = steps[idx]
    config = _state["config"]
    client = _state["client"]
    output_dir = _state["project_dir"] / "output"

    # --- Merge step: programmatic, no LLM ---
    if step.step_type == "merge":
        def generate_merge():
            _state["streaming"] = True
            # Collect coding output files
            code_files = [
                output_dir / s.filename
                for s in steps
                if s.step_type == "coding"
            ]
            merged = merge_code_lists(code_files)
            _state["last_response"] = merged
            _state["streaming"] = False
            # Send entire result as one chunk
            yield f"data: {json.dumps({'chunk': merged})}\n\n"
            yield f"data: {json.dumps({'done': True, 'step_index': idx})}\n\n"

        return Response(
            generate_merge(),
            mimetype="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    # --- LLM step: coding or analysis ---
    messages, prompt_content = _build_step_context(step, steps)

    # Persist the context seed for the first analysis step
    if step.step_type == "analysis" and not _current_messages_for_step(step):
        _save_messages_for_step(step, messages)

    user_msg = {"role": "user", "content": prompt_content}
    current_messages = messages + [user_msg]

    # Count tokens in the context being sent to the LLM
    try:
        enc = tiktoken.encoding_for_model(config.model)
    except KeyError:
        enc = tiktoken.get_encoding("cl100k_base")
    token_count = sum(len(enc.encode(m["content"])) for m in current_messages)

    def generate():
        _state["streaming"] = True
        full_response = ""
        yield f"data: {json.dumps({'token_count': token_count})}\n\n"
        try:
            for chunk in stream_message(
                client, current_messages, config.model, config.reasoning_effort
            ):
                full_response += chunk
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            _state["streaming"] = False
            return

        _state["last_response"] = full_response
        _state["streaming"] = False
        yield f"data: {json.dumps({'done': True, 'step_index': idx})}\n\n"

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.route("/api/verify")
def verify():
    """SSE endpoint — verify verbatim quotes with per-quote progress."""
    if _state["config"] is None or not _state["last_response"]:
        def empty():
            yield f"data: {json.dumps({'done': True, 'stats': {'total': 0, 'verified_count': 0, 'unverified_count': 0}, 'verified': [], 'unverified': []})}\n\n"
        return Response(empty(), mimetype="text/event-stream",
                        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    response_text = _state["last_response"]
    step = _state["steps"][_state["step_index"]]
    if step.step_type == "coding" and step.transcript_index is not None:
        transcripts = [_state["config"].transcripts[step.transcript_index]]
    else:
        transcripts = _state["config"].transcripts
    total_quotes = len(extract_quotes(response_text))

    def generate():
        results = []
        verified_count = 0
        for i, result in enumerate(verify_verbatims_iter(response_text, transcripts)):
            results.append(result)
            if result.found:
                verified_count += 1
            yield f"data: {json.dumps({'progress': i + 1, 'total': total_quotes, 'verified_so_far': verified_count})}\n\n"

        summary = format_verification_summary(results)
        summary["done"] = True
        yield f"data: {json.dumps(summary)}\n\n"

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.route("/api/reject-quotes", methods=["POST"])
def reject_quotes():
    """Strip rejected quotes from the last response."""
    data = request.json
    rejected = data.get("quotes", [])
    if not rejected or not _state["last_response"]:
        return jsonify({"ok": True, "response": _state["last_response"]})

    _state["last_response"] = strip_rejected_quotes(
        _state["last_response"], rejected
    )
    return jsonify({"ok": True, "response": _state["last_response"]})


@app.route("/api/save-verified-quotes", methods=["POST"])
def save_verified_quotes_endpoint():
    """Save verified quotes from a coding step to the registry."""
    if _state["project_dir"] is None or _state["steps"] is None:
        return jsonify({"error": "No project active"}), 400

    data = request.json
    verification_data = data.get("verification_data", {})
    accepted_indices = data.get("accepted_indices", [])

    step = _state["steps"][_state["step_index"]]
    output_dir = _state["project_dir"] / "output"

    registry = save_verified_quotes(
        output_dir, verification_data, accepted_indices, step.filename
    )
    return jsonify({
        "ok": True,
        "total_quotes": registry["metadata"]["total_quotes"],
    })


@app.route("/api/decision", methods=["POST"])
def decision():
    """Handle the user's review decision: continue, retry, or quit."""
    data = request.json
    action = data.get("action", "")

    if _state["steps"] is None:
        return jsonify({"error": "No analysis active"}), 400

    idx = _state["step_index"]
    steps = _state["steps"]
    output_dir = _state["project_dir"] / "output"

    if action == "retry":
        _state["last_response"] = ""
        return jsonify({"ok": True, "action": "retry", "step_index": idx})

    elif action == "continue":
        step = steps[idx]
        response_text = _state["last_response"]

        # Save output file
        save_stage_output(output_dir, step, response_text)

        # Update conversation history (skip for merge steps)
        if step.step_type != "merge":
            messages = _current_messages_for_step(step)
            messages.append({"role": "user", "content": step.prompt})
            messages.append({"role": "assistant", "content": response_text})
            _save_messages_for_step(step, messages)

        # Advance
        _state["step_index"] = idx + 1
        _state["last_response"] = ""

        complete = _state["step_index"] >= len(steps)
        return jsonify({
            "ok": True,
            "action": "continue",
            "step_index": _state["step_index"],
            "complete": complete,
        })

    elif action == "quit":
        # Save all conversation states
        for ti, msgs in _state["coding_messages"].items():
            if msgs:
                save_conversation(output_dir, msgs, phase="coding", transcript_index=ti)
        if _state["analysis_messages"]:
            save_conversation(output_dir, _state["analysis_messages"], phase="analysis")
        return jsonify({"ok": True, "action": "quit"})

    return jsonify({"error": f"Unknown action: {action}"}), 400


@app.route("/api/outputs")
def list_outputs():
    if _state["project_dir"] is None and _state["steps"] is None:
        return jsonify([])

    output_dir = _state["project_dir"] / "output"
    steps = _state["steps"] or []
    files = []
    for step in steps:
        filepath = output_dir / step.filename
        if filepath.exists():
            files.append({
                "filename": step.filename,
                "title": step.title,
                "size": filepath.stat().st_size,
            })
    return jsonify(files)


@app.route("/api/outputs/<filename>")
def get_output(filename: str):
    if _state["project_dir"] is None:
        return jsonify({"error": "No project active"}), 400

    # Security: only allow .md files from the output directory
    if not filename.endswith(".md"):
        return jsonify({"error": "Invalid filename"}), 400

    filepath = _state["project_dir"] / "output" / filename
    if not filepath.exists():
        return jsonify({"error": "File not found"}), 404

    content = filepath.read_text(encoding="utf-8")
    return jsonify({"filename": filename, "content": content})


@app.route("/api/download-zip")
def download_zip():
    """Create and return a zip of all project outputs."""
    if _state["project_dir"] is None:
        return jsonify({"error": "No project active"}), 400

    project_dir = _state["project_dir"]
    output_dir = project_dir / "output"

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        # Add output .md files and verified quotes registry
        if output_dir.exists():
            for f in sorted(output_dir.glob("*.md")):
                zf.write(f, f"output/{f.name}")
            registry_file = output_dir / "verified-quotes.json"
            if registry_file.exists():
                zf.write(registry_file, f"output/{registry_file.name}")

        # Add config
        config_file = project_dir / "config.toml"
        if config_file.exists():
            zf.write(config_file, "config.toml")

        # Add transcripts
        transcripts_dir = project_dir / "transcripts"
        if transcripts_dir.exists():
            for f in sorted(transcripts_dir.glob("*.txt")):
                zf.write(f, f"transcripts/{f.name}")

    buf.seek(0)
    project_name = project_dir.name
    return send_file(
        buf,
        mimetype="application/zip",
        as_attachment=True,
        download_name=f"{project_name}-analysis.zip",
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main():
    """Launch the thematic analysis web UI."""
    port = int(os.getenv("THEMATIC_ANALYSIS_PORT", "5111"))
    Timer(1.0, lambda: webbrowser.open(f"http://localhost:{port}")).start()
    print(f"Starting Thematic Analysis at http://localhost:{port}")
    app.run(host="127.0.0.1", port=port, debug=False, threaded=True)


if __name__ == "__main__":
    main()
