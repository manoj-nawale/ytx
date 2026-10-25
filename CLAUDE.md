# ytx — YouTube transcript extractor

## Goal
A small Python CLI. It gets the transcript of one YouTube video and saves it as TXT and JSON.
Later layers (speaker classification, summaries) read only the JSON. They are NOT part of this phase.

## Stack
- Python, managed with uv. src layout: src/ytx/
- youtube-transcript-api 1.x — use the instance API: YouTubeTranscriptApi().fetch() and .list().
  Check the installed version before you write code. The old static get_transcript() API is removed.
- typer for the CLI.
- Video metadata (title, channel): YouTube oEmbed endpoint
  https://www.youtube.com/oembed?url=<url>&format=json — standard library urllib only, no API key.

## Command
ytx fetch <url-or-id> [--lang en] [--out ./transcripts]
- Accept full URLs (watch?v=, youtu.be/, shorts/, with extra params) and bare video IDs.
- --lang may be repeated; the order is the preference order. Default: en.
- Output folder: <out>/<video_id>/ with transcript.txt and transcript.json.
- Print the output path and a one-line summary (title, language, segment count, manual/auto).

## JSON contract (keep stable)
{
  "schema_version": "1.0",
  "fetched_at": "<ISO 8601 UTC>",
  "video": {
    "id": "...", "url": "...", "title": "...", "channel": "...",
    "language": "English", "language_code": "en", "is_generated": true
  },
  "segments": [ {"start": 12.34, "duration": 4.1, "text": "..."} ]
}
- If oEmbed fails, set title/channel to null. Do not fail the whole run.
- transcript.txt: plain text, segments joined with spaces, wrapped into paragraphs. No timestamps.
- Keep segment text raw. Do not remove '>>' (speaker change marker) or tags like '[music]'. Later layers use them.

## Errors (clear message, exit code 1, no stack trace)
- The video has no captions / captions are disabled.
- The video is private, removed, or the ID is invalid.
- The requested language is not available: list the available languages.
- YouTube blocks the request (IP block): say so plainly.

## Structure
src/ytx/cli.py     arguments and user messages only
src/ytx/fetch.py   URL parsing, captions, metadata
src/ytx/output.py  writes TXT and JSON
tests/             pytest; tests/fixtures/ holds one small saved sample

## Commands
- Run:   uv run ytx fetch <url>
- Test:  uv run pytest
- Lint:  uv run ruff check . && uv run ruff format --check .

## Rules
- Plan first. Show the plan for each milestone and wait for approval.
- Stop after each milestone. Show what changed and how to verify it. Wait for review.
- One commit per milestone. Conventional commit messages (feat:, fix:, test:, docs:).
- Tests never use the network. Mock the network calls or use fixtures.
- Never commit real transcripts. The transcripts/ folder is in .gitignore.
- Keep dependencies minimal. Ask before you add a new one.
- Tests and lint must pass before each commit.

## Do NOT build now
Docker, speaker classification, summaries, playlists or channels, config files,
databases, web UI, async or parallel downloads, PyPI publishing.

## Milestones
M1  ytx fetch <url> writes both files for a video with English captions.
M2  --lang, --out, URL formats, all error cases, tests pass, lint clean.
    Also run the tests on Python 3.11: uv run --python 3.11 pytest
M3  README (install + usage). uv tool install from GitHub works. Tag v0.1.0.
