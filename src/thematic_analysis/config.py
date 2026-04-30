"""Configuration loading and validation."""

from __future__ import annotations

import os
import sys
import textwrap
import tomllib
from dataclasses import dataclass
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

console = Console()

VALID_REASONING_EFFORTS = ("none", "minimal", "low", "medium", "high", "xhigh")


@dataclass
class TeamMember:
    name: str
    role: str  # "moderator" or "note-taker"


@dataclass
class AnalysisConfig:
    model: str
    moderator_name: str
    research_questions: str
    business_context: str
    transcripts: list[dict]
    prompts_file: Path
    reasoning_effort: str | None = None
    team: list[TeamMember] | None = None

    @property
    def team_description(self) -> str:
        """Format team members for prompt injection."""
        if not self.team:
            return f"{self.moderator_name} (moderator)"
        parts = []
        for m in self.team:
            parts.append(f"{m.name} ({m.role})")
        return ", ".join(parts)


def _default_prompts_path() -> Path:
    """Return the path to the bundled default-prompts.md."""
    return Path(__file__).parent.parent.parent / "prompts" / "default-prompts.md"


def get_api_key() -> str:
    """Get the OpenAI API key, with helpful error if missing."""
    api_key = os.getenv("OPENAI_API_KEY", "") or os.getenv(
        "ODIN_OPENAI_API_KEY", ""
    )
    if os.getenv("ODIN_OPENAI_API_KEY") and not os.getenv("OPENAI_API_KEY"):
        console.print(
            "[yellow]Note:[/yellow] Using ODIN_OPENAI_API_KEY. "
            "Consider renaming to OPENAI_API_KEY in your .env file."
        )
    if not api_key:
        console.print(
            Panel(
                "[red bold]OpenAI API key not found.[/red bold]\n\n"
                "Create a [bold].env[/bold] file in this directory with:\n"
                "  [cyan]OPENAI_API_KEY=sk-your-key-here[/cyan]\n\n"
                "Get an API key at: https://platform.openai.com/api-keys",
                title="Missing API Key",
                border_style="red",
            )
        )
        sys.exit(1)
    return api_key


def load_config(config_path: Path) -> AnalysisConfig:
    """Load and validate the TOML config file."""
    try:
        with open(config_path, "rb") as f:
            raw = tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        console.print(
            Panel(
                f"[red bold]Could not parse config file.[/red bold]\n\n"
                f"Error: {e}\n\n"
                f"Check for missing quotes, unclosed brackets, or "
                f"mismatched delimiters in:\n  {config_path}",
                title="Config Error",
                border_style="red",
            )
        )
        sys.exit(1)

    settings = raw.get("settings", {})
    context = raw.get("context", {})
    transcripts_raw = raw.get("transcripts", [])

    config_dir = config_path.parent

    # Resolve prompts file path — default to bundled prompts
    prompts_rel = settings.get("prompts_file")
    if prompts_rel:
        prompts_path = (config_dir / prompts_rel).resolve()
    else:
        prompts_path = _default_prompts_path()

    # Resolve transcript paths relative to config dir
    transcripts = []
    for t in transcripts_raw:
        t_path = (config_dir / t["path"]).resolve()
        transcripts.append({"path": t_path, "participant": t["participant"]})

    reasoning_effort = settings.get("reasoning_effort")
    if reasoning_effort and reasoning_effort not in VALID_REASONING_EFFORTS:
        console.print(
            f"[yellow]Warning:[/yellow] Unknown reasoning_effort "
            f"'{reasoning_effort}'. Valid values: "
            f"{', '.join(VALID_REASONING_EFFORTS)}."
        )

    # Warn on missing context
    rqs = context.get("research_questions", "").strip()
    biz = context.get("business_context", "").strip()
    if not rqs:
        console.print(
            "[yellow]Warning:[/yellow] Research questions are empty. "
            "Analysis quality will suffer without them."
        )
    if not biz:
        console.print(
            "[yellow]Warning:[/yellow] Business context is empty. "
            "Stage 4 (implications) will lack context."
        )

    # Parse team members
    team_raw = raw.get("team", [])
    team = [TeamMember(name=m["name"], role=m["role"]) for m in team_raw]
    # If no team section, create one from moderator_name
    moderator_name = settings.get("moderator_name", "the moderator")
    if not team and moderator_name:
        team = [TeamMember(name=moderator_name, role="moderator")]

    return AnalysisConfig(
        model=settings.get("model", "gpt-4o"),
        moderator_name=moderator_name,
        research_questions=rqs,
        business_context=biz,
        transcripts=transcripts,
        prompts_file=prompts_path,
        reasoning_effort=reasoning_effort,
        team=team,
    )


CONFIG_TEMPLATE = textwrap.dedent("""\
    # Thematic Analysis Configuration

    [settings]
    model = "{model}"
    reasoning_effort = "{reasoning_effort}"
    moderator_name = "{moderator_name}"

    [context]
    research_questions = \"\"\"
    {research_questions}
    \"\"\"

    business_context = \"\"\"
    {business_context}
    \"\"\"
""")

TEAM_MEMBER_TEMPLATE = '[[team]]\nname = "{name}"\nrole = "{role}"\n'


def _save_transcript(
    project_dir: Path, participant_name: str, transcript_text: str
) -> str:
    """Save a transcript file and return its relative path."""
    import re

    safe_name = re.sub(r"[^\w\s-]", "", participant_name.lower())
    safe_name = re.sub(r"[\s]+", "-", safe_name)
    filename = f"{safe_name}-transcript.txt"
    transcript_path = project_dir / "transcripts" / filename
    transcript_path.write_text(transcript_text, encoding="utf-8")
    return f"./transcripts/{filename}"


def generate_config(
    project_dir: Path,
    *,
    model: str = "gpt-5.4",
    reasoning_effort: str = "high",
    moderator_name: str = "",
    research_questions: str = "",
    business_context: str = "",
    transcripts: list[tuple[str, str]] | None = None,
    note_takers: list[str] | None = None,
) -> Path:
    """Generate a config.toml and transcript files from form data.

    Args:
        transcripts: List of (participant_name, transcript_text) tuples.

    Returns the path to the created config file.
    """
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "transcripts").mkdir(exist_ok=True)
    (project_dir / "output").mkdir(exist_ok=True)

    config_content = CONFIG_TEMPLATE.format(
        model=model,
        reasoning_effort=reasoning_effort,
        moderator_name=moderator_name,
        research_questions=research_questions,
        business_context=business_context,
    )

    # Add team members
    if moderator_name:
        config_content += "\n" + TEAM_MEMBER_TEMPLATE.format(
            name=moderator_name, role="moderator"
        )
    for nt in (note_takers or []):
        if nt.strip():
            config_content += TEAM_MEMBER_TEMPLATE.format(
                name=nt.strip(), role="note-taker"
            )

    # Save transcripts
    for participant_name, transcript_text in (transcripts or []):
        if not transcript_text.strip() or not participant_name.strip():
            continue
        rel_path = _save_transcript(project_dir, participant_name, transcript_text)
        config_content += (
            f'\n[[transcripts]]\npath = "{rel_path}"\n'
            f'participant = "{participant_name}"\n'
        )

    config_file = project_dir / "config.toml"
    config_file.write_text(config_content, encoding="utf-8")
    return config_file


def find_config(directory: Path | None = None) -> Path | None:
    """Search for a config file in the given directory (default: cwd).

    Looks for config.toml, then thematic-analysis-config.toml.
    Returns the path if found, None otherwise.
    """
    search_dir = directory or Path.cwd()
    for name in ("config.toml", "thematic-analysis-config.toml"):
        candidate = search_dir / name
        if candidate.exists():
            return candidate
    return None
