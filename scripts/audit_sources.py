"""Inspect local reports for text coverage and candidate evidence pages. No model needed."""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import re
from pathlib import Path

from pypdf import PdfReader

logging.getLogger("pypdf").setLevel(logging.ERROR)
PATTERNS = {
    "chase_uk": r"Chase\s+(?:U\.?\s*K\.?|United Kingdom)",
    "icb": r"international\s+consumer",
    "ccb": r"consumer\s*(?:&|and)\s*community\s+banking",
    "cloud": r"cloud(?:[-\s]+native)?",
    "generative_ai": r"generative\s+(?:AI|artificial intelligence)",
    "artificial_intelligence": r"artificial\s+intelligence",
    "digital_customers": r"digitally\s+active|digital\s+engagement",
    "technology_risk": r"cybersecurity|technology\s+risk|operational\s+resilien",
}


def audit(root: Path) -> dict:
    manifest = json.loads((root / "data/source_manifest.json").read_text())
    output_dir = root / "data/processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    hits = []
    summaries = []
    with (output_dir / "pages.jsonl").open("w") as output:
        for source in manifest["sources"]:
            path = root / source["local_path"]
            if hashlib.sha256(path.read_bytes()).hexdigest() != source["sha256"]:
                raise ValueError(f"Source hash mismatch: {path}")
            reader = PdfReader(path)
            lengths = []
            for index, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                lengths.append(len(text.strip()))
                record = {
                    "document_id": source["document_id"],
                    "report_year": source["report_year"],
                    "source_url": source["source_url"],
                    "document_sha256": source["sha256"],
                    "pdf_page_index": index,
                    "pdf_page_number": index + 1,
                    "printed_page_label": None,
                    "printed_page_label_status": "Requires visual verification; do not assume PDF index equals printed page.",
                    "text": text,
                }
                output.write(json.dumps(record, ensure_ascii=False) + "\n")
                for topic, pattern in PATTERNS.items():
                    match = re.search(pattern, text, flags=re.IGNORECASE)
                    if match:
                        hits.append({
                            "document_id": source["document_id"],
                            "pdf_page_number": index + 1,
                            "topic": topic,
                            "preview": re.sub(r"\s+", " ", text[max(0, match.start()-160):match.end()+500]),
                        })
            summaries.append({
                "document_id": source["document_id"],
                "page_count": len(lengths),
                "pages_with_extractable_text": sum(n > 0 for n in lengths),
                "total_extracted_characters": sum(lengths),
                "short_text_pages": [i+1 for i,n in enumerate(lengths) if n < 100],
                "quality_note": "Text presence does not establish reading-order or table fidelity; selected pages require visual review.",
            })
    (output_dir / "keyword_hits.json").write_text(json.dumps(hits, indent=2, ensure_ascii=False) + "\n")
    (output_dir / "extraction_audit.json").write_text(json.dumps(summaries, indent=2) + "\n")
    print(json.dumps(summaries, ensure_ascii=False))
    print(f"Candidate topic/page hits: {len(hits)}")
    return {"summaries": summaries, "hits": hits}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    audit(parser.parse_args().root)

