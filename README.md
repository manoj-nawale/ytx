# ytx

Fetch the transcript of one YouTube video and save it as TXT and JSON.

## Install

Requirements: [uv](https://docs.astral.sh/uv/) and Python 3.11 or newer (uv installs Python if it is missing).

```bash
uv tool install git+https://github.com/manoj-nawale/ytx@v0.1.0
```

Without `@v0.1.0` you get the latest commit on the default branch.

## Usage

```bash
ytx fetch <url-or-id> [--lang en] [--out ./transcripts]
```

`<url-or-id>` can be a full URL (`watch?v=`, `youtu.be/`, `shorts/`, with extra parameters) or a bare video ID.

```bash
# English captions (default)
ytx fetch https://www.youtube.com/watch?v=dQw4w9WgXcQ

# Bare ID, short URL
ytx fetch dQw4w9WgXcQ
ytx fetch https://youtu.be/dQw4w9WgXcQ

# Language preference: try German, then English
ytx fetch dQw4w9WgXcQ --lang de --lang en

# Choose the output folder
ytx fetch dQw4w9WgXcQ --out ~/notes/transcripts
```

`--lang` can be repeated. The order is the preference order. Default: `en`.

On success ytx prints the output folder and a one-line summary:

```
transcripts/dQw4w9WgXcQ
<title> | English | 61 segments | manual
```

The last field is `manual` for uploaded captions or `auto` for auto-generated ones.

## Output

ytx writes two files to `<out>/<video_id>/`:

- `transcript.txt`: plain text, segments joined with spaces and wrapped into paragraphs. No timestamps.
- `transcript.json`: the full transcript with timing and video metadata.

JSON contract (`schema_version` 1.0):

```json
{
  "schema_version": "1.0",
  "fetched_at": "2026-10-25T12:00:00Z",
  "video": {
    "id": "...", "url": "...", "title": "...", "channel": "...",
    "language": "English", "language_code": "en", "is_generated": true
  },
  "segments": [ {"start": 12.34, "duration": 4.1, "text": "..."} ]
}
```

- `fetched_at` is ISO 8601 in UTC.
- `title` and `channel` come from the YouTube oEmbed endpoint. If that request fails they are `null` and the run still succeeds.
- Segment text is raw. Speaker-change markers (`>>`) and tags such as `[music]` are kept.

## Errors

On an expected failure ytx prints `Error: <message>` to stderr and exits with code 1. No stack trace.

| Message | Meaning |
|---|---|
| `Not a valid YouTube URL or video ID: <input>` | The input is not a URL or ID that ytx understands. |
| `No captions in: <langs>. Available: <list>.` | The requested language is missing. The list shows each available code, name and `manual` or `auto`. |
| `This video has no captions (disabled or none uploaded).` | The video has no transcript. |
| `Video unavailable: it is private, removed, or the ID is invalid.` | The video cannot be played or does not exist. |
| `YouTube is blocking requests from this IP address. Try another network or wait a while.` | YouTube blocked the request. |
| `Could not fetch transcript: <detail>` | Any other YouTube transcript error. `<detail>` is the first line of the error text. |

## Limits

- Captions only. ytx does not transcribe audio. Videos without captions fail.
- YouTube may block requests from some IP addresses, such as cloud servers and VPNs.
- One video per run. No playlists or channels.
- Keep transcripts private. They are often copyrighted. The `transcripts/` folder is git-ignored; do not commit or share transcripts.

## License

No license yet. All rights reserved.
