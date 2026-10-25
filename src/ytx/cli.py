"""Command line interface: arguments and user messages only."""

from pathlib import Path
from typing import Annotated

import typer
from youtube_transcript_api import (
    InvalidVideoId,
    RequestBlocked,
    TranscriptsDisabled,
    VideoUnavailable,
    VideoUnplayable,
    YouTubeTranscriptApiException,
)

from ytx.fetch import (
    LanguageNotAvailable,
    fetch_metadata,
    fetch_transcript,
    parse_video_id,
    watch_url,
)
from ytx.output import build_document, write_outputs

app = typer.Typer(add_completion=False, no_args_is_help=True)


@app.callback()
def main() -> None:
    """Fetch YouTube transcripts."""


def _message(error: Exception, video: str) -> str:
    """Turn an expected failure into a one-line user message."""
    if isinstance(error, ValueError):
        return f"Not a valid YouTube URL or video ID: {video}"
    if isinstance(error, LanguageNotAvailable):
        available = ", ".join(
            f"{code} ({name}, {'auto' if generated else 'manual'})"
            for code, name, generated in error.available
        )
        return f"No captions in: {', '.join(error.requested)}. Available: {available}."
    if isinstance(error, TranscriptsDisabled):
        return "This video has no captions (disabled or none uploaded)."
    if isinstance(error, (VideoUnavailable, VideoUnplayable, InvalidVideoId)):
        return "Video unavailable: it is private, removed, or the ID is invalid."
    if isinstance(error, RequestBlocked):
        return (
            "YouTube is blocking requests from this IP address. "
            "Try another network or wait a while."
        )
    detail = getattr(error, "cause", None) or str(error)
    first_line = next((ln.strip() for ln in detail.splitlines() if ln.strip()), "")
    return f"Could not fetch transcript: {first_line or type(error).__name__}"


@app.command()
def fetch(
    video: Annotated[str, typer.Argument(help="Video URL or ID.")],
    lang: Annotated[
        list[str] | None,
        typer.Option(help="Language code; repeat for fallbacks, first is preferred."),
    ] = None,
    out: Annotated[Path, typer.Option(help="Output folder.")] = Path("transcripts"),
) -> None:
    """Save the transcript of one video as TXT and JSON."""
    try:
        video_id = parse_video_id(video)
        transcript = fetch_transcript(video_id, tuple(lang or ["en"]))
    except (ValueError, LanguageNotAvailable, YouTubeTranscriptApiException) as error:
        typer.echo(f"Error: {_message(error, video)}", err=True)
        raise typer.Exit(code=1) from None

    url = watch_url(video_id)
    title, channel = fetch_metadata(url)
    doc = build_document(video_id, url, title, channel, transcript)
    folder = write_outputs(out, doc)

    kind = "auto" if transcript.is_generated else "manual"
    typer.echo(str(folder))
    typer.echo(
        f"{title or video_id} | {transcript.language} | "
        f"{len(doc['segments'])} segments | {kind}"
    )
