import os
import argparse
import zipfile
import tempfile
import logging
from pathlib import Path

# Langchain imports (v2 native preferred)
from langchain_ollama import OllamaEmbeddings
from langchain_postgres import PGVector
from langchain_text_splitters import RecursiveCharacterTextSplitter
import fitz  # PyMuPDF
from langchain_core.documents import Document
import pandas as pd

# Docling for OCR
try:
    from docling.document_converter import DocumentConverter
    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False
    import fitz  # PyMuPDF fallback

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database configuration
CONNECTION_STRING = "postgresql+psycopg://admin:password@localhost:5444/tender_eval"
COLLECTION_NAME = "bidder_documents"

def extract_text_per_page(file_path):
    """Extract text per page from a PDF using PyMuPDF. Returns list of (page_num, text) tuples."""
    logger.info(f"Extracting text with PyMuPDF (per-page): {file_path}")
    pages = []
    try:
        with fitz.open(file_path) as doc:
            for page_num, page in enumerate(doc, start=1):
                text = page.get_text().strip()
                if text:
                    pages.append((page_num, text))
    except Exception as e:
        logger.error(f"PyMuPDF failed for {file_path}: {e}")
    return pages

def extract_excel(file_path):
    """Extract content from Excel files and convert to text representation."""
    logger.info(f"Extracting Excel data: {file_path}")
    text = ""
    try:
        # Read all sheets
        with pd.ExcelFile(file_path) as xl:
            for sheet_name in xl.sheet_names:
                df = xl.parse(sheet_name)
                if not df.empty:
                    text += f"\nSheet: {sheet_name}\n"
                    # Convert sheet content to string (CSV-like format for LLM to understand rows)
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
    """Process documents in a directory."""
    extracted_docs = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)

            if file.lower().endswith('.pdf'):
                logger.info(f"Processing PDF: {file}")
                pages = extract_text_per_page(file_path)
                for page_num, page_text in pages:
                    doc = Document(
                        page_content=page_text,
                        metadata={
                            "bidder": bidder_name,
                            "source": file,
                            "page": page_num,
                        }
                    )
                    extracted_docs.append(doc)

            elif file.lower().endswith(('.xlsx', '.xls')):
                logger.info(f"Processing Excel: {file}")
                text_content = extract_excel(file_path)
                if text_content:
                    doc = Document(
                        page_content=text_content,
                        metadata={
                            "bidder": bidder_name,
                            "source": file,
                            "page": "N/A",
                        }
                    )
                    extracted_docs.append(doc)

    return extracted_docs

def embed_and_store(documents: list, clear_existing: bool = True):
    """Store chunks in PostgreSQL."""
    if not documents:
        logger.warning("No documents to process.")
        return
        
    logger.info("Splitting text...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=400)
    chunks = text_splitter.split_documents(documents)
    
    logger.info(f"Generating embeddings for {len(chunks)} chunks...")
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    
    PGVector.from_documents(
        embedding=embeddings,
        documents=chunks,
        collection_name=COLLECTION_NAME,
        connection=CONNECTION_STRING,
        pre_delete_collection=clear_existing
    )
    logger.info("Done.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="Path to zip file or directory")
    parser.add_argument("--append", action="store_true", help="Append to existing collection instead of clearing it")
    args = parser.parse_args()
    
    docs = process_input(args.path)
    embed_and_store(docs, clear_existing=not args.append)
