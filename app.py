"""
app.py
------
FastAPI demo server for the Tender Evaluation RAG system.
Exposes the workflow visually: retrieved chunks + LLM extraction.

Run with:
    .\\venv\\Scripts\\uvicorn app:app --reload --port 8000
"""

import json
import logging
import os
import re
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# ── DB / collection constants ─────────────────────────────────
CONNECTION_STRING = "postgresql+psycopg://admin:password@localhost:5444/tender_eval"
COLLECTION_NAME   = "bidder_documents"

# ── Copy of evaluation section definitions ────────────────────
EVALUATIONS = [
    {
        "id":     "a",
        "label":  "(a) PQC Exp. & Technical Evaluation (Contracts)",
        "search_query": "work order experience criteria technical qualification completion certificate executed value industry petroleum petrochemical",
        "instruction": """
You must fill EVERY field below from the bidder's submitted documents.

FIELDS TO EXTRACT:
1.1  similar_nature_of_job           → Nature of similar jobs the bidder has done (e.g., electrical, instrumentation).
1.2  value_of_work_order_required    → WO value submitted (1x/2x/3x format, in Rs. Lakhs).
1.3  details_of_work_order_submitted → Full details of the WO submitted.
1.4  work_order_number_and_date      → WO number and date.
1.5  nature_of_industry              → Industry type of WO issuer (Petroleum / Petrochemical / Refinery / Power).
1.6  name_of_issuer                  → Name of the company that issued the WO.
1.7  completion_certificate_details  → Details of completion certificate (cert number, date, from whom).
1.8  executed_value_as_per_completion_certificate → Executed value in Rs. Lakhs from completion certificate.
1.9  value_considered_for_technical_evaluation    → Value of order considered for TE (in Rs. Lakhs).
1.10 annualization_of_value          → Annualized value for ARC jobs, or "Not Applicable".
1.11 subcontract_approval_submitted  → Subcontract approval / end-user certificate: "Yes", "No", "Not Applicable".
1.12 work_order_meeting_experience_criteria → The specific WO that meets experience criteria.
2    additional_technical_pqc        → Any extra PQC requirements met or "None".
3    deviations                      → List of deviations from tender requirements (empty [] if nil).
4    query_to_be_raised              → List of queries/clarifications needed from the bidder.
5    technical_acceptance_status     → "Accepted", "Under Query", or "Rejected".
6    reason_for_rejection            → Reason if rejected, else "Not Applicable".

RULE: If a value is not found in the context, write "Not Found in Documents" — do NOT leave blank.
""",
    },
    {
        "id":     "b",
        "label":  "(b) PQC Fin. & Commercial Evaluation (Contracts)",
        "search_query": "annual turnover financial statements networth EPF ESI EMD formats submission MSE MII blacklisting commercial evaluation",
        "instruction": """
You must fill EVERY field below from the bidder's submitted documents.

FIELDS TO EXTRACT:
1   technical_qualification       → "Qualified", "Not Qualified", or "Under TE".
2   integrity_pact                → "Submitted (Page: X)", "Not Submitted", or "Not Applicable".
3   emd_applicable                → EMD amount and details, or "EMD exemption as MSE".
5a  annual_turnover_2021_22       → Turnover FY2021-22 in Rs. Lakhs.
5b  annual_turnover_2022_23       → Turnover FY2022-23 in Rs. Lakhs.
5c  annual_turnover_2023_24       → Turnover FY2023-24 in Rs. Lakhs.
6   networth                      → Net Worth. State "Positive" or "Negative".
7   epf_code_number               → EPF Code Number.
8   esi_code_number               → ESI Code Number.
12  mse_status                    → MSE details.
19  commercial_evaluation_status  → "Qualified", "Not Qualified", or "Under Query".

RULE: If a value is not found in the context, write "Not Found in Documents" — do NOT leave blank.
""",
    },
    {
        "id":     "c",
        "label":  "(c) Materials - PQ Experience Criteria",
        "search_query": "purchase order PO supply experience criteria GST invoice delivery challan commissioning proof of supply materials",
        "instruction": """
You must fill EVERY field below from the bidder's submitted documents.

FIELDS TO EXTRACT:
1a  po_item_description           → Description of the similar item in the Purchase Order.
1b  po_number                     → Purchase Order number.
1c  po_acceptable_date            → PO date.
1d  po_value                      → PO value in Rs. Lakhs.
1e  po_issuer_name                → Name of the organization that issued the PO.
1i  proof_of_supply               → Proof submitted: GST Invoices, Delivery Challans, or Completion Certificates.
    pqc_experience_status         → "Qualified", "Not Qualified", or "Query to be raised".

RULE: If a value is not found in the context, write "Not Found in Documents" — do NOT leave blank.
""",
    },
    {
        "id":     "d",
        "label":  "(d) Materials - PQ Financial Criteria",
        "search_query": "annual turnover balance sheet networth financial year 2021 2022 2023 2024 profit loss reserves capital",
        "instruction": """
You must fill EVERY field below from the bidder's submitted financial documents.

FIELDS TO EXTRACT:
1a  annual_turnover_2021_22       → Turnover FY2021-22 in Rs. Lakhs.
1b  annual_turnover_2022_23       → Turnover FY2022-23 in Rs. Lakhs.
1c  annual_turnover_2023_24       → Turnover FY2023-24 in Rs. Lakhs.
2   positive_networth_for_latest_fy → "Applicable - Positive", "Applicable - Negative", or "Not Applicable".
    pq_financial_status           → "Qualified", "Not Qualified", or "Query to be raised".

RULE: If a value is not found in the context, write "Not Found in Documents" — do NOT leave blank.
""",
    },
    {
        "id":     "e",
        "label":  "(e) Materials - Technical Evaluation",
        "search_query": "technical specification signed sealed NIL deviation statement technical compliance user department requirement",
        "instruction": """
You must fill EVERY field below from the bidder's submitted documents.

FIELDS TO EXTRACT:
1   technical_specification_signed_and_sealed   → "Yes - Signed & Sealed", "No", or "Not Found".
2   nil_deviation_statement_signed_and_sealed   → "Yes - Signed & Sealed", "No", or "Not Found".
3   additional_user_department_requirement      → Additional requirements, or "None".
4   deviations                                  → List of technical deviations.
    technical_evaluation_status                 → "Qualified", "Not Qualified", or "Query to be raised".

RULE: If a value is not found in the context, write "Not Found in Documents" — do NOT leave blank.
""",
    },
    {
        "id":     "f",
        "label":  "(f) Materials - Commercial Evaluation (CBA)",
        "search_query": "vendor code contact person email mobile EMD MSE UDYAM MII local content GST blacklisting integrity pact deviations validity declarations",
        "instruction": """
You must fill EVERY field below from the bidder's submitted documents.

FIELDS TO EXTRACT:
1   vendor_code                        → Vendor Code of the bidder.
2   contact_person                     → Name of the contact person.
3   mobile_number                      → Mobile number of the contact person.
4   email_id                           → Email ID of the contact person.
5   emd_applicability                  → "Applicable" or "Not Applicable".
10  udyam_number                       → UDYAM number or "Not Applicable".
27  gst_number                         → GST Registration Number.
    commercial_evaluation_status       → "Qualified", "Not Qualified", or "Query to be raised".

RULE: If a value is not found in the context, write "Not Found in Documents" — do NOT leave blank.
""",
    },
]

SECTION_MAP = {s["id"]: s for s in EVALUATIONS}

# ── FastAPI app ───────────────────────────────────────────────
app = FastAPI(title="Tender Evaluation Demo", version="1.0.0")


def _extract_text(response) -> str:
    """Normalize LLM response to a plain string, handling str/list/dict content."""
    content = response.content if hasattr(response, "content") else str(response)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        # List of content parts — join text parts
        parts = []
        for part in content:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict):
                parts.append(part.get("text", str(part)))
            else:
                parts.append(str(part))
        return "".join(parts)
    return str(content)


def get_vectorstore():
    from langchain_ollama import OllamaEmbeddings
    from langchain_postgres import PGVector
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    return PGVector(
        embeddings=embeddings,
        collection_name=COLLECTION_NAME,
        connection=CONNECTION_STRING,
    )


def get_llm():
    api_key    = os.getenv("GEMINI_API_KEY", "")
    model_id   = os.getenv("MODEL_ID", "gemini-3-flash-preview")
    gcp_project= os.getenv("GOOGLE_CLOUD_PROJECT", "")
    gcp_location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    if gcp_location == "global":
        gcp_location = "us-central1"

    use_vertexai = os.getenv("GEMINI_USE_VERTEXAI", "false").lower() == "true"

    if use_vertexai and gcp_project and api_key:
        try:
            from langchain_google_vertexai import ChatVertexAI
            llm = ChatVertexAI(model=model_id, api_key=api_key,
                               project=gcp_project, location=gcp_location, temperature=0)
            return llm, f"{model_id} (Vertex AI)"
        except Exception as exc:
            logger.warning(f"Vertex AI failed: {exc}")

    if api_key:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            llm = ChatGoogleGenerativeAI(model=model_id, google_api_key=api_key, temperature=0)
            return llm, f"{model_id} (Google AI Studio)"
        except Exception as exc:
            logger.warning(f"Google AI Studio failed: {exc}")

    from langchain_ollama import ChatOllama
    return ChatOllama(model="qwen2.5-coder:latest", temperature=0), "Ollama qwen2.5-coder"


# ── Routes ────────────────────────────────────────────────────
@app.get("/api/sections")
def list_sections():
    return [{"id": s["id"], "label": s["label"]} for s in EVALUATIONS]


@app.post("/api/evaluate/{section_id}")
def evaluate_section(section_id: str) -> Any:
    section = SECTION_MAP.get(section_id)
    if not section:
        raise HTTPException(status_code=404, detail=f"Section '{section_id}' not found.")

    # ── Step 1: Retrieve chunks from vector DB ────────────────
    try:
        vectorstore = get_vectorstore()
        docs = vectorstore.similarity_search(section["search_query"], k=12)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Vector DB error: {exc}")

    if not docs:
        raise HTTPException(status_code=404, detail="No documents found in the database. Please run extract_and_embed.py first.")

    # Build serialisable chunk list (with metadata for the frontend)
    chunks = []
    for i, doc in enumerate(docs):
        chunks.append({
            "index":   i + 1,
            "source":  doc.metadata.get("source", "Unknown"),
            "bidder":  doc.metadata.get("bidder", "Unknown"),
            "page":    doc.metadata.get("page", "N/A"),
            "chars":   len(doc.page_content),
            "content": doc.page_content,
        })

    context_text = "\n\n".join(d.page_content for d in docs)

    # ── Step 2: Build prompt ──────────────────────────────────
    prompt = f"""You are an expert Tender Evaluation AI Agent working for CPCL (Chennai Petroleum Corporation Limited).

Evaluation Section: {section['label']}

TASK — Fill every single field listed below. For each field:
- If found in the documents, extract the exact value.
- If NOT found, write "Not Found in Documents".
- Never leave a field empty.

{section['instruction']}

Bidder Documentation Context (retrieved from submitted documents):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{context_text}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CRITICAL: Respond with ONLY a valid JSON object. Fill ALL fields. No markdown, no explanations.
"""

    # ── Step 3: Call LLM with Full Fallback Chain ─────────────────
    api_key      = os.getenv("GEMINI_API_KEY", "")
    model_id     = os.getenv("MODEL_ID", "gemini-3-flash-preview")
    gcp_project  = os.getenv("GOOGLE_CLOUD_PROJECT", "")
    gcp_location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    if gcp_location == "global":
        gcp_location = "us-central1"
    use_vertexai = os.getenv("GEMINI_USE_VERTEXAI", "false").lower() == "true"

    raw_text  = None
    llm_label = "Unknown"
    errors    = []

    # Priority 1: Vertex AI via API Key
    if use_vertexai and gcp_project and api_key:
        try:
            from langchain_google_vertexai import ChatVertexAI
            logger.info(f"[LLM] Trying {model_id} via Vertex AI (project={gcp_project})")
            llm = ChatVertexAI(model=model_id, api_key=api_key, project=gcp_project, location=gcp_location, temperature=0)
            response  = llm.invoke(prompt)
            raw_text  = _extract_text(response)
            llm_label = f"{model_id} (Vertex AI)"
        except Exception as e:
            logger.warning(f"[LLM] Vertex AI failed: {e}")
            errors.append(f"Vertex AI: {e}")

    # Priority 2: Google AI Studio (direct API key)
    if not raw_text and api_key:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            logger.info(f"[LLM] Trying {model_id} via Google AI Studio")
            llm = ChatGoogleGenerativeAI(model=model_id, google_api_key=api_key, temperature=0)
            response  = llm.invoke(prompt)
            raw_text  = _extract_text(response)
            llm_label = f"{model_id} (Google AI Studio)"
        except Exception as e:
            logger.warning(f"[LLM] Google AI Studio failed: {e}")
            errors.append(f"Google AI Studio ({model_id}): {e}")

    # Priority 3: Ollama local fallback (only if a chat model is available)
    if not raw_text:
        try:
            import httpx
            ollama_models_resp = httpx.get("http://localhost:11434/api/tags", timeout=5)
            available = [m["name"] for m in ollama_models_resp.json().get("models", [])]
            chat_models = [m for m in available if "embed" not in m.lower()]
            if chat_models:
                ollama_model = chat_models[0]
                from langchain_ollama import ChatOllama
                logger.info(f"[LLM] Trying Ollama model: {ollama_model}")
                llm = ChatOllama(model=ollama_model, temperature=0)
                response  = llm.invoke(prompt)
                raw_text  = _extract_text(response)
                llm_label = f"Ollama {ollama_model} (local)"
            else:
                errors.append("Ollama: No local chat models installed. Only embedding models found.")
        except Exception as e:
            logger.warning(f"[LLM] Ollama failed: {e}")
            errors.append(f"Ollama: {e}")

    if not raw_text:
        extracted = {
            "error": "All LLMs in the priority chain failed.",
            "details": " | ".join(errors),
            "hint": f"Your API key quota for '{model_id}' may be exhausted. Try changing MODEL_ID in .env to another model (e.g. gemini-1.5-flash), or install a local Ollama chat model."
        }
        return JSONResponse({
            "section_id":      section_id,
            "section_label":   section["label"],
            "llm_used":        "Error",
            "chunks_retrieved": len(chunks),
            "chunks":          chunks,
            "extracted":       extracted,
        })

    # Log the raw response so it's visible in the server terminal
    logger.info(f"[LLM] Raw response ({len(raw_text)} chars): {raw_text[:500]!r}")

    extracted = None

    # Strategy 1: Strip markdown code fences (```json ... ``` or ``` ... ```)
    clean_text = raw_text.strip()
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", clean_text, re.DOTALL)
    if fence_match:
        try:
            extracted = json.loads(fence_match.group(1))
            logger.info("[LLM] Parsed JSON via markdown fence extraction.")
        except Exception:
            pass

    # Strategy 2: Direct JSON parse (entire response is valid JSON)
    if extracted is None:
        try:
            extracted = json.loads(clean_text)
            logger.info("[LLM] Parsed JSON via direct parse.")
        except Exception:
            pass

    # Strategy 3: Greedy regex — find outermost { ... }
    if extracted is None:
        json_match = re.search(r"\{.*\}", clean_text, re.DOTALL)
        if json_match:
            try:
                extracted = json.loads(json_match.group())
                logger.info("[LLM] Parsed JSON via greedy regex.")
            except Exception:
                pass

    if extracted is None:
        logger.warning(f"[LLM] Could not parse JSON. Full raw text: {raw_text!r}")
        extracted = {
            "error": "JSON Parse Error — model did not return valid JSON.",
            "raw_response": raw_text,
            "hint": "The model may have returned an explanation instead of JSON. Check the server logs for the full response."
        }

    return JSONResponse({
        "section_id":  section_id,
        "section_label": section["label"],
        "llm_used":    llm_label,
        "chunks_retrieved": len(chunks),
        "chunks":      chunks,
        "extracted":   extracted,
    })

# ── Serve static frontend ─────────────────────────────────────
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
