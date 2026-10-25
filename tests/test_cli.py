import pytest
from typer.testing import CliRunner
from youtube_transcript_api import (
    AgeRestricted,
    InvalidVideoId,
    IpBlocked,
    RequestBlocked,
    TranscriptsDisabled,
    VideoUnavailable,
    VideoUnplayable,
)

from ytx import cli
from ytx.fetch import LanguageNotAvailable

runner = CliRunner()
VIDEO_ID = "FAKEvid0001"


def run_fetch(*args):
    return runner.invoke(cli.app, ["fetch", *args])


def patch_failure(monkeypatch, error):
    def fail(video_id, langs):
        raise error

    monkeypatch.setattr(cli, "fetch_transcript", fail)


def assert_clean_error(result, *expected):
    assert result.exit_code == 1, result.output
    assert result.output.startswith("Error: ")
    assert "Traceback" not in result.output
    for text in expected:
        assert text in result.output


def test_fetch_writes_files_and_prints_summary(tmp_path, transcript, monkeypatch):
    monkeypatch.setattr(cli, "fetch_transcript", lambda video_id, langs: transcript)
    monkeypatch.setattr(cli, "fetch_metadata", lambda url: ("Demo", "Nobody"))

    result = run_fetch(VIDEO_ID, "--out", str(tmp_path))

    assert result.exit_code == 0, result.output
    folder = tmp_path / VIDEO_ID
    assert (folder / "transcript.txt").is_file()
    assert (folder / "transcript.json").is_file()
    assert str(folder) in result.output
    assert "Demo | English | 3 segments | auto" in result.output


def test_default_language_is_english(tmp_path, transcript, monkeypatch):
    seen = []
    monkeypatch.setattr(
        cli,
        "fetch_transcript",
        lambda video_id, langs: seen.append(langs) or transcript,
    )
    monkeypatch.setattr(cli, "fetch_metadata", lambda url: (None, None))
    assert run_fetch(VIDEO_ID, "--out", str(tmp_path)).exit_code == 0
    assert seen == [("en",)]


def test_repeated_lang_keeps_preference_order(tmp_path, transcript, monkeypatch):
    seen = []
    monkeypatch.setattr(
        cli,
        "fetch_transcript",
        lambda video_id, langs: seen.append(langs) or transcript,
    )
    monkeypatch.setattr(cli, "fetch_metadata", lambda url: (None, None))
    result = run_fetch(VIDEO_ID, "--lang", "de", "--lang", "en", "--out", str(tmp_path))
    assert result.exit_code == 0, result.output
    assert seen == [("de", "en")]


def test_out_folder_is_created_and_used(tmp_path, transcript, monkeypatch):
    monkeypatch.setattr(cli, "fetch_transcript", lambda video_id, langs: transcript)
    monkeypatch.setattr(cli, "fetch_metadata", lambda url: (None, None))
    target = tmp_path / "a" / "b"
    assert run_fetch(VIDEO_ID, "--out", str(target)).exit_code == 0
    assert (target / VIDEO_ID / "transcript.json").is_file()


def test_url_formats_resolve_to_the_same_video(tmp_path, transcript, monkeypatch):
    seen = []
    monkeypatch.setattr(
        cli,
        "fetch_transcript",
        lambda video_id, langs: seen.append(video_id) or transcript,
    )
    monkeypatch.setattr(cli, "fetch_metadata", lambda url: (None, None))
    for value in (
        f"https://youtu.be/{VIDEO_ID}?t=5",
        f"https://www.youtube.com/shorts/{VIDEO_ID}",
        f"https://www.youtube.com/watch?v={VIDEO_ID}&list=PLfake",
    ):
        assert run_fetch(value, "--out", str(tmp_path)).exit_code == 0
    assert seen == [VIDEO_ID] * 3


# One test per error case from CLAUDE.md.


def test_error_invalid_url_or_id(tmp_path):
    result = run_fetch("not a video", "--out", str(tmp_path))
    assert_clean_error(result, "Not a valid YouTube URL or video ID: not a video")
    assert not any(tmp_path.iterdir())


def test_error_captions_disabled(tmp_path, monkeypatch):
    patch_failure(monkeypatch, TranscriptsDisabled(VIDEO_ID))
    result = run_fetch(VIDEO_ID, "--out", str(tmp_path))
    assert_clean_error(result, "no captions")


def test_error_video_unavailable(tmp_path, monkeypatch):
    patch_failure(monkeypatch, VideoUnavailable(VIDEO_ID))
    result = run_fetch(VIDEO_ID, "--out", str(tmp_path))
    assert_clean_error(result, "Video unavailable", "private, removed")


def test_error_video_unplayable(tmp_path, monkeypatch):
    patch_failure(monkeypatch, VideoUnplayable(VIDEO_ID, "Private video", []))
    result = run_fetch(VIDEO_ID, "--out", str(tmp_path))
    assert_clean_error(result, "Video unavailable", "private, removed")


def test_error_youtube_rejects_the_id(tmp_path, monkeypatch):
    patch_failure(monkeypatch, InvalidVideoId(VIDEO_ID))
    result = run_fetch(VIDEO_ID, "--out", str(tmp_path))
    assert_clean_error(result, "Video unavailable", "ID is invalid")


def test_error_language_not_available_lists_languages(tmp_path, monkeypatch):
    available = [("en", "English", True), ("es", "Spanish", False)]
    patch_failure(monkeypatch, LanguageNotAvailable(VIDEO_ID, ("de", "fr"), available))
    result = run_fetch(VIDEO_ID, "--lang", "de", "--lang", "fr", "--out", str(tmp_path))
    assert_clean_error(
        result,
        "No captions in: de, fr.",
        "en (English, auto)",
        "es (Spanish, manual)",
    )


def test_error_ip_blocked(tmp_path, monkeypatch):
    patch_failure(monkeypatch, IpBlocked(VIDEO_ID))
    result = run_fetch(VIDEO_ID, "--out", str(tmp_path))
    assert_clean_error(result, "YouTube is blocking requests from this IP address")


def test_error_request_blocked(tmp_path, monkeypatch):
    patch_failure(monkeypatch, RequestBlocked(VIDEO_ID))
    result = run_fetch(VIDEO_ID, "--out", str(tmp_path))
    assert_clean_error(result, "YouTube is blocking requests from this IP address")


def test_error_other_library_exception_is_clean(tmp_path, monkeypatch):
    patch_failure(monkeypatch, AgeRestricted(VIDEO_ID))
    result = run_fetch(VIDEO_ID, "--out", str(tmp_path))
    assert_clean_error(result, "Could not fetch transcript:")


@pytest.mark.parametrize("value", ["", "https://example.com/watch?v=FAKEvid0001"])
def test_error_invalid_input_variants(tmp_path, value):
    result = run_fetch(value, "--out", str(tmp_path))
    assert_clean_error(result, "Not a valid YouTube URL or video ID")
