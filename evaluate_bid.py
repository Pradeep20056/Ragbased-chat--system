import argparse
import logging
import os
from dotenv import load_dotenv
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_postgres import PGVector
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
    
    # Initialize Local LLM (Ollama) Using Phi model
    logger.info("Initializing Ollama (Phi) LLM...")
    llm = ChatOllama(
        model="phi",
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
        
        IMPORTANT: Your output MUST strictly follow the provided structured format.
        """
    )
    
    formatted_prompt = prompt_template.format(query=query, context=context_text)
    
    logger.info("Invoking Ollama LLM for reasoning and structured generation...")
    try:
        result = structured_llm.invoke(formatted_prompt)
        
        if result is None:
            logger.error("LLM returned None. This usually happens if the model failed to generate a response in the required structured format.")
            return

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
