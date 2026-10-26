# Banking Reports & Digital Strategy RAG Assistant

A Python project for querying annual reports with verifiable evidence and comparing digital strategy disclosures across reporting years. Initial case study: JPMorganChase / Chase.

**Status:** Phase 1 source preparation. No RAG model, search index, API or user interface has been built yet. This repository is independent of the Unity dissertation project.

## Scope

- Official JPMorganChase annual reports for reporting years 2024 and 2025.
- Group technology/AI/risk disclosures and Chase consumer banking material.
- Distinguish JPMorganChase group, US Consumer & Community Banking, and Chase UK / International Consumer Banking. Unknown scope stays unknown.
- Treat reporting year, publication date and the period of a quoted metric as separate information.
- English questions and answers first; source document, PDF page and supporting passage accompany factual answers in the planned application.

## Phase 1 setup

Python 3.11 or newer is sufficient for the current source-preparation scripts. Later model and service dependencies will be selected after a small hardware benchmark.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-phase1.txt
python scripts/prepare_sources.py --download
python scripts/audit_sources.py
python scripts/verify_phase1.py
```

`prepare_sources.py --download` downloads a report only when its PDF is missing. It records source URLs, retrieval timestamps, file sizes, page counts and SHA-256 hashes. Re-running it checks the existing snapshot instead of silently replacing documents. Deleting a PDF and downloading it again is still checked against its recorded hash.

`audit_sources.py` extracts page-level text and creates keyword/page candidates. It does not perform final reading-order reconstruction, chunking, embedding, retrieval or answer generation. Printed page labels in general extraction remain unverified; reviewed evidence pages are recorded separately.

`verify_phase1.py` checks the downloaded hashes and reviewed evidence references. These are source and project-integrity checks, not model-quality scores.

## Files

- `data/source_manifest.json`: exact local source snapshot and official URLs.
- `data/raw/`: original PDFs, excluded from Git.
- `data/processed/`: generated text/audits, excluded from Git.
- `evaluation/dev_questions.json`: the initial development questions and their reviewed evidence. Never ingest evaluation answers into a future RAG index.
- `evaluation/evidence_review.json`: reviewed page references, text anchors and review notes for this source snapshot.
- `docs/PROJECT_PLAN.md`: development plan, architecture and later evaluation scope.
- `docs/PHASE1_STATUS.md`: what has been completed, environment findings and next steps.
- `docs/FIRST_10_QUESTIONS.md`: Chinese guide to the initial development questions.
- `scripts/`: reproducible source preparation and verification.

## Planned sequence

1. Source scope, exact report versions and initial evidence questions.
2. Reliable extraction, section-aware chunks and scope metadata.
3. Dense retrieval and cited answer baseline.
4. Fixed development/test split and evaluation.
5. BM25/RRF and reranking comparison.
6. FastAPI, Streamlit, testing, Docker/CI and demo.

LoRA and complex financial-table reasoning are later experiments, dependent on a measured need.

## References and source handling

Architecture reference: [choeyunbeom/arxiv_rag_system](https://github.com/choeyunbeom/arxiv_rag_system). This Phase 1 implementation was written for this project; no source code from that repository has been copied.

Annual reports remain their respective owner's material. Raw PDFs and generated full-text exports are kept outside Git tracking; official download URLs and local preparation scripts are provided. This is an independent learning/portfolio project.
