"""Command line interface: arguments and user messages only."""

from pathlib import Path
from typing import Annotated

import typer
from youtube_transcript_api import YouTubeTranscriptApiException

from ytx.fetch import fetch_metadata, fetch_transcript, parse_video_id, watch_url
from ytx.output import build_document, write_outputs

app = typer.Typer(add_completion=False, no_args_is_help=True)


@app.callback()
def main() -> None:
    """Fetch YouTube transcripts."""


@app.command()
def fetch(
    video: Annotated[str, typer.Argument(help="Video URL or ID.")],
    lang: Annotated[
        list[str] | None, typer.Option(help="Language code; repeat for fallbacks.")
    ] = None,
    out: Annotated[Path, typer.Option(help="Output folder.")] = Path("transcripts"),
) -> None:
    """Save the transcript of one video as TXT and JSON."""
    try:
        video_id = parse_video_id(video)
        transcript = fetch_transcript(video_id, tuple(lang or ["en"]))
    except (ValueError, YouTubeTranscriptApiException) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(code=1) from None

    url = watch_url(video_id)
    title, channel = fetch_metadata(url)
    doc = build_document(video_id, url, title, channel, transcript)
    folder = write_outputs(out, doc)

    kind = "auto" if transcript.is_generated else "manual"
    typer.echo(str(folder))
    typer.echo(
        f"{title or video_id} | {transcript.language} | {len(doc['segments'])} segments | {kind}"
    )
