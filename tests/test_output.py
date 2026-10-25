import json

from youtube_transcript_api import FetchedTranscript, FetchedTranscriptSnippet

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


def test_markers_stay_raw_in_json_and_txt(tmp_path):
    snippets = [
        FetchedTranscriptSnippet(text="[music]", start=0.0, duration=1.0),
        FetchedTranscriptSnippet(
            text=">> Invented host: hello.", start=1.0, duration=2.0
        ),
        FetchedTranscriptSnippet(
            text=">> Invented guest: hi [music]", start=3.0, duration=2.0
        ),
    ]
    transcript = FetchedTranscript(
        snippets=snippets,
        video_id="FAKEvid0001",
        language="English",
        language_code="en",
        is_generated=True,
    )
    doc = build_document("FAKEvid0001", URL, None, None, transcript)
    folder = write_outputs(tmp_path, doc)

    saved = json.loads((folder / "transcript.json").read_text(encoding="utf-8"))
    assert [s["text"] for s in saved["segments"]] == [s.text for s in snippets]
    text = " ".join((folder / "transcript.txt").read_text(encoding="utf-8").split())
    assert text == "[music] >> Invented host: hello. >> Invented guest: hi [music]"
