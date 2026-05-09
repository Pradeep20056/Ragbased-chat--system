"""
inspect_ocr.py
──────────────
Diagnostic tool: extracts text from every PDF/Excel in a bidder zip or folder
and writes the raw OCR content + chunks to a readable folder structure.

Uses the EXACT same extraction logic as extract_and_embed.py so what you see
here is precisely what gets embedded in the vector DB.

Usage:
    python inspect_ocr.py "Bidder2 offer.zip"
    python inspect_ocr.py path/to/bidder/folder
    python inspect_ocr.py "Bidder2 offer.zip" --chunk-size 1000 --chunk-overlap 200

Output layout:
    ocr_inspection/
    └── Bidder2offer/
        ├── _summary.txt                  ← overview of all files + stats
        ├── 01_filename.pdf_raw.txt       ← full raw OCR text (page-by-page)
        ├── 01_filename.pdf_chunks.txt    ← every chunk (numbered, with metadata)
        ├── 02_anotherfile.xlsx_raw.txt
        ├── 02_anotherfile.xlsx_chunks.txt
        └── ...
"""

import os
import argparse
import zipfile
import tempfile
import logging
import shutil
from pathlib import Path
from datetime import datetime

import fitz  # PyMuPDF
import pandas as pd
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

# OCR dependencies (same as extract_and_embed.py)
try:
    import pytesseract
    from PIL import Image
    import io
    # Windows: point explicitly to Tesseract binary (often not on PATH)
    import platform as _platform, os as _os
    if _platform.system() == "Windows":
        _win_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        if _os.path.exists(_win_path):
            pytesseract.pytesseract.tesseract_cmd = _win_path
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

# ── Logging ─────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# ── Defaults (match extract_and_embed.py exactly) ────────────────
DEFAULT_CHUNK_SIZE    = 1000
DEFAULT_CHUNK_OVERLAP = 200
OCR_DPI               = 250
OUTPUT_ROOT           = Path("ocr_inspection")


# ── OCR helper ───────────────────────────────────────────────────

def _ocr_page(page) -> str:
    """Render a PyMuPDF page to an image and run Tesseract on it."""
    if not TESSERACT_AVAILABLE:
        return ""
    try:
        mat = fitz.Matrix(OCR_DPI / 72, OCR_DPI / 72)
        pix = page.get_pixmap(matrix=mat, colorspace=fitz.csGRAY)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        return pytesseract.image_to_string(img, lang="eng")
    except Exception as e:
        logger.warning(f"   Tesseract OCR failed on page: {e}")
        return ""


# ── Text extractors (identical strategy to extract_and_embed.py) ─

def extract_text_pdf(file_path: str) -> tuple[str, int, int]:
    """
    Extract text from a PDF with per-page smart fallback:
      - Native get_text() first (fast).
      - If page is blank but has images → Tesseract OCR.
    Returns (full_text, native_page_count, ocr_page_count).
    """
    text       = ""
    text_pages = 0
    ocr_pages  = 0
    page_log   = []   # for the raw file header

    try:
        with fitz.open(file_path) as doc:
            total = len(doc)
            for page_num, page in enumerate(doc, start=1):
                native = page.get_text().strip()
                if native:
                    text       += f"\n{'─'*60}\n[PAGE {page_num} — native text]\n{'─'*60}\n"
                    text       += native + "\n"
                    text_pages += 1
                    page_log.append(f"  Page {page_num:>3}/{total}: native text ({len(native):,} chars)")
                elif page.get_images():
                    ocr_text = _ocr_page(page)
                    stripped  = ocr_text.strip()
                    if stripped:
                        text += f"\n{'─'*60}\n[PAGE {page_num} — Tesseract OCR]\n{'─'*60}\n"
                        text += ocr_text + "\n"
                    ocr_pages += 1
                    page_log.append(
                        f"  Page {page_num:>3}/{total}: OCR ({len(stripped):,} chars)"
                        + ("" if stripped else "  ← BLANK after OCR")
                    )
                else:
                    page_log.append(f"  Page {page_num:>3}/{total}: empty (no text, no images)")
    except Exception as e:
        logger.error(f"Extraction failed for {file_path}: {e}")
        text = f"[ERROR] {e}"

    return text, text_pages, ocr_pages, page_log


def extract_text_excel(file_path: str) -> str:
    """Extract content from Excel files (same as pipeline)."""
    text = ""
    try:
        with pd.ExcelFile(file_path) as xl:
            for sheet_name in xl.sheet_names:
                df = xl.parse(sheet_name)
                if not df.empty:
                    text += f"\nSheet: {sheet_name}\n"
                    text += df.to_csv(index=False, sep="\t")
                else:
                    text += f"\nSheet: {sheet_name} — [EMPTY]\n"
    except Exception as e:
        logger.error(f"Excel extraction failed for {file_path}: {e}")
        text = f"[ERROR] Excel extraction failed: {e}"
    return text


# ── Safe filename helper ─────────────────────────────────────────

def safe_name(name: str, index: int, max_len: int = 60) -> str:
    """Turn a filename into a safe prefix for output files."""
    clean = "".join(c if c.isalnum() or c in "._- " else "_" for c in name)
    clean = clean.replace(" ", "_")
    prefix = f"{index:02d}_{clean}"
    return prefix[:max_len]


# ── Main inspection logic ────────────────────────────────────────

def inspect_directory(directory: str, bidder_label: str, chunk_size: int, chunk_overlap: int):
    """Walk a directory, extract all PDFs/Excel, write inspection files."""

    out_dir = OUTPUT_ROOT / bidder_label
    out_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory: {out_dir.resolve()}")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    summary_lines = [
        f"OCR Inspection Report",
        f"=====================",
        f"Bidder     : {bidder_label}",
        f"Source dir : {directory}",
        f"Chunk size : {chunk_size}  |  Overlap: {chunk_overlap}",
        f"Generated  : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"",
        f"{'─'*70}",
        f"{'#':<4} {'File':<50} {'Raw chars':>10} {'Chunks':>7} {'Status'}",
        f"{'─'*70}",
    ]

    file_index = 0
    total_chars  = 0
    total_chunks = 0
    errors       = []

    for root, dirs, files in os.walk(directory):
        # Sort so output is predictable
        for file in sorted(files):
            file_path   = os.path.join(root, file)
            file_lower  = file.lower()

            if file_lower.endswith(".pdf"):
                file_index += 1
                logger.info(f"[{file_index}] PDF  → {file}")
                raw_text, native_pg, ocr_pg, page_log = extract_text_pdf(file_path)
                file_type   = "PDF"
                extra_header = (
                    f"NATIVE PAGES : {native_pg}\n"
                    f"OCR PAGES    : {ocr_pg}\n"
                    f"PAGE DETAIL  :\n" + "\n".join(page_log) + "\n"
                )

            elif file_lower.endswith((".xlsx", ".xls")):
                file_index += 1
                logger.info(f"[{file_index}] XLSX → {file}")
                raw_text    = extract_text_excel(file_path)
                file_type   = "EXCEL"
                extra_header = ""

            else:
                continue  # skip non-supported files

            # ── Determine status ──
            char_count = len(raw_text.strip())
            status = "OK" if char_count > 50 else "⚠ EMPTY / VERY SHORT"
            if "[ERROR]" in raw_text:
                status = "❌ EXTRACTION ERROR"
                errors.append(file)

            # ── Write raw text ──
            prefix   = safe_name(file, file_index)
            raw_path = out_dir / f"{prefix}_raw.txt"
            raw_path.write_text(
                f"FILE     : {file}\n"
                f"TYPE     : {file_type}\n"
                f"PATH     : {file_path}\n"
                f"CHARS    : {char_count:,}\n"
                f"STATUS   : {status}\n"
                + extra_header
                + f"{'='*70}\n\n"
                + raw_text,
                encoding="utf-8",
                errors="replace",
            )

            # ── Create Document and chunk ──
            doc = Document(
                page_content=raw_text,
                metadata={"bidder": bidder_label, "source": file},
            )
            chunks = splitter.split_documents([doc])
            total_chunks += len(chunks)

            # ── Write chunks file ──
            chunks_path = out_dir / f"{prefix}_chunks.txt"
            chunk_lines = [
                f"FILE     : {file}",
                f"TYPE     : {file_type}",
                f"TOTAL CHUNKS: {len(chunks)}",
                f"CHUNK SIZE  : {chunk_size}  |  OVERLAP: {chunk_overlap}",
                f"{'='*70}",
                "",
            ]
            for i, chunk in enumerate(chunks, start=1):
                chunk_lines.append(f"{'─'*70}")
                chunk_lines.append(f"CHUNK {i:03d} / {len(chunks):03d}   |   chars: {len(chunk.page_content):,}")
                chunk_lines.append(f"{'─'*70}")
                chunk_lines.append(chunk.page_content)
                chunk_lines.append("")

            chunks_path.write_text(
                "\n".join(chunk_lines),
                encoding="utf-8",
                errors="replace",
            )

            total_chars += char_count
            summary_lines.append(
                f"{file_index:<4} {file:<50} {char_count:>10,} {len(chunks):>7}  {status}"
            )
            logger.info(f"     → {char_count:,} chars | {len(chunks)} chunks | {status}")

    # ── Write summary ──
    summary_lines += [
        f"{'─'*70}",
        f"{'TOTAL':<4} {'':<50} {total_chars:>10,} {total_chunks:>7}",
        f"{'─'*70}",
        "",
        f"Files processed : {file_index}",
        f"Total chars     : {total_chars:,}",
        f"Total chunks    : {total_chunks}",
    ]
    if errors:
        summary_lines += ["", "⚠  FILES WITH ERRORS:"]
        for e in errors:
            summary_lines.append(f"   - {e}")
    else:
        summary_lines.append("")
        summary_lines.append("✅ No extraction errors detected.")

    summary_path = out_dir / "_summary.txt"
    summary_path.write_text("\n".join(summary_lines), encoding="utf-8")
    logger.info(f"\n{'='*60}")
    logger.info(f"Inspection complete.")
    logger.info(f"  Files found   : {file_index}")
    logger.info(f"  Total chars   : {total_chars:,}")
    logger.info(f"  Total chunks  : {total_chunks}")
    logger.info(f"  Output folder : {out_dir.resolve()}")
    logger.info(f"  Summary file  : {summary_path.resolve()}")
    logger.info(f"{'='*60}")

    return file_index, total_chars, total_chunks


def inspect(path: str, chunk_size: int, chunk_overlap: int):
    """Entry point: handles zip or directory input."""
    p = Path(path)

    if not p.exists():
        logger.error(f"Path not found: {path}")
        return

    # Build a clean label for the output subfolder
    bidder_label = "".join(c for c in p.stem if c.isalnum() or c in "_-")

    if p.is_dir():
        logger.info(f"Processing directory: {path}")
        inspect_directory(str(p), bidder_label, chunk_size, chunk_overlap)

    elif zipfile.is_zipfile(path):
        logger.info(f"Extracting zip: {path}")
        tmp = tempfile.mkdtemp(prefix="ocr_inspect_")
        try:
            with zipfile.ZipFile(path, "r") as zf:
                zf.extractall(tmp)
            inspect_directory(tmp, bidder_label, chunk_size, chunk_overlap)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    else:
        logger.error(f"Unsupported input — must be a .zip file or a directory: {path}")


# ── CLI ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    if not TESSERACT_AVAILABLE:
        logger.warning(
            "pytesseract / Pillow not installed — scanned PDFs will show 0 chars.\n"
            "  pip install pytesseract Pillow\n"
            "  Then install Tesseract engine: https://github.com/UB-Mannheim/tesseract/wiki"
        )
    else:
        logger.info("✅ Tesseract available — scanned pages will be OCR'd.")

    parser = argparse.ArgumentParser(
        description="Inspect OCR output and chunks for a bidder zip/folder."
    )
    parser.add_argument(
        "path",
        help="Path to a bidder .zip file or directory",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=DEFAULT_CHUNK_SIZE,
        help=f"Chunk size (default: {DEFAULT_CHUNK_SIZE})",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=DEFAULT_CHUNK_OVERLAP,
        help=f"Chunk overlap (default: {DEFAULT_CHUNK_OVERLAP})",
    )
    args = parser.parse_args()
    inspect(args.path, args.chunk_size, args.chunk_overlap)
