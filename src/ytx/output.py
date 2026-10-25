"""Write the transcript as TXT and JSON."""

import json
import textwrap
from datetime import UTC, datetime
from pathlib import Path

from youtube_transcript_api import FetchedTranscript

SCHEMA_VERSION = "1.0"


def build_document(
    video_id: str,
    url: str,
    title: str | None,
    channel: str | None,
    transcript: FetchedTranscript,
) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "fetched_at": datetime.now(UTC)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z"),
        "video": {
            "id": video_id,
            "url": url,
            "title": title,
            "channel": channel,
            "language": transcript.language,
            "language_code": transcript.language_code,
            "is_generated": transcript.is_generated,
        },
        "segments": [
            {"start": s.start, "duration": s.duration, "text": s.text}
            for s in transcript
        ],
    }


def render_text(doc: dict) -> str:
    joined = " ".join(" ".join(s["text"].split()) for s in doc["segments"])
    return textwrap.fill(joined, width=100) + "\n"


def write_outputs(out: Path, doc: dict) -> Path:
    folder = out / doc["video"]["id"]
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "transcript.json").write_text(
        json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (folder / "transcript.txt").write_text(render_text(doc), encoding="utf-8")
    return folder
