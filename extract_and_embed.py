import os
import argparse
import zipfile
import tempfile
import logging
from pathlib import Path

# Langchain imports
from langchain_ollama import OllamaEmbeddings
from langchain_postgres import PGVector
from langchain_text_splitters import RecursiveCharacterTextSplitter
import fitz  # PyMuPDF
from langchain_core.documents import Document
import pandas as pd

# OCR dependencies (pytesseract + Pillow)
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

# ── Logging ──────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ── Database configuration ────────────────────────────────────────
CONNECTION_STRING = "postgresql+psycopg://admin:password@localhost:5444/tender_eval"
COLLECTION_NAME   = "bidder_documents"

# DPI for rendering image pages — 200 is fast, 300 is more accurate for dense text
OCR_DPI = 250


def _ocr_page(page) -> str:
    """Render a single PyMuPDF page to an image and run Tesseract OCR on it."""
    if not TESSERACT_AVAILABLE:
        return ""
    try:
        mat = fitz.Matrix(OCR_DPI / 72, OCR_DPI / 72)   # scale to DPI
        pix = page.get_pixmap(matrix=mat, colorspace=fitz.csGRAY)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        return pytesseract.image_to_string(img, lang="eng")
    except Exception as e:
        logger.warning(f"   Tesseract OCR failed on page: {e}")
        return ""


def extract_text(file_path: str) -> str:
    """
    Extract text from a PDF with a smart page-level strategy:
      1. Try PyMuPDF get_text() — instant for text-native PDFs.
      2. If a page returns 0 chars but contains images → run Tesseract OCR.
    This keeps text PDFs fast while correctly reading scanned pages.
    """
    logger.info(f"Extracting text: {file_path}")
    text        = ""
    ocr_pages   = 0
    text_pages  = 0

    try:
        with fitz.open(file_path) as doc:
            total_pages = len(doc)
            for page_num, page in enumerate(doc, start=1):
                native = page.get_text().strip()
                if native:
                    text       += native + "\n"
                    text_pages += 1
                elif page.get_images():
                    # Scanned page — fall back to Tesseract
                    ocr_text = _ocr_page(page)
                    if ocr_text.strip():
                        text     += ocr_text + "\n"
                    ocr_pages += 1
                    if ocr_pages == 1:
                        logger.info(f"   Page {page_num}/{total_pages}: scanned — using Tesseract OCR")

        logger.info(
            f"   Extraction complete: {text_pages} native-text pages, "
            f"{ocr_pages} OCR pages, {len(text):,} total chars"
        )
    except Exception as e:
        logger.error(f"Extraction failed for {file_path}: {e}")

    return text


def extract_excel(file_path: str) -> str:
    """Extract content from Excel files and convert to text representation."""
    logger.info(f"Extracting Excel data: {file_path}")
    text = ""
    try:
        with pd.ExcelFile(file_path) as xl:
            for sheet_name in xl.sheet_names:
                df = xl.parse(sheet_name)
                if not df.empty:
                    text += f"\nSheet: {sheet_name}\n"
                    text += df.to_csv(index=False, sep="\t")
    except Exception as e:
        logger.error(f"Excel extraction failed for {file_path}: {e}")
    return text


def process_input(path: str):
    """Process either a zip file or a directory."""
    if os.path.isdir(path):
        logger.info(f"Processing directory: {path}")
        return process_directory(path, Path(path).stem)
    elif zipfile.is_zipfile(path):
        logger.info(f"Extracting and processing zip: {path}")
        with tempfile.TemporaryDirectory() as temp_dir:
            with zipfile.ZipFile(path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            return process_directory(temp_dir, Path(path).stem)
    else:
        logger.error(f"Unsupported file type: {path}")
        return []


def process_directory(directory: str, bidder_name: str):
    """Process all supported documents in a directory."""
    extracted_docs = []
    for root, dirs, files in os.walk(directory):
        for file in sorted(files):
            file_path = os.path.join(root, file)
            if file.lower().endswith('.pdf'):
                logger.info(f"Processing PDF: {file}")
                text_content = extract_text(file_path)
            elif file.lower().endswith(('.xlsx', '.xls')):
                logger.info(f"Processing Excel: {file}")
                text_content = extract_excel(file_path)
            else:
                continue

            if text_content.strip():
                doc = Document(
                    page_content=text_content,
                    metadata={"bidder": bidder_name, "source": file}
                )
                extracted_docs.append(doc)
            else:
                logger.warning(f"   ⚠ No text extracted from {file} — skipping.")

    return extracted_docs


def embed_and_store(documents: list, clear_existing: bool = True, batch_size: int = 20):
    """
    Chunk documents and store embeddings in PostgreSQL / PGVector.
    Embeds in small batches to avoid Ollama HTTP timeouts on large document sets.
    """
    if not documents:
        logger.warning("No documents to process.")
        return

    logger.info("Splitting text into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_documents(documents)
    total = len(chunks)
    logger.info(f"Total chunks to embed: {total}  (batch size: {batch_size})")

    embeddings = OllamaEmbeddings(
        model="nomic-embed-text",
        keep_alive=600,   # keep model loaded for 10 min across batches
    )

    # ── Create / clear the collection with the first batch ───────
    first_batch = chunks[:batch_size]
    rest        = chunks[batch_size:]

    logger.info(f"Initialising vector store (batch 1/{-(-total // batch_size)})...")
    vectorstore = PGVector.from_documents(
        embedding=embeddings,
        documents=first_batch,
        collection_name=COLLECTION_NAME,
        connection=CONNECTION_STRING,
        pre_delete_collection=clear_existing,
    )
    logger.info(f"  ✓ Batch 1 — {len(first_batch)} chunks stored.")

    # ── Add remaining batches ─────────────────────────────────────
    for batch_num, start in enumerate(range(0, len(rest), batch_size), start=2):
        batch = rest[start: start + batch_size]
        n_batches = -(-total // batch_size)
        attempts = 0
        while attempts < 3:
            try:
                vectorstore.add_documents(batch)
                logger.info(f"  ✓ Batch {batch_num}/{n_batches} — {len(batch)} chunks stored.")
                break
            except Exception as exc:
                attempts += 1
                logger.warning(f"  ⚠ Batch {batch_num} attempt {attempts} failed: {exc}")
                if attempts == 3:
                    logger.error(f"  ❌ Batch {batch_num} failed after 3 attempts — skipping.")

    logger.info(f"✅ Done — {total} chunks stored in vector DB.")



if __name__ == "__main__":
    if not TESSERACT_AVAILABLE:
        logger.warning(
            "pytesseract / Pillow not found — scanned PDFs will produce 0 text.\n"
            "Install with:  pip install pytesseract Pillow\n"
            "Also install Tesseract engine: https://github.com/UB-Mannheim/tesseract/wiki"
        )

    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="Path to zip file or directory")
    parser.add_argument("--append", action="store_true",
                        help="Append to existing collection instead of clearing it")
    args = parser.parse_args()

    docs = process_input(args.path)
    embed_and_store(docs, clear_existing=not args.append)
