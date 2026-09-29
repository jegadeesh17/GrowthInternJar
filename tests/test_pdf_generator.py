"""Tests for the submission cover note (src/pdf_generator.py, src/generate_pdf.py).

The note must be a valid PDF of at most 2 pages, link to the live dashboard and
the repository, and map every assignment question to its dashboard section.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import zlib
from datetime import date
from pathlib import Path

import pytest

from src.pdf_generator import (
    DEFAULT_DASHBOARD_URL,
    DEFAULT_REPO_URL,
    MAX_PAGES,
    QUESTION_MAP,
    PdfGenerator,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _page_count(data: bytes) -> int:
    return len(re.findall(rb"/Type\s*/Page(?!s)", data))


def _text(data: bytes) -> str:
    """Decompresses every content stream and returns the raw text operators."""
    chunks = []
    for match in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", data, re.S):
        try:
            chunks.append(zlib.decompress(match.group(1)).decode("latin-1"))
        except zlib.error:
            chunks.append(match.group(1).decode("latin-1"))
    return "".join(chunks)


@pytest.fixture
def note(tmp_path: Path) -> bytes:
    gen = PdfGenerator(candidate_name="Test Candidate", submission_date=date(2026, 9, 29))
    out = gen.build_submission_pdf(tmp_path / "note.pdf")
    assert gen.page_count == _page_count(out.read_bytes())
    return out.read_bytes()


def test_note_is_valid_pdf_within_page_limit(note: bytes) -> None:
    assert note.startswith(b"%PDF")
    assert 1 <= _page_count(note) <= MAX_PAGES


def test_note_links_to_dashboard_and_repo(note: bytes) -> None:
    for url in (DEFAULT_DASHBOARD_URL, DEFAULT_REPO_URL):
        assert f"/URI ({url})".encode() in note, f"missing clickable link to {url}"
    text = _text(note)
    assert DEFAULT_DASHBOARD_URL in text


def test_note_maps_every_question_to_a_section(note: bytes) -> None:
    text = _text(note)
    for question, _, where, _ in QUESTION_MAP:
        assert question in text
        assert where.split("\n")[0] in text
    assert "Test Candidate" in text
    assert "29 September 2026" in text


def test_env_overrides_links_and_name(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DASHBOARD_URL", "https://example.com/dash/")
    monkeypatch.setenv("REPO_URL", "https://example.com/repo")
    monkeypatch.setenv("CANDIDATE_NAME", "Env Name")
    data = PdfGenerator().build_submission_pdf(tmp_path / "n.pdf").read_bytes()
    assert b"/URI (https://example.com/dash/)" in data
    assert b"/URI (https://example.com/repo)" in data
    assert "Env Name" in _text(data)


def test_creates_missing_output_directory(tmp_path: Path) -> None:
    out = PdfGenerator().build_submission_pdf(tmp_path / "a" / "b" / "note.pdf")
    assert out.is_file()


def _run_cli(env_overrides: dict) -> subprocess.CompletedProcess:
    env = {**os.environ, **env_overrides}
    return subprocess.run(
        [sys.executable, "-m", "src.generate_pdf"],
        cwd=str(PROJECT_ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )


def test_cli_writes_note(tmp_path: Path) -> None:
    out = tmp_path / "cli" / "note.pdf"
    proc = _run_cli({"OUTPUT_PDF_PATH": str(out)})
    assert proc.returncode == 0, proc.stderr
    assert "SUCCESS" in proc.stdout
    assert 1 <= _page_count(out.read_bytes()) <= MAX_PAGES


def test_cli_fails_cleanly_when_output_is_a_directory(tmp_path: Path) -> None:
    proc = _run_cli({"OUTPUT_PDF_PATH": str(tmp_path)})
    assert proc.returncode == 1
    assert "ERROR" in proc.stderr
