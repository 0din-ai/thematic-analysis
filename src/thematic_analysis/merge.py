"""Programmatic code deduplication across transcripts."""

from __future__ import annotations

import re
from pathlib import Path


def extract_codes_from_output(text: str) -> list[str]:
    """Extract the numbered code list from a coding step's AI output.

    Looks for a numbered list at the end of the response (the prompt
    asks the AI to "provide a clean numbered list of all code names").
    Falls back to extracting any numbered list items in the text.
    """
    # Try to find a numbered list section near the end
    # Look for patterns like "1. Code name" or "1) Code name"
    lines = text.strip().split("\n")

    # Scan backwards from the end to find the start of the numbered list
    list_start = None
    for i in range(len(lines) - 1, -1, -1):
        line = lines[i].strip()
        if re.match(r"^\d+[\.\)]\s+", line):
            list_start = i
        elif list_start is not None:
            # We've found the end of the contiguous numbered list
            break

    if list_start is not None:
        codes = []
        for line in lines[list_start:]:
            line = line.strip()
            m = re.match(r"^\d+[\.\)]\s+(.+)", line)
            if m:
                code = m.group(1).strip().rstrip(".")
                # Strip markdown bold/italic
                code = re.sub(r"\*+", "", code).strip()
                if code:
                    codes.append(code)
            elif not line:
                continue
            else:
                # Non-numbered line after list started — stop
                break
        if codes:
            return codes

    # Fallback: extract all numbered list items anywhere in the text
    codes = []
    for line in lines:
        m = re.match(r"^\d+[\.\)]\s+(.+)", line.strip())
        if m:
            code = m.group(1).strip().rstrip(".")
            code = re.sub(r"\*+", "", code).strip()
            if code:
                codes.append(code)
    return codes


def merge_code_lists(code_files: list[Path]) -> str:
    """Extract codes from individual coding outputs and deduplicate.

    Performs exact case-insensitive deduplication. Returns a formatted
    markdown document with the merged code list.
    """
    all_codes: list[tuple[str, str]] = []  # (code, source_file)

    for path in code_files:
        if not path.exists():
            continue
        content = path.read_text(encoding="utf-8")
        codes = extract_codes_from_output(content)
        source = path.stem  # e.g., "01a-codes-bryan-johns"
        for code in codes:
            all_codes.append((code, source))

    # Deduplicate (case-insensitive, keep first occurrence)
    seen: set[str] = set()
    unique: list[tuple[str, str]] = []
    duplicates: list[tuple[str, str, str]] = []  # (code, kept_source, dup_source)

    for code, source in all_codes:
        normalized = code.strip().lower()
        if normalized not in seen:
            seen.add(normalized)
            unique.append((code, source))
        else:
            # Find which source had the original
            orig_source = next(
                s for c, s in unique if c.strip().lower() == normalized
            )
            duplicates.append((code, orig_source, source))

    # Format output
    lines = ["# Merged Code List\n"]
    lines.append(
        f"**{len(unique)}** unique codes extracted from "
        f"**{len(code_files)}** transcripts "
        f"({len(all_codes)} total, {len(duplicates)} duplicates removed).\n"
    )

    lines.append("## Codes\n")
    for i, (code, _source) in enumerate(unique, 1):
        lines.append(f"{i}. {code}")

    if duplicates:
        lines.append("\n## Duplicates Removed\n")
        for code, orig, dup in duplicates:
            lines.append(f"- \"{code}\" (in {dup}, already in {orig})")

    return "\n".join(lines)
