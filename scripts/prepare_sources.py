"""Download the two official reports and record a reproducible local snapshot."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import ssl
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from pypdf import PdfReader

SOURCES = [
    {
        "document_id": f"jpmc_annual_report_{year}",
        "report_year": year,
        "title": f"JPMorgan Chase & Co. Annual Report {year}",
        "source_url": (
            "https://www.jpmorganchase.com/content/dam/jpmc/"
            "jpmorgan-chase-and-co/investor-relations/documents/"
            f"annualreport-{year}.pdf"
        ),
        "local_path": f"data/raw/jpmc_annual_report_{year}.pdf",
    }
    for year in (2024, 2025)
]


def sha256(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def create_tls_context() -> ssl.SSLContext:
    context = ssl.create_default_context()
    # Some python.org macOS installs lack their optional CA symlink.
    # Add the OS-provided trusted roots while retaining HTTPS verification.
    system_ca = Path("/etc/ssl/cert.pem")
    if sys.platform == "darwin" and system_ca.is_file():
        context.load_verify_locations(cafile=str(system_ca))
    return context


def prepare(root: Path, download: bool = False) -> list[dict]:
    manifest_path = root / "data/source_manifest.json"
    old_manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    old_by_id = {item["document_id"]: item for item in old_manifest.get("sources", [])}
    output = []
    for source in SOURCES:
        path = root / source["local_path"]
        old = old_by_id.get(source["document_id"], {})
        fetched_now = False
        if not path.exists():
            if not download:
                raise FileNotFoundError(f"Missing {path}. Run with --download.")
            path.parent.mkdir(parents=True, exist_ok=True)
            request = Request(source["source_url"], headers={"User-Agent": "BankingReportsRAG/0.1 (research project)"})
            temporary = None
            try:
                with urlopen(request, timeout=90, context=create_tls_context()) as response:
                    with tempfile.NamedTemporaryFile(dir=path.parent, suffix=".download", delete=False) as target:
                        temporary = Path(target.name)
                        shutil.copyfileobj(response, target)
                    final_url = response.geturl()
                    content_type = response.headers.get("Content-Type", "")
                with temporary.open("rb") as stream:
                    if stream.read(5) != b"%PDF-":
                        raise ValueError(f"Response is not a PDF: {source['source_url']}")
                temporary.replace(path)
                fetched_now = True
            finally:
                if temporary is not None:
                    temporary.unlink(missing_ok=True)
        digest = sha256(path)
        if old.get("sha256") and old["sha256"] != digest:
            raise ValueError(f"Snapshot hash mismatch for {path}; review the changed source before updating its manifest.")
        reader = PdfReader(path)
        item = {
            **source,
            "sha256": digest,
            "size_bytes": path.stat().st_size,
            "page_count": len(reader.pages),
            "publication_date": None,
            "publication_date_note": "Not independently verified for this PDF; not inferred from companion HTML.",
            "retrieved_at": datetime.now(ZoneInfo("Europe/London")).isoformat() if fetched_now else old.get("retrieved_at"),
            "final_url": final_url if fetched_now else old.get("final_url"),
            "content_type": content_type if fetched_now else old.get("content_type"),
        }
        output.append(item)
        print(f"{item['document_id']}: {item['page_count']} pages, {item['size_bytes']} bytes, SHA256 {digest[:12]}...")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps({"schema_version": 1, "sources": output}, indent=2) + "\n")
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--download", action="store_true", help="Fetch a report only if its local PDF is missing.")
    args = parser.parse_args()
    prepare(args.root, args.download)
