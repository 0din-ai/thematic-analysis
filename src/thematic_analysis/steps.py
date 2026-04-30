"""Step/Stage dataclasses and step-building logic.

Steps are built dynamically based on the number of transcripts:
  - N per-transcript coding steps (one per transcript)
  - 1 merge step (programmatic code dedup, no LLM call) if N > 1
  - 6 analysis steps (axial coding through final report)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from .config import AnalysisConfig
from .prompts import Stage, inject_placeholders, parse_prompts


# Fixed analysis stages (post-coding)
ANALYSIS_STAGES = [
    ("02", "axial-focus-coding"),
    ("03", "develop-themes"),
    ("04", "why-it-matters"),
    ("05", "recommendations"),
    ("06", "find-the-gaps"),
    ("07", "reporting"),
]


def slugify(name: str) -> str:
    """Convert a participant name to a filename-safe slug."""
    s = re.sub(r"[^\w\s-]", "", name.lower())
    return re.sub(r"[\s]+", "-", s).strip("-")


@dataclass
class Step:
    prompt: str
    stage_number: int
    sub_index: int
    title: str
    file_prefix: str
    file_slug: str
    step_type: str = "analysis"  # "coding", "merge", or "analysis"
    transcript_index: int | None = None
    participant: str = ""
    metadata: dict = field(default_factory=dict)

    @property
    def filename(self) -> str:
        return f"{self.file_prefix}-{self.file_slug}.md"


def build_stage_files(
    transcripts: list[dict],
) -> list[tuple[str, str, dict]]:
    """Build (prefix, slug, metadata) list dynamically from transcript count.

    Returns tuples of (file_prefix, file_slug, metadata_dict).
    """
    files: list[tuple[str, str, dict]] = []

    # Per-transcript coding steps
    for i, t in enumerate(transcripts):
        safe = slugify(t["participant"])
        letter = chr(ord("a") + i) if i < 26 else str(i)
        files.append((
            f"01{letter}",
            f"codes-{safe}",
            {"type": "coding", "transcript_index": i,
             "participant": t["participant"]},
        ))

    # Merged code list (programmatic, no LLM)
    if len(transcripts) > 1:
        files.append((
            "01-merged",
            "codes",
            {"type": "merge"},
        ))

    # Fixed analysis stages 2-7
    for prefix, slug in ANALYSIS_STAGES:
        files.append((prefix, slug, {"type": "analysis"}))

    return files


def build_steps(stages: list[Stage], config: AnalysisConfig) -> list[Step]:
    """Build the full ordered step list.

    Stage 1 is handled specially: one coding pass per transcript, then a
    merge step.  Stages 2-7 use the parsed prompts as before.
    """
    transcripts = config.transcripts
    stage_files = build_stage_files(transcripts)
    steps: list[Step] = []

    # Separate Stage 1 prompts from the rest
    stage1 = next((s for s in stages if s.number == 1), None)
    later_stages = [s for s in stages if s.number >= 2]

    # --- Per-transcript coding steps ---
    if stage1 and stage1.sub_prompts:
        coding_prompt_template = inject_placeholders(
            stage1.sub_prompts[0], config
        )

        for i, t in enumerate(transcripts):
            # Build a prompt with just this one transcript
            path: Path = t["path"]
            if path.exists():
                content = path.read_text(encoding="utf-8")
            else:
                content = "(transcript file not found)"
            prompt = (
                coding_prompt_template
                + f"\n\n---\n\n**Transcript: {t['participant']}**"
                + f"\n\n{content}"
            )
            safe = slugify(t["participant"])
            letter = chr(ord("a") + i) if i < 26 else str(i)
            steps.append(Step(
                prompt=prompt,
                stage_number=1,
                sub_index=i,
                title=f"Open Codes — {t['participant']}",
                file_prefix=f"01{letter}",
                file_slug=f"codes-{safe}",
                step_type="coding",
                transcript_index=i,
                participant=t["participant"],
            ))

    # --- Merge step (programmatic, no prompt needed) ---
    if len(transcripts) > 1:
        steps.append(Step(
            prompt="",  # no LLM call — handled programmatically
            stage_number=1,
            sub_index=len(transcripts),
            title="Merge Code Lists",
            file_prefix="01-merged",
            file_slug="codes",
            step_type="merge",
        ))

    # --- Analysis stages 2-7 ---
    analysis_file_idx = 0
    for stage in later_stages:
        for i, sub_prompt in enumerate(stage.sub_prompts):
            prompt = inject_placeholders(sub_prompt, config)

            if analysis_file_idx >= len(ANALYSIS_STAGES):
                break
            prefix, slug = ANALYSIS_STAGES[analysis_file_idx]
            steps.append(Step(
                prompt=prompt,
                stage_number=stage.number,
                sub_index=i,
                title=stage.title,
                file_prefix=prefix,
                file_slug=slug,
                step_type="analysis",
            ))
            analysis_file_idx += 1

    return steps
