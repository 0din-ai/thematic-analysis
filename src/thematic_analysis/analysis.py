"""OpenAI interaction and streaming."""

from __future__ import annotations

from collections.abc import Generator

from openai import OpenAI
from rich.console import Console

console = Console()


# Models that support the reasoning_effort parameter
_REASONING_MODELS = {"o1", "o3", "o3-mini", "o4-mini"}
_REASONING_PREFIXES = ("gpt-5", "o1-", "o3-", "o4-")


def _supports_reasoning(model: str) -> bool:
    """Check if a model supports the reasoning_effort parameter."""
    return model in _REASONING_MODELS or model.startswith(_REASONING_PREFIXES)


def _create_stream(
    client: OpenAI,
    messages: list[dict],
    model: str,
    reasoning_effort: str | None = None,
):
    """Create an OpenAI streaming completion."""
    kwargs: dict = dict(model=model, messages=messages, stream=True)
    if reasoning_effort and _supports_reasoning(model):
        kwargs["reasoning_effort"] = reasoning_effort
    return client.chat.completions.create(**kwargs)


def send_message(
    client: OpenAI,
    messages: list[dict],
    model: str,
    reasoning_effort: str | None = None,
) -> str:
    """Send messages to OpenAI and stream the response to the terminal."""
    stream = _create_stream(client, messages, model, reasoning_effort)

    response_text = ""
    for chunk in stream:
        delta = chunk.choices[0].delta
        if delta.content:
            console.print(delta.content, end="")
            response_text += delta.content

    console.print()
    return response_text


def stream_message(
    client: OpenAI,
    messages: list[dict],
    model: str,
    reasoning_effort: str | None = None,
) -> Generator[str]:
    """Yield response text chunks for SSE streaming to a web client."""
    stream = _create_stream(client, messages, model, reasoning_effort)
    for chunk in stream:
        delta = chunk.choices[0].delta
        if delta.content:
            yield delta.content
