"""URL parsing, captions and video metadata."""

import http.client
import json
import re
import urllib.parse
import urllib.request

from youtube_transcript_api import (
    FetchedTranscript,
    NoTranscriptFound,
    TranscriptsDisabled,
    YouTubeTranscriptApi,
)

_VIDEO_ID = re.compile(r"[A-Za-z0-9_-]{11}")
_OEMBED = "https://www.youtube.com/oembed?url={url}&format=json"
_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com"}
_SHORT_HOST = "youtu.be"
_ID_IN_PATH = {"shorts", "embed", "live", "v"}


class LanguageNotAvailable(Exception):
    """None of the requested languages exist. `available` lists what does."""

    def __init__(
        self,
        video_id: str,
        requested: tuple[str, ...],
        available: list[tuple[str, str, bool]],
    ):
        super().__init__(video_id)
        self.video_id = video_id
        self.requested = requested
        self.available = available  # (language_code, language, is_generated)


def parse_video_id(value: str) -> str:
    """Return the video ID from a bare ID or a YouTube URL.

    Accepts watch?v=, youtu.be/, shorts/, embed/ and live/ URLs, with or
    without a scheme, and ignores extra parameters.
    """
    value = value.strip()
    if _VIDEO_ID.fullmatch(value):
        return value
    candidate = _id_from_url(value)
    if candidate and _VIDEO_ID.fullmatch(candidate):
        return candidate
    raise ValueError(f"Cannot find a video ID in {value!r}.")


def _id_from_url(value: str) -> str | None:
    try:
        parsed = urllib.parse.urlparse(value if "://" in value else f"https://{value}")
        host = parsed.hostname
    except ValueError:
        return None
    segments = [s for s in parsed.path.split("/") if s]
    if host == _SHORT_HOST:
        return segments[0] if segments else None
    if host not in _HOSTS:
        return None
    if segments[:1] == ["watch"]:
        return urllib.parse.parse_qs(parsed.query).get("v", [None])[0]
    if len(segments) >= 2 and segments[0] in _ID_IN_PATH:
        return segments[1]
    return None


def watch_url(video_id: str) -> str:
    return f"https://www.youtube.com/watch?v={video_id}"


def fetch_transcript(
    video_id: str, languages: tuple[str, ...] = ("en",)
) -> FetchedTranscript:
    """Fetch the first available language in `languages` (order = preference)."""
    transcripts = YouTubeTranscriptApi().list(video_id)
    try:
        return transcripts.find_transcript(languages).fetch()
    except NoTranscriptFound:
        available = [(t.language_code, t.language, t.is_generated) for t in transcripts]
        if not available:
            raise TranscriptsDisabled(video_id) from None
        raise LanguageNotAvailable(video_id, languages, available) from None


def fetch_metadata(url: str, timeout: float = 10) -> tuple[str | None, str | None]:
    """Return (title, channel) from oEmbed, or (None, None) on any failure."""
    endpoint = _OEMBED.format(url=urllib.parse.quote(url, safe=""))
    try:
        with urllib.request.urlopen(endpoint, timeout=timeout) as response:
            data = json.load(response)
        return data.get("title"), data.get("author_name")
    except (OSError, ValueError, AttributeError, http.client.HTTPException):
        return None, None
