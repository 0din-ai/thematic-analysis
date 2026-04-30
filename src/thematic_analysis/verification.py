"""Verbatim quote verification against source transcripts."""

from __future__ import annotations

import difflib
import re
from collections.abc import Generator
from dataclasses import dataclass
from pathlib import Path


_TRAILING_PUNCT = re.compile(r"[.,;:!?…]+$")


def _normalize_quote(text: str) -> str:
    """Strip trailing punctuation to avoid mismatches (e.g. comma→period)."""
    return _TRAILING_PUNCT.sub("", text).strip()


@dataclass
class VerbatimResult:
    quote: str
    found: bool
    participant: str = ""
    line_number: int = 0
    context: str = ""  # surrounding lines for display
    closest_match: str = ""
    match_ratio: float = 0.0


def extract_quotes(text: str) -> list[str]:
    """Extract quoted text from an AI response.

    Looks for text in double quotes, curly quotes, or markdown
    blockquote-style verbatims. Filters out very short quotes
    (< 10 chars) which are likely code names, not verbatims.
    """
    quotes: list[str] = []

    # Standard double quotes and curly quotes
    for pattern in [
        r'"([^"]{10,})"',        # straight double quotes
        r'\u201c([^\u201d]{10,})\u201d',  # curly quotes
        r'> *"?([^"\n]{10,})"?',  # blockquote style
    ]:
        for match in re.finditer(pattern, text):
            q = match.group(1).strip()
            if q and q not in quotes:
                quotes.append(q)

    return quotes


def _find_in_transcript(
    quote: str, transcript_lines: list[str]
) -> tuple[int, str]:
    """Search for a quote in transcript lines.

    Returns (line_number, context) if found, (0, "") if not.
    Line numbers are 1-based.
    """
    full_text = "\n".join(transcript_lines)

    # Exact substring match (case-insensitive), trimming trailing punctuation
    # from the quote so comma→period changes don't cause mismatches.
    lower_text = full_text.lower()
    lower_quote = _normalize_quote(quote.lower().strip())

    idx = lower_text.find(lower_quote)
    if idx >= 0:
        # Find line number
        line_num = full_text[:idx].count("\n") + 1
        # Context: the line containing the match +/- 1 line
        start_line = max(0, line_num - 2)
        end_line = min(len(transcript_lines), line_num + 1)
        context = "\n".join(transcript_lines[start_line:end_line])
        return line_num, context

    return 0, ""


def _fuzzy_match(
    quote: str, transcript_lines: list[str], threshold: float = 0.80
) -> tuple[str, float, int]:
    """Find the closest fuzzy match for a quote in the transcript.

    Returns (best_match, ratio, line_number).

    Uses a two-pass approach for performance:
    1. Quick character-overlap pre-filter (very fast) to skip obviously bad windows
    2. Full SequenceMatcher.ratio() only on candidates that pass the pre-filter
    """
    best_match = ""
    best_ratio = 0.0
    best_line = 0

    # Build word list with line number tracking
    words: list[str] = []
    word_line: list[int] = []  # line number (1-based) for each word
    for line_idx, line in enumerate(transcript_lines):
        for w in line.split():
            words.append(w)
            word_line.append(line_idx + 1)

    if not words:
        return "", 0.0, 0

    quote_lower = _normalize_quote(quote.lower())
    quote_words = quote.split()
    window_size = len(quote_words)

    # Narrower window range to reduce search space
    min_window = max(3, int(window_size * 0.8))
    max_window = min(int(window_size * 1.2) + 1, len(words) + 1)

    # Pre-compute quote character set for fast overlap check
    quote_chars = set(quote_lower)

    for wsize in range(min_window, max_window):
        for i in range(len(words) - wsize + 1):
            candidate = " ".join(words[i : i + wsize])
            candidate_lower = _normalize_quote(candidate.lower())

            # Fast pre-filter: check character overlap
            # If fewer than 60% of quote chars appear in candidate, skip
            if len(quote_chars & set(candidate_lower)) < len(quote_chars) * 0.6:
                continue

            # Use quick_ratio first (upper bound, very fast)
            sm = difflib.SequenceMatcher(None, quote_lower, candidate_lower)
            if sm.quick_ratio() < best_ratio:
                continue

            ratio = sm.ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = candidate
                best_line = word_line[i]

    if best_ratio >= threshold:
        return best_match, best_ratio, best_line

    return "", 0.0, 0


def verify_verbatims(
    ai_response: str, transcripts: list[dict]
) -> list[VerbatimResult]:
    """Check that quoted text in the AI response appears in transcripts.

    Non-streaming version — returns all results at once.
    """
    return list(verify_verbatims_iter(ai_response, transcripts))


def verify_verbatims_iter(
    ai_response: str, transcripts: list[dict]
) -> Generator[VerbatimResult, None, None]:
    """Check quotes one at a time, yielding results as they complete.

    Use this for streaming progress to the frontend.
    """
    quotes = extract_quotes(ai_response)
    if not quotes:
        return

    # Load all transcripts once
    transcript_data: list[tuple[str, list[str]]] = []
    for t in transcripts:
        path: Path = t["path"]
        if path.exists():
            lines = path.read_text(encoding="utf-8").splitlines()
            transcript_data.append((t["participant"], lines))

    for quote in quotes:
        found = False
        result = VerbatimResult(quote=quote, found=False)

        # Try exact match first (fast)
        for participant, lines in transcript_data:
            line_num, context = _find_in_transcript(quote, lines)
            if line_num > 0:
                result = VerbatimResult(
                    quote=quote,
                    found=True,
                    participant=participant,
                    line_number=line_num,
                    context=context,
                    match_ratio=1.0,
                )
                found = True
                break

        # If no exact match, try fuzzy (slow)
        if not found:
            for participant, lines in transcript_data:
                match, ratio, line_num = _fuzzy_match(quote, lines)
                if ratio > result.match_ratio:
                    result = VerbatimResult(
                        quote=quote,
                        found=False,
                        participant=participant,
                        line_number=line_num,
                        closest_match=match,
                        match_ratio=ratio,
                    )

        yield result


def strip_rejected_quotes(text: str, rejected_quotes: list[str]) -> str:
    """Remove rejected verbatim quotes from AI response text.

    Removes the quote and its surrounding quotation marks. Also removes
    any line that becomes empty after removal.
    """
    for quote in rejected_quotes:
        # Remove with surrounding quotes
        for pattern in [f'"{quote}"', f'\u201c{quote}\u201d']:
            text = text.replace(pattern, "[quote removed]")
    return text


def format_verification_summary(results: list[VerbatimResult]) -> dict:
    """Format verification results for the API response.

    Returns a dict with:
      - verified: list of verified quotes with citations
      - unverified: list of unverified quotes with closest matches
      - stats: {total, verified_count, unverified_count}
    """
    verified = []
    unverified = []

    for r in results:
        if r.found:
            verified.append({
                "quote": r.quote,
                "participant": r.participant,
                "line_number": r.line_number,
                "context": r.context,
            })
        else:
            entry = {"quote": r.quote}
            if r.closest_match:
                entry["closest_match"] = r.closest_match
                entry["match_ratio"] = round(r.match_ratio, 2)
                entry["participant"] = r.participant
                entry["line_number"] = r.line_number
            unverified.append(entry)

    return {
        "verified": verified,
        "unverified": unverified,
        "stats": {
            "total": len(results),
            "verified_count": len(verified),
            "unverified_count": len(unverified),
        },
    }
