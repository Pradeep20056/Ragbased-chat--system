# AI Tender Evaluator

A high-performance RAG (Retrieval-Augmented Generation) pipeline designed to analyze complex bidder offers and generate structured, audit-ready evaluation results. The system uses local infrastructure for secure data processing and cloud-based reasoning via Gemini for advanced interpretation.

## 🚀 Key Features
- **Local Embeddings**: Sensitive data stays local using Ollama and PostgreSQL.
- **Advanced Reasoning**: Leverages Gemini 3 Flash for deep technical analysis.
- **Audit-Ready Output**: Enforced JSON schema for structured, machine-readable results.

---

## 🛠 Prerequisites

Ensure you have the following installed on your system:
- **Python 3.14+**
- **Docker & Docker Compose** (for vector storage)
- **Ollama** (for local embedding generation)
- **Google Cloud Account** (for Gemini API access)

---

## ⚙️ Setup & Installation

### 1. Initialize Python Environment
```powershell
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
.\venv\Scripts\activate
```

### 2. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 3. Start Infrastructure (Docker)
Ensure Docker Desktop is running, then start the pgvector database:
```powershell
docker-compose up -d
```
*The database will be available at `localhost:5444`.*

### 4. Setup Local Embeddings (Ollama)
Download the required embedding model:
```powershell
ollama pull nomic-embed-text
```

### 5. Configure Environment Variables
Create a `.env` file in the root directory (refer to `.env.example` if available) and provide your credentials:
```env
GEMINI_API_KEY=your_gemini_api_key
GOOGLE_CLOUD_PROJECT=your_project_id
GOOGLE_CLOUD_LOCATION=global
```

---

## 🏃 Running the System

### Step 1: Document Ingestion
Process a bidder's offer (ZIP file containing PDFs) into the vector store:
```powershell
python extract_and_embed.py "Path\To\Bidder_Offer.zip"
```

### Step 2: Run Evaluation
Execute the AI evaluation engine to analyze the ingested documents:
```powershell
python evaluate_bid.py
```
*The results will be printed to the console in structured JSON format.*

---

## 🏗 System Architecture
For a deep dive into the technical design, refer to the [System Architecture](system_architecture.md) document.

## 📄 License
Internal Use Only.
