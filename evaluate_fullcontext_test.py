"""
evaluate_fullcontext_test.py
────────────────────────────
TEST SCRIPT: Bypasses vector DB retrieval entirely.
Feeds ALL OCR-extracted text directly to the LLM for every section.

If this produces better results than the RAG pipeline → retrieval is the bottleneck.
If results are still "Not Found" → the data is genuinely missing from the OCR text.

Output goes to:  ./fullcontext_test_evaluation/

Usage:
    python evaluate_fullcontext_test.py
    python evaluate_fullcontext_test.py --ocr-dir ocr_inspection/Bidder2offer
"""

import argparse
import json
import logging
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate

# ── same models as the real pipeline ─────────────────────────────
from models import (
    ContractsTechEvaluation,
    ContractsCommercialEvaluation,
    MaterialsPQExperience,
    MaterialsPQFinancial,
    MaterialsTechnicalEvaluation,
    MaterialsCommercialEvaluation,
)

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

OUTPUT_DIR = Path("fullcontext_test_evaluation")
DEFAULT_OCR_DIR = Path("ocr_inspection/Bidder2offer")

# ── Same sections / instructions as evaluate_full.py ─────────────
EVALUATIONS = [
    {
        "id": "a",
        "label": "(a) PQC Exp. & Technical Evaluation (Contracts)",
        "schema": ContractsTechEvaluation,
        "instruction": """
FIELDS TO EXTRACT:
1.1  similar_nature_of_job
1.2  value_of_work_order_required
1.3  details_of_work_order_submitted
1.4  work_order_number_and_date
1.5  nature_of_industry
1.6  name_of_issuer
1.7  completion_certificate_details
1.8  executed_value_as_per_completion_certificate
1.9  value_considered_for_technical_evaluation
1.10 annualization_of_value
1.11 subcontract_approval_submitted
1.12 work_order_meeting_experience_criteria
2    additional_technical_pqc
3    deviations
4    query_to_be_raised
5    technical_acceptance_status
6    reason_for_rejection
RULE: If not found, write "Not Found in Documents".
""",
    },
    {
        "id": "b",
        "label": "(b) PQC Fin. & Commercial Evaluation (Contracts)",
        "schema": ContractsCommercialEvaluation,
        "instruction": """
FIELDS TO EXTRACT:
1   technical_qualification
2   integrity_pact
3   emd_applicable
3a  emd_in_form_of_bg
4   emd_sent_to_finance
5a  annual_turnover_2021_22
5b  annual_turnover_2022_23
5c  annual_turnover_2023_24
6   share_capital / reserve_and_surplus / loss / networth
7   epf_code_number
8   esi_code_number
9   cpcl_vendor_code
10  power_of_attorney_submitted
11a-k  formats submitted
12  mse_status
13  mii_status
14  blacklisting_sap_cppp_gem
15  blacklisting_in_gst_portal
16  deviations
17  corrigendums_signed_submitted
18  queries_to_be_raised
19  commercial_evaluation_status
20  reason_for_rejection
RULE: If not found, write "Not Found in Documents".
""",
    },
    {
        "id": "c",
        "label": "(c) Materials - PQ Experience Criteria",
        "schema": MaterialsPQExperience,
        "instruction": """
FIELDS TO EXTRACT:
1a  po_item_description
1b  po_number
1c  po_acceptable_date
1d  po_value
1e  po_issuer_name
1f  po_receiver_name
1g  po_issuer_type_of_industry
1h  po_supplied_value
1i  proof_of_supply
1j  supplied_within_india
1k  commissioned
2   additional_pqc
    queries_to_be_raised
    pqc_experience_status
    reason_for_rejection
RULE: If not found, write "Not Found in Documents".
""",
    },
    {
        "id": "d",
        "label": "(d) Materials - PQ Financial Criteria",
        "schema": MaterialsPQFinancial,
        "instruction": """
FIELDS TO EXTRACT:
1   annual_turnover_applicable
1a  annual_turnover_2021_22
1b  annual_turnover_2022_23
1c  annual_turnover_2023_24
2   positive_networth_for_latest_fy
    networth_value
    queries_to_be_raised
    pq_financial_status
    reason_for_rejection
RULE: If not found, write "Not Found in Documents".
""",
    },
    {
        "id": "e",
        "label": "(e) Materials - Technical Evaluation",
        "schema": MaterialsTechnicalEvaluation,
        "instruction": """
FIELDS TO EXTRACT:
1   technical_specification_signed_and_sealed
2   nil_deviation_statement_signed_and_sealed
3   additional_user_department_requirement
4   deviations
    query_to_be_raised
    technical_evaluation_status
    reason_for_rejection
RULE: If not found, write "Not Found in Documents".
""",
    },
    {
        "id": "f",
        "label": "(f) Materials - Commercial Evaluation (CBA)",
        "schema": MaterialsCommercialEvaluation,
        "instruction": """
FIELDS TO EXTRACT:
1   vendor_code
2   contact_person
3   mobile_number
4   email_id
5   emd_applicability
6   emd_details
7   emd_exemption_reason
8   mse_preference_applicability
9   mse_preference_applied_in_gem
10  udyam_number
11  mse_category
12  mse_pp_verification
13  mse_purchase_preference_eligibility
14  mii_preference_applicability
15  mii_preference_applied_in_gem
16  mii_local_content_declaration
17  local_content_percentage
18  mii_purchase_preference_eligibility
19  integrity_pact
20  confidentiality_clause_declaration
21  holiday_listing_declaration
22  land_border_sharing_declaration
23  nil_deviations_declaration
24  details_of_deviations
25  deviations_acceptance
26  validity
27  gst_number
28  gst_filing_status
29  blacklisted_in_cpcl_mopng
    query_to_be_raised
    commercial_evaluation_status
    reason_for_rejection
RULE: If not found, write "Not Found in Documents".
""",
    },
]

PROMPT = PromptTemplate.from_template(
    """You are an expert Tender Evaluation AI for CPCL (Chennai Petroleum Corporation Limited).

Evaluation Section: {section_label}

TASK: Fill every single field listed below from the bidder's submitted documents.
- If found: extract the EXACT value.
- If NOT found: write "Not Found in Documents".
- NEVER leave a field blank.

{instruction}

=== COMPLETE BIDDER DOCUMENT TEXT (ALL FILES) ===
{context}
=== END OF DOCUMENTS ===

CRITICAL: Output MUST be valid structured JSON matching the schema. Fill ALL fields.
"""
)


# ── LLM — prefer Gemini AI Studio (large context) ────────────────

def get_llm():
    api_key = os.getenv("GEMINI_API_KEY", "")

    # Try models in order of context window size — stop at first that works
    models_to_try = [
        "gemini-3-flash-preview"         # 2M context, lower RPM
    ]

    if api_key:
        from langchain_google_genai import ChatGoogleGenerativeAI
        for model_id in models_to_try:
            try:
                logger.info(f"[LLM] Trying {model_id} via Google AI Studio...")
                llm = ChatGoogleGenerativeAI(
                    model=model_id,
                    google_api_key=api_key,
                    temperature=0,
                )
                # Quick smoke test
                llm.invoke("ping")
                logger.info(f"[LLM] Using {model_id}")
                return llm, f"{model_id} (Google AI Studio)"
            except Exception as e:
                logger.warning(f"[LLM] {model_id} failed: {e}")

    from langchain_ollama import ChatOllama
    logger.warning("[LLM] All Gemini models failed — falling back to Ollama. NOTE: Ollama has a small context window and WILL truncate the full-context prompt.")
    return ChatOllama(model="qwen2.5-coder:latest", temperature=0), "Ollama"


# ── Load all OCR text from inspection folder ──────────────────────

def load_all_ocr_text(ocr_dir: Path) -> str:
    """Read every *_raw.txt file and concatenate into one big context string."""
    raw_files = sorted(ocr_dir.glob("*_raw.txt"))
    if not raw_files:
        raise FileNotFoundError(
            f"No *_raw.txt files found in {ocr_dir}.\n"
            "Run  python inspect_ocr.py \"Bidder2 offer.zip\"  first."
        )

    parts = []
    total_chars = 0
    for f in raw_files:
        content = f.read_text(encoding="utf-8", errors="replace")
        # Strip the header lines (FILE/TYPE/PATH/CHARS/STATUS/==) — keep raw text only
        lines = content.splitlines()
        # Find the === separator line and take everything after it
        sep = next((i for i, l in enumerate(lines) if l.startswith("="*10)), 5)
        raw_text = "\n".join(lines[sep + 1:]).strip()
        if raw_text:
            src = f.stem.replace("_raw", "")
            parts.append(f"\n{'─'*60}\n[FILE: {src}]\n{'─'*60}\n{raw_text}")
            total_chars += len(raw_text)

    full_context = "\n".join(parts)
    logger.info(f"Loaded {len(raw_files)} files | {total_chars:,} total chars")
    return full_context


# ── Run one section ───────────────────────────────────────────────

def evaluate_section(section: dict, context: str, llm, llm_label: str) -> dict:
    sid   = section["id"]
    label = section["label"]
    logger.info(f"  [{sid.upper()}] {label}")

    prompt_text = PROMPT.format(
        section_label=label,
        instruction=section["instruction"],
        context=context,
    )
    logger.info(f"       Prompt size: {len(prompt_text):,} chars")

    try:
        structured = llm.with_structured_output(section["schema"])
        result = structured.invoke(prompt_text)
    except Exception as exc:
        logger.error(f"       LLM failed: {exc}")
        return {"error": str(exc)}

    if result is None:
        return {}

    data = result.model_dump()
    # Count how many fields are NOT "Not Found in Documents"
    found = sum(
        1 for v in data.values()
        if isinstance(v, str) and v not in ("Not Found in Documents", "")
        or isinstance(v, list) and len(v) > 0
    )
    total = len(data)
    logger.info(f"       {found}/{total} fields populated  ✓")
    return data


# ── Main ──────────────────────────────────────────────────────────

def main(ocr_dir: Path):
    OUTPUT_DIR.mkdir(exist_ok=True)

    logger.info("=" * 60)
    logger.info("FULL-CONTEXT TEST — no retrieval, all text sent to LLM")
    logger.info("=" * 60)

    context = load_all_ocr_text(ocr_dir)
    llm, llm_label = get_llm()

    all_results = {}
    for section in EVALUATIONS:
        data = evaluate_section(section, context, llm, llm_label)
        sid  = section["id"]
        all_results[sid] = data

        out = OUTPUT_DIR / f"section_{sid}.json"
        out.write_text(json.dumps(data, indent=4, ensure_ascii=False), encoding="utf-8")
        logger.info(f"       Saved → {out}")

    # ── Compare summary ───────────────────────────────────────────
    logger.info("\n" + "=" * 60)
    logger.info("RESULTS SUMMARY — fields found vs not-found")
    logger.info("=" * 60)
    for sid, data in all_results.items():
        if not data:
            logger.info(f"  [{sid.upper()}] ERROR / empty")
            continue
        found     = sum(1 for v in data.values()
                        if isinstance(v, str) and v not in ("Not Found in Documents", "")
                        or isinstance(v, list))
        not_found = sum(1 for v in data.values()
                        if isinstance(v, str) and v == "Not Found in Documents")
        label = next(s["label"] for s in EVALUATIONS if s["id"] == sid)
        logger.info(f"  [{sid.upper()}] found={found}  not_found={not_found}  | {label}")

    logger.info(f"\nOutput folder: {OUTPUT_DIR.resolve()}")
    logger.info("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Full-context evaluation test (no RAG retrieval)"
    )
    parser.add_argument(
        "--ocr-dir",
        type=Path,
        default=DEFAULT_OCR_DIR,
        help=f"Folder with *_raw.txt files (default: {DEFAULT_OCR_DIR})",
    )
    args = parser.parse_args()

    if not args.ocr_dir.exists():
        print(f"ERROR: OCR dir not found: {args.ocr_dir}")
        print("Run first:  python inspect_ocr.py \"Bidder2 offer.zip\"")
        raise SystemExit(1)

    main(args.ocr_dir)
