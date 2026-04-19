One-Page Diagram: LLM-Based Bid Evaluation Architecture
(THIS IS THE ONLY PART WE NEED TO DO IN THIS CODE BASE !)
BIDDER OFFER (500-page PDF) [On-Prem]
        │
        ▼
OCR PROCESSING (CPU)
• Converts scanned PDF to text
• Preserves page numbers & sections
        │
        ▼
TEXT CHUNKING
• Splits text into logical chunks (500–1000 tokens)
• Tags each chunk with bidder, page, clause
        │
        ▼
EMBEDDING MODEL (On-Prem)
(e.g., nomic-embed-text via Ollama)
• Converts text chunks into semantic vectors
        │
        ▼
POSTGRESQL + pgvector (On-Prem)
• Stores embedding vectors & text
• Performs semantic similarity search
        │
        │  User Query
        │  "Identify technical deviations and risks"
        ▼
QUESTION EMBEDDING (On-Prem)
• Converts user query to embedding vector
        │
        ▼
pgvector SIMILARITY SEARCH
• Returns Top-K relevant text chunks
        │
        ▼
LLM (Cloud – Temporary)
• Receives only retrieved text
• Performs reasoning & interpretation
• Generates structured JSON output
        │
        ▼
STRUCTURED JSON OUTPUT
• PQ Evaluation Results
• Audit-ready, machine-readable
        │
        ▼
EVALUATION SHEET / UI (Human Review)
• Final decision by officers
