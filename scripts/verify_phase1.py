"""Validate snapshot hashes and reviewed evidence links, not RAG quality."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from pypdf import PdfReader


def normalized(text: str) -> str:
    return re.sub(r"\s+", " ", text).casefold()


def verify(root: Path) -> dict:
    manifest = json.loads((root / "data/source_manifest.json").read_text())
    sources = {s["document_id"]: s for s in manifest["sources"]}
    assert len(sources) == len(manifest["sources"]) == 2
    readers = {}
    for document_id, source in sources.items():
        path = root / source["local_path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == source["sha256"], document_id
        readers[document_id] = PdfReader(path)
        assert len(readers[document_id].pages) == source["page_count"], document_id
    evidence = json.loads((root / "evaluation/evidence_review.json").read_text())["evidence"]
    by_id = {e["evidence_id"]: e for e in evidence}
    assert len(by_id) == len(evidence)
    for item in evidence:
        reader = readers[item["document_id"]]
        number = item["pdf_page_number"]
        assert 1 <= number <= len(reader.pages), item["evidence_id"]
        text = normalized(reader.pages[number - 1].extract_text() or "")
        assert normalized(item["anchor"]) in text, item["evidence_id"]
        assert item["printed_page_label"], item["evidence_id"]
        # Printed labels were visually checked, not inferred from PDF metadata.
    questions = json.loads((root / "evaluation/dev_questions.json").read_text())["questions"]
    assert len(questions) == len({q["question_id"] for q in questions}) == 10
    for question in questions:
        assert question["expected_answer_points"]
        assert all(e in by_id for e in question["evidence_ids"]), question["question_id"]
        if len(question["report_years"]) == 2 and question["expected_behavior"].startswith("compare"):
            years = {sources[by_id[e]["document_id"]]["report_year"] for e in question["evidence_ids"]}
            assert set(question["report_years"]).issubset(years), question["question_id"]
    return {"source_hashes_verified": len(sources), "evidence_records_verified": len(evidence),
            "development_questions_verified": len(questions), "held_out_test_questions": 0,
            "note": "Integrity checks pass; no RAG model or quality evaluation has run. User review of development answers is pending."}


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    print(json.dumps(verify(root), indent=2))
