"""Conversation persistence and resume logic.

Supports separate conversation histories for the coding phase
(per-transcript, independent) and the analysis phase (shared,
stages 2-7).
"""

from __future__ import annotations

import json
from pathlib import Path

from .steps import Step

CODING_CONVERSATION_PREFIX = "conversation_coding_"
ANALYSIS_CONVERSATION_FILE = "conversation_analysis.json"


def save_stage_output(output_dir: Path, step: Step, content: str) -> Path:
    """Save a step's AI response to a markdown file."""
    filepath = output_dir / step.filename
    filepath.write_text(content, encoding="utf-8")
    return filepath


def save_conversation(
    output_dir: Path,
    messages: list[dict],
    phase: str = "analysis",
    transcript_index: int | None = None,
) -> None:
    """Persist conversation history.

    Args:
        output_dir: Directory to save to.
        messages: The message list to save.
        phase: "coding" (per-transcript) or "analysis" (shared).
        transcript_index: Required when phase is "coding".
    """
    if phase == "coding" and transcript_index is not None:
        filename = f"{CODING_CONVERSATION_PREFIX}{transcript_index}.json"
    else:
        filename = ANALYSIS_CONVERSATION_FILE
    filepath = output_dir / filename
    filepath.write_text(
        json.dumps(messages, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def load_conversation(
    output_dir: Path,
    phase: str = "analysis",
    transcript_index: int | None = None,
) -> list[dict]:
    """Load conversation history if it exists."""
    if phase == "coding" and transcript_index is not None:
        filename = f"{CODING_CONVERSATION_PREFIX}{transcript_index}.json"
    else:
        filename = ANALYSIS_CONVERSATION_FILE
    filepath = output_dir / filename
    if filepath.exists():
        return json.loads(filepath.read_text(encoding="utf-8"))
    return []


def determine_resume_point(output_dir: Path, steps: list[Step]) -> int:
    """Return the 0-based index of the next step to execute.

    Checks which step output files exist in the output directory.
    """
    for i, step in enumerate(steps):
        filepath = output_dir / step.filename
        if not filepath.exists():
            return i
    return len(steps)
