"""Prompt parsing and placeholder injection."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

from rich.console import Console

from .config import AnalysisConfig

console = Console()


@dataclass
class Stage:
    number: int
    title: str
    sub_prompts: list[str] = field(default_factory=list)


def parse_prompts(prompts_path: Path) -> list[Stage]:
    """Parse the prompts markdown file into Stage objects.

    The file is structured with ``# N-Title`` headers for each stage.
    Sub-prompts within a stage are separated by ``---`` horizontal rules.
    The "# Fetch information" section at the end is excluded.
    """
    text = prompts_path.read_text(encoding="utf-8")

    # Strip everything from "# Fetch information" onward
    text = re.split(r"^# Fetch information", text, flags=re.MULTILINE)[0]

    # Split on numbered stage headers
    pattern = r"^(# \d+[-\s].*)$"
    parts = re.split(pattern, text, flags=re.MULTILINE)

    stages: list[Stage] = []
    i = 1  # skip preamble
    while i < len(parts) - 1:
        header = parts[i].strip()
        body = parts[i + 1]
        i += 2

        num_match = re.match(r"^# (\d+)", header)
        if not num_match:
            continue
        number = int(num_match.group(1))

        title = re.sub(r"^# \d+[-\s]*", "", header).strip()
        # Only strip wrapping quotes if the entire title is quoted
        if len(title) >= 2 and title[0] == '"' and title[-1] == '"':
            title = title[1:-1]

        raw_parts = re.split(r"^\s*---\s*$", body, flags=re.MULTILINE)
        sub_prompts = [p.strip() for p in raw_parts if p.strip()]

        if sub_prompts:
            stages.append(Stage(number=number, title=title, sub_prompts=sub_prompts))

    return stages


def inject_placeholders(prompt: str, config: AnalysisConfig) -> str:
    """Replace ``{{...}}`` placeholders with config values."""
    prompt = prompt.replace("{{MODERATOR_NAME}}", config.moderator_name)
    prompt = prompt.replace("{{TEAM_MEMBERS}}", config.team_description)
    prompt = prompt.replace("{{RESEARCH_QUESTIONS}}", config.research_questions)
    prompt = prompt.replace("{{BUSINESS_CONTEXT}}", config.business_context)

    # Check for unreplaced placeholders
    remaining = re.findall(r"\{\{[A-Z_]+\}\}", prompt)
    if remaining:
        console.print(
            f"[yellow]Warning:[/yellow] Unreplaced placeholders in prompt: "
            f"{', '.join(remaining)}"
        )

    return prompt


