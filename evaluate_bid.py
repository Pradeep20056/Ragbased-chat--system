import argparse
import logging
import os
from dotenv import load_dotenv
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_postgres import PGVector
from langchain_core.prompts import PromptTemplate
from models import PQEvaluationResult

# Load environment variables first
load_dotenv()

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database configuration
CONNECTION_STRING = "postgresql+psycopg://admin:password@localhost:5444/tender_eval"
COLLECTION_NAME = "bidder_documents"


def get_llm():
    """
    Returns the primary LLM (Google Gemini via API key) if GEMINI_API_KEY is present,
    otherwise falls back to local Ollama (phi).
    """
    gemini_api_key = os.getenv("GEMINI_API_KEY", "")

    if gemini_api_key:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            logger.info("[LLM] Using Gemini 3 Flash via Google AI (API Key)")
            llm = ChatGoogleGenerativeAI(
                model="gemini-3-flash-preview",
                google_api_key=gemini_api_key,
                temperature=0,
            )
            return llm, "Gemini 3 Flash (Google AI)"
        except Exception as e:
            logger.warning(f"[LLM] Gemini init failed ({e}). Falling back to Ollama...")

    # Fallback — local Ollama
    logger.info("[LLM] Falling back to Ollama (phi)...")
    llm = ChatOllama(model="phi", temperature=0)
    return llm, "Ollama phi (local fallback)"


def evaluate(query: str):
    logger.info("Initializing Vector Store connections...")

    # Embeddings — always on-prem via Ollama
    embeddings = OllamaEmbeddings(model="nomic-embed-text")

    # PGVector store
    vectorstore = PGVector(
        embeddings=embeddings,
        collection_name=COLLECTION_NAME,
        connection=CONNECTION_STRING,
    )

    # Similarity search
    logger.info(f"Performing pgvector similarity search for query: '{query}'")
    retrieved_docs = vectorstore.similarity_search(query, k=10)

    if not retrieved_docs:
        logger.warning("No documents found in Vector Store. Have you run the extraction script?")
        return

    context_text = "\n\n".join([doc.page_content for doc in retrieved_docs])
    logger.info(f"Retrieved {len(retrieved_docs)} chunks containing relevant context.")

    # Get LLM (Gemini primary, Ollama fallback)
    llm, llm_label = get_llm()
    logger.info(f"[LLM] Active model: {llm_label}")

    # Bind structured output schema
    structured_llm = llm.with_structured_output(PQEvaluationResult)

    # Build prompt
    prompt_template = PromptTemplate.from_template(
        """You are an expert Tender Evaluation AI Agent.
        Analyze the provided bidder documentation context against the user's evaluation query.
        Extract any technical deviations, assess compliance, identify risks, and recommend an action.

        Evaluation Query: {query}

        Bidder Documentation Context:
        {context}

        IMPORTANT: Your output MUST strictly follow the provided structured format.
        """
    )

    formatted_prompt = prompt_template.format(query=query, context=context_text)

    logger.info(f"Invoking {llm_label} for reasoning and structured generation...")
    try:
        result = structured_llm.invoke(formatted_prompt)
    except Exception as e:
        logger.warning(f"Primary LLM ({llm_label}) failed: {e}. Falling back to Ollama...")
        # Re-initialize with Ollama
        llm = ChatOllama(model="phi", temperature=0)
        structured_llm = llm.with_structured_output(PQEvaluationResult)
        logger.info("Invoking Ollama (phi) for reasoning and structured generation...")
        try:
            result = structured_llm.invoke(formatted_prompt)
        except Exception as ollama_e:
            logger.error(f"Fallback Ollama also failed: {ollama_e}")
            return

    if result is None:
        logger.error(
            "LLM returned None. The model may have failed to generate "
            "a response in the required structured format."
        )
        return

    logger.info("\n=== STRUCTURED JSON EVALUATION OUTPUT ===")
    print(result.model_dump_json(indent=4))
    logger.info("=========================================\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate bidder using AI")
    parser.add_argument(
        "--query",
        type=str,
        default="Identify technical deviations, risk criteria, and overall compliance.",
        help="Evaluation criteria or question",
    )
    args = parser.parse_args()

    evaluate(args.query)
