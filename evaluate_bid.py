import argparse
import logging
import os
from dotenv import load_dotenv
from langchain_ollama import OllamaEmbeddings
from langchain_postgres import PGVector
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from models import PQEvaluationResult

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database configuration
CONNECTION_STRING = "postgresql+psycopg://admin:password@localhost:5444/tender_eval"
COLLECTION_NAME = "bidder_documents"

# Load environment variables
load_dotenv()

def evaluate(query: str):
    logger.info(f"Initializing Vector Store connections...")
    
    # Initialize Embedding model (On-Prem)
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    
    # Initialize PGVector (On-Prem)
    vectorstore = PGVector(
        embeddings=embeddings,
        collection_name=COLLECTION_NAME,
        connection=CONNECTION_STRING,
    )
    
    # Perform Similarity Search
    logger.info(f"Performing pgvector similarity search for query: '{query}'")
    retrieved_docs = vectorstore.similarity_search(query, k=10)
    
    if not retrieved_docs:
        logger.warning("No documents found in Vector Store. Have you run the extraction script?")
        return
        
    context_text = "\n\n".join([doc.page_content for doc in retrieved_docs])
    logger.info(f"Retrieved {len(retrieved_docs)} chunks containing relevant context.")
    
    # Initialize Cloud LLM (Google GenAI) Using Gemini 3 Flash
    logger.info("Initializing Google GenAI LLM...")
    llm = ChatGoogleGenerativeAI(
        model="gemini-3-flash-preview",
        google_api_key=os.getenv("GEMINI_API_KEY"),
        temperature=0
    )
    
    # Force structured output using our Pydantic schema
    structured_llm = llm.with_structured_output(PQEvaluationResult)
    
    # Craft the Prompt
    prompt_template = PromptTemplate.from_template(
        """You are an expert Tender Evaluation AI Agent.
        Analyze the provided bidder documentation context against the user's evaluation query.
        Extract any technical deviations, assess compliance, identify risks, and recommend an action.
        
        Evaluation Query: {query}
        
        Bidder Documentation Context:
        {context}
        """
    )
    
    formatted_prompt = prompt_template.format(query=query, context=context_text)
    
    logger.info("Invoking Vertex AI LLM for reasoning and structured generation...")
    try:
        result: PQEvaluationResult = structured_llm.invoke(formatted_prompt)
        
        logger.info("\n=== STRUCTURED JSON EVALUATION OUTPUT ===")
        print(result.model_dump_json(indent=4))
        logger.info("=========================================\n")
        
    except Exception as e:
        logger.error(f"Failed to generate evaluation: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate bidder using AI")
    parser.add_argument("--query", type=str, default="Identify technical deviations, risk criteria, and overall compliance.", help="Evaluation criteria or question")
    args = parser.parse_args()
    
    evaluate(args.query)
