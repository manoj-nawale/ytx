"""URL parsing, captions and video metadata."""

import http.client
import json
import re
import urllib.parse
import urllib.request

from youtube_transcript_api import FetchedTranscript, YouTubeTranscriptApi

_VIDEO_ID = re.compile(r"[A-Za-z0-9_-]{11}")
_OEMBED = "https://www.youtube.com/oembed?url={url}&format=json"


def parse_video_id(value: str) -> str:
    """Return the video ID from a bare ID or a watch?v= URL."""
    value = value.strip()
    if _VIDEO_ID.fullmatch(value):
        return value
    query = urllib.parse.parse_qs(urllib.parse.urlparse(value).query)
    candidate = query.get("v", [""])[0]
    if _VIDEO_ID.fullmatch(candidate):
        return candidate
    raise ValueError(f"Cannot find a video ID in {value!r}.")


def watch_url(video_id: str) -> str:
    return f"https://www.youtube.com/watch?v={video_id}"


def fetch_transcript(
    video_id: str, languages: tuple[str, ...] = ("en",)
) -> FetchedTranscript:
    return YouTubeTranscriptApi().fetch(video_id, languages=languages)


def fetch_metadata(url: str, timeout: float = 10) -> tuple[str | None, str | None]:
    """Return (title, channel) from oEmbed, or (None, None) on any failure."""
    endpoint = _OEMBED.format(url=urllib.parse.quote(url, safe=""))
    try:
        with urllib.request.urlopen(endpoint, timeout=timeout) as response:
            data = json.load(response)
        return data.get("title"), data.get("author_name")
    except (OSError, ValueError, AttributeError, http.client.HTTPException):
        return None, None
