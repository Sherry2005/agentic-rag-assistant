#!/usr/bin/env python3
"""Ingest a PDF into page-aware chunks, keeping each table in one piece.

Usage:
    python ingest.py data/raw/52868.pdf --out data/chunks_52868.jsonl

Requires: poppler-utils (pdftotext) and pypdf.

Each output line is one chunk:
    {"id", "source_doc", "pdf_page", "printed_page", "section",
     "chunk_type": "text" | "table", "table_id", "text"}

Why this exists (tested on NREL/TP-6A20-52868):
  * `pdftotext -layout` keeps table rows intact and column-aligned.
    pdfplumber's default extract_tables() fragments these tables into
    many empty/merged sub-tables, so it is NOT used here.
  * Printed page numbers differ from PDF page indexes (roman numerals in
    the front matter, then body page 1 = PDF page 10), so we read them
    from each page's footer. Golden-set `page` fields use printed numbers.
  * A table is kept as ONE chunk with its caption, source and notes, so
    retrieval cannot return half a table.
"""
import argparse
import json
import re
import subprocess
import textwrap
from pathlib import Path

from pypdf import PdfReader

LABEL_RE = re.compile(r"^(?:[ivxl]+|\d{1,3})$", re.I)
TABLE_CAPTION = re.compile(r"^\s*Table\s+(\d+)\.\s+\S")
NOTE_START = re.compile(r"^\s*(Source|Sources|Note|\*|\d+\s+[A-Z])")
HEADING = re.compile(r"^\s*(\d+(?:\.\d+)?)\s{1,3}([A-Z][^\n]{3,70})$")
FRONT_LABELS = {1: "cover", 2: "title", 3: "notice"}
MAX_CHARS = 900


def printed_labels(pdf_path: Path) -> dict[int, str]:
    """Map pdf page index (1-based) -> printed page label (footer number)."""
    labels = {}
    for i, page in enumerate(PdfReader(str(pdf_path)).pages, 1):
        lines = [l.strip() for l in (page.extract_text() or "").splitlines() if l.strip()]
        label = None
        for cand in lines[-1:] + lines[:1]:  # footer first, then header
            if LABEL_RE.match(cand):
                label = cand.lower()
                break
        labels[i] = label or FRONT_LABELS.get(i, f"pdf{i}")
    return labels



def page_texts(pdf_path: Path) -> list[str]:
    """Layout-preserving text, one string per page."""
    result = subprocess.run(
        ["pdftotext", "-layout", str(pdf_path), "-"],
        check=True,
        capture_output=True,
    )
    out = result.stdout.decode("utf-8", errors="replace")
    pages = out.split("\f")
    return pages[:-1] if pages and not pages[-1].strip() else pages


def split_tables(lines: list[str]):
    """Yield ('table', table_id, [lines]) and ('text', None, [lines]) blocks."""
    i, buf = 0, []
    while i < len(lines):
        m = TABLE_CAPTION.match(lines[i])
        if not m:
            buf.append(lines[i])
            i += 1
            continue
        if buf:
            yield "text", None, buf
            buf = []
        table_id, block, in_notes = m.group(1), [lines[i]], False
        i += 1
        while i < len(lines):
            line = lines[i]
            if NOTE_START.match(line):
                in_notes = True
            if in_notes and not line.strip():
                nxt = next((l for l in lines[i + 1:] if l.strip()), "")
                if not NOTE_START.match(nxt):
                    break  # notes block finished
            block.append(line)
            i += 1
        yield "table", table_id, block
    if buf:
        yield "text", None, buf


def paragraphs(lines: list[str]) -> list[str]:
    paras, cur = [], []
    for line in lines + [""]:
        if line.strip():
            cur.append(line.strip())
        elif cur:
            paras.append(re.sub(r"\s+", " ", " ".join(cur)))
            cur = []
    return paras


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    labels = printed_labels(args.pdf)
    section, n, chunks = "front matter", 0, []

    def emit(page_no, ctype, text, table_id=None):
        nonlocal n
        n += 1
        chunks.append({
            "id": f"{args.pdf.stem}-{n:04d}",
            "source_doc": args.pdf.name,
            "pdf_page": page_no,
            "printed_page": labels[page_no],
            "section": section,
            "chunk_type": ctype,
            "table_id": table_id,
            "text": text,
        })

    for page_no, raw in enumerate(page_texts(args.pdf), 1):
        for kind, table_id, block in split_tables(raw.splitlines()):
            if kind == "table":
                text = textwrap.dedent("\n".join(block)).strip("\n")
                emit(page_no, "table", text, table_id)
                continue
            for line in block:
                m = HEADING.match(line)
                if (
                    m
                    and not line.rstrip().endswith((".", ","))
                    and "Port Royal Road" not in line
                    and "Cole Boulevard" not in line
                ):
                    section = f"{m.group(1)} {m.group(2).strip()}"                    

            buf = ""
            for para in paragraphs(block):
                if buf and len(buf) + len(para) > MAX_CHARS:
                    emit(page_no, "text", buf)
                    buf = ""
                buf = f"{buf} {para}".strip()
        if buf:
            emit(page_no, "text", buf)

    args.out.parent.mkdir(parents=True, exist_ok=True)

    with args.out.open("w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    tables = sum(c["chunk_type"] == "table" for c in chunks)
    print(f"{len(chunks)} chunks ({tables} table chunks) -> {args.out}")


if __name__ == "__main__":
    main()