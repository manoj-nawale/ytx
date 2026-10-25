import io
import json
import urllib.error

import pytest
from youtube_transcript_api import TranscriptList, TranscriptsDisabled

from ytx import fetch

VIDEO_ID = "FAKEvid0001"


@pytest.mark.parametrize(
    "value",
    [
        VIDEO_ID,
        f"  {VIDEO_ID}  ",
        f"https://www.youtube.com/watch?v={VIDEO_ID}",
        f"https://www.youtube.com/watch?v={VIDEO_ID}&t=42s",
        f"https://www.youtube.com/watch?feature=share&v={VIDEO_ID}&list=PLfake",
        f"https://m.youtube.com/watch?v={VIDEO_ID}",
        f"https://music.youtube.com/watch?v={VIDEO_ID}",
        f"https://youtu.be/{VIDEO_ID}",
        f"https://youtu.be/{VIDEO_ID}?t=10",
        f"https://www.youtube.com/shorts/{VIDEO_ID}",
        f"https://www.youtube.com/shorts/{VIDEO_ID}?feature=share",
        f"https://www.youtube.com/embed/{VIDEO_ID}",
        f"https://www.youtube.com/live/{VIDEO_ID}",
        f"youtube.com/watch?v={VIDEO_ID}",
        f"youtu.be/{VIDEO_ID}",
    ],
)
def test_parse_video_id(value):
    assert fetch.parse_video_id(value) == VIDEO_ID


@pytest.mark.parametrize(
    "value",
    [
        "",
        "not a video",
        "short",
        "FAKEvid0001extra",
        "https://example.com/watch?v=FAKEvid0001",
        "https://www.youtube.com/watch",
        "https://www.youtube.com/watch?v=short",
        "https://www.youtube.com/playlist?list=PLfake",
        "https://youtu.be/",
        "https://www.youtube.com/shorts/",
    ],
)
def test_parse_video_id_rejects_invalid_input(value):
    with pytest.raises(ValueError):
        fetch.parse_video_id(value)


class FakeTranscript:
    def __init__(self, code, name, is_generated):
        self.language_code = code
        self.language = name
        self.is_generated = is_generated

    def fetch(self):
        return f"fetched:{self.language_code}"


def patch_list(monkeypatch, manual=(), generated=()):
    transcripts = TranscriptList(
        VIDEO_ID,
        {t.language_code: t for t in manual},
        {t.language_code: t for t in generated},
        [],
    )

    class FakeApi:
        def list(self, video_id):
            return transcripts

    monkeypatch.setattr(fetch, "YouTubeTranscriptApi", FakeApi)


def test_fetch_transcript_prefers_first_requested_language(monkeypatch):
    patch_list(
        monkeypatch,
        manual=[FakeTranscript("en", "English", False)],
        generated=[FakeTranscript("de", "German", True)],
    )
    assert fetch.fetch_transcript(VIDEO_ID, ("de", "en")) == "fetched:de"
    assert fetch.fetch_transcript(VIDEO_ID, ("en", "de")) == "fetched:en"


def test_fetch_transcript_falls_back_to_later_language(monkeypatch):
    patch_list(monkeypatch, manual=[FakeTranscript("en", "English", False)])
    assert fetch.fetch_transcript(VIDEO_ID, ("fr", "en")) == "fetched:en"


def test_fetch_transcript_language_not_available_lists_languages(monkeypatch):
    patch_list(
        monkeypatch,
        manual=[FakeTranscript("es", "Spanish", False)],
        generated=[FakeTranscript("en", "English", True)],
    )
    with pytest.raises(fetch.LanguageNotAvailable) as info:
        fetch.fetch_transcript(VIDEO_ID, ("de", "fr"))
    assert info.value.requested == ("de", "fr")
    assert sorted(info.value.available) == [
        ("en", "English", True),
        ("es", "Spanish", False),
    ]


def test_fetch_transcript_without_any_captions(monkeypatch):
    patch_list(monkeypatch)
    with pytest.raises(TranscriptsDisabled):
        fetch.fetch_transcript(VIDEO_ID, ("en",))


def test_fetch_metadata_reads_oembed(monkeypatch):
    body = json.dumps({"title": "Demo", "author_name": "Nobody"}).encode()
    monkeypatch.setattr(
        fetch.urllib.request, "urlopen", lambda *a, **k: io.BytesIO(body)
    )
    assert fetch.fetch_metadata("https://example.invalid/watch?v=x") == (
        "Demo",
        "Nobody",
    )


def test_fetch_metadata_returns_none_on_failure(monkeypatch):
    def boom(*args, **kwargs):
        raise urllib.error.URLError("offline")

    monkeypatch.setattr(fetch.urllib.request, "urlopen", boom)
    assert fetch.fetch_metadata("https://example.invalid/watch?v=x") == (None, None)
