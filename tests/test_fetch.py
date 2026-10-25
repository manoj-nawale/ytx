import io
import json
import urllib.error

import pytest

from ytx import fetch

VIDEO_ID = "FAKEvid0001"


@pytest.mark.parametrize(
    "value",
    [
        VIDEO_ID,
        f"https://www.youtube.com/watch?v={VIDEO_ID}",
        f"https://www.youtube.com/watch?v={VIDEO_ID}&t=42s",
    ],
)
def test_parse_video_id(value):
    assert fetch.parse_video_id(value) == VIDEO_ID


def test_parse_video_id_rejects_garbage():
    with pytest.raises(ValueError):
        fetch.parse_video_id("not a video")


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
