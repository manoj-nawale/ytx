from typer.testing import CliRunner

from ytx import cli

runner = CliRunner()


def test_fetch_writes_files_and_prints_summary(tmp_path, transcript, monkeypatch):
    monkeypatch.setattr(cli, "fetch_transcript", lambda video_id, langs: transcript)
    monkeypatch.setattr(cli, "fetch_metadata", lambda url: ("Demo", "Nobody"))

    result = runner.invoke(cli.app, ["fetch", "FAKEvid0001", "--out", str(tmp_path)])

    assert result.exit_code == 0, result.output
    folder = tmp_path / "FAKEvid0001"
    assert (folder / "transcript.txt").is_file()
    assert (folder / "transcript.json").is_file()
    assert str(folder) in result.output
    assert "Demo | English | 3 segments | auto" in result.output


def test_invalid_input_exits_1_without_trace(tmp_path):
    result = runner.invoke(cli.app, ["fetch", "not a video", "--out", str(tmp_path)])
    assert result.exit_code == 1
    assert "Error:" in result.output
    assert "Traceback" not in result.output
