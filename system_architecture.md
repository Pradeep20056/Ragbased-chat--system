# System Architecture: AI Tender Evaluator

This document outlines the technical architecture, data flow, and component interaction for the AI-based Tender Evaluation Engine.

## Overview

The system is a high-performance RAG (Retrieval-Augmented Generation) pipeline designed to analyze complex bidder offers (500+ page PDFs) and generate structured, audit-ready evaluation results. It is built as a **fully local architecture** to ensure maximum data privacy, leveraging local embeddings and local LLM reasoning.

## Component Diagram

```mermaid
graph TD
    subgraph "On-Premise Infrastructure"
        A[Bidder Offer ZIP] --> B[Extraction & Ingestion Script]
        B -->|PDF Extraction| C[PyMuPDF / docling]
        C -->|Text Chunks| D[Recursive Character Splitter]
        D -->|Embedding Query| E[Ollama: nomic-embed-text]
        E -->|Vector Store| F[(PostgreSQL + pgvector)]
    end

    subgraph "Evaluation Logic (On-Prem)"
        G[User Query] -->|Similarity Search| F
        F -->|Top-K Context| H[Evaluation Engine]
        H -->|Context + Prompt| I[Ollama Reasoning: Phi]
        I -->|Structured JSON| K[PQ Evaluation JSON Result]
    end
```

## Technical Components

### 1. Ingestion & Vector Storage
- **PDF Extraction**: Uses `PyMuPDF` (fitz) for lightweight and fast text extraction. Support for `docling` is included for advanced OCR tasks.
- **Embedding Model**: `nomic-embed-text` running locally on **Ollama**. This ensures that raw text never leaves the local environment for vectorization.
- **Vector Database**: **PostgreSQL 16** with the `pgvector` extension, running via Docker on host port **5444**.
- **Chunking Strategy**: Recursive character splitting with a chunk size of 1000 characters and 200-character overlap to preserve semantic context across page boundaries.

### 2. Reasoning & Evaluation
- **Orchestration**: Python-based engine using `LangChain` primitives for retrieval and prompt management.
- **LLM Engine**: **Ollama (Phi)** running locally. This ensures that the reasoning process and structured evaluation generation also occur within the private local environment.
- **Structured Output**: **Pydantic** models enforce a strict JSON schema (`PQEvaluationResult`) for the LLM response, ensuring machine-readability for integration with local TMS.

### 3. Data Flow
1. **Extraction**: The ZIP file is unpacked; all PDFs are parsed into raw text.
2. **Indexing**: Text is chunked, embedded via Ollama, and metadata (bidder name, source page) is stored in pgvector.
3. **Retrieval**: User queries are embedded and compared against the vector store using cosine similarity to find the most relevant document sections.
4. **Augmentation**: The reasoning engine (Gemini) receives the user query along with the top retrieved chunks.
5. **Generation**: Gemini generates a structured evaluation covering technical deviations, risks, and final recommendations.

## Security & Privacy
- **Data residency**: All data, including raw text, embeddings, and reasoning context, stays on the organization's local infrastructure.
- **No Cloud Dependency**: By moving to a local LLM (Ollama Phi), the system eliminates data transfer to third-party cloud providers, significantly enhancing security.
- **Authentication**: Vector store and local APIs are secured within the host network.

## Setup Requirements
- **Docker**: For running the pgvector container.
- **Ollama**: For running local embeddings (`nomic-embed-text`) and local reasoning (`phi`).
- **Python 3.14+**: Current runtime environment.
