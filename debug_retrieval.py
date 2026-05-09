"""
debug_retrieval.py
──────────────────
Shows exactly which chunks are retrieved for each evaluation section query.
This tells you whether the problem is RETRIEVAL (wrong chunks coming back)
or CONTENT (right chunks come back but data is missing from the text).

Usage:
    python debug_retrieval.py                # tests all 6 section queries
    python debug_retrieval.py --section f    # test only section f
    python debug_retrieval.py --query "vendor code GST mobile"  # custom query
"""

import argparse
from langchain_ollama import OllamaEmbeddings
from langchain_postgres import PGVector

CONNECTION_STRING = "postgresql+psycopg://admin:password@localhost:5444/tender_eval"
COLLECTION_NAME   = "bidder_documents"

SECTION_QUERIES = {
    "a": "work order experience criteria technical qualification completion certificate executed value industry petroleum petrochemical",
    "b": "annual turnover financial statements networth EPF ESI EMD formats submission MSE MII blacklisting commercial evaluation",
    "c": "purchase order PO supply experience criteria GST invoice delivery challan commissioning proof of supply materials",
    "d": "annual turnover balance sheet networth financial year 2021 2022 2023 2024 profit loss reserves capital",
    "e": "technical specification signed sealed NIL deviation statement technical compliance user department requirement",
    "f": "vendor code contact person email mobile EMD MSE UDYAM MII local content GST blacklisting integrity pact deviations validity declarations",
}

def run(section_id: str, query: str, k: int):
    embeddings  = OllamaEmbeddings(model="nomic-embed-text")
    vectorstore = PGVector(
        embeddings=embeddings,
        collection_name=COLLECTION_NAME,
        connection=CONNECTION_STRING,
    )

    print(f"\n{'='*70}")
    print(f"SECTION [{section_id.upper()}]  k={k}")
    print(f"QUERY : {query}")
    print(f"{'='*70}")

    docs = vectorstore.similarity_search(query, k=k)
    if not docs:
        print("  !! NO CHUNKS RETRIEVED !!")
        return

    for i, doc in enumerate(docs, 1):
        src   = doc.metadata.get("source", "?")
        chars = len(doc.page_content)
        print(f"\n  ── Chunk {i:02d}/{len(docs)} │ source: {src} │ {chars} chars ──")
        # Print first 400 chars so you can see what the LLM actually sees
        preview = doc.page_content[:500].replace("\n", " ").strip()
        print(f"  {preview}")

    print(f"\n  Total chunks retrieved: {len(docs)}")
    print(f"  Sources: {list({d.metadata.get('source','?') for d in docs})}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--section", default="all",
                        help="Section id (a-f) or 'all'")
    parser.add_argument("--query",   default=None,
                        help="Custom search query (overrides section query)")
    parser.add_argument("--k",       type=int, default=15,
                        help="Number of chunks to retrieve (default: 15)")
    args = parser.parse_args()

    if args.query:
        run("custom", args.query, args.k)
    elif args.section == "all":
        for sid, q in SECTION_QUERIES.items():
            run(sid, q, args.k)
    else:
        sid = args.section.lower()
        if sid not in SECTION_QUERIES:
            print(f"Unknown section '{sid}'. Choose from: {list(SECTION_QUERIES)}")
        else:
            run(sid, SECTION_QUERIES[sid], args.k)
