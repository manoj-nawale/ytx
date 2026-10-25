import json
from pathlib import Path

import pytest
from youtube_transcript_api import FetchedTranscript, FetchedTranscriptSnippet

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def transcript() -> FetchedTranscript:
    data = json.loads((FIXTURES / "sample_transcript.json").read_text(encoding="utf-8"))
    data["snippets"] = [FetchedTranscriptSnippet(**s) for s in data["snippets"]]
    return FetchedTranscript(**data)
