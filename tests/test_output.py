import json

from ytx.output import build_document, write_outputs

URL = "https://www.youtube.com/watch?v=FAKEvid0001"


def test_document_follows_contract(transcript):
    doc = build_document("FAKEvid0001", URL, "Demo", "Nobody", transcript)
    assert list(doc) == ["schema_version", "fetched_at", "video", "segments"]
    assert doc["schema_version"] == "1.0"
    assert doc["fetched_at"].endswith("Z")
    assert doc["video"] == {
        "id": "FAKEvid0001",
        "url": URL,
        "title": "Demo",
        "channel": "Nobody",
        "language": "English",
        "language_code": "en",
        "is_generated": True,
    }
    assert doc["segments"][0] == {
        "start": 0.0,
        "duration": 2.5,
        "text": "Welcome to the made-up demo.",
    }
    assert len(doc["segments"]) == 3


def test_null_metadata_is_kept_as_null(transcript):
    doc = build_document("FAKEvid0001", URL, None, None, transcript)
    assert doc["video"]["title"] is None
    assert doc["video"]["channel"] is None


def test_write_outputs_creates_both_files(tmp_path, transcript):
    doc = build_document("FAKEvid0001", URL, "Demo", "Nobody", transcript)
    folder = write_outputs(tmp_path, doc)
    assert folder == tmp_path / "FAKEvid0001"
    assert json.loads((folder / "transcript.json").read_text(encoding="utf-8")) == doc
    text = (folder / "transcript.txt").read_text(encoding="utf-8")
    assert (
        "Welcome to the made-up demo. This line is invented text only."
        in text.replace("\n", " ")
    )
    assert "0.0" not in text and "2.5" not in text
