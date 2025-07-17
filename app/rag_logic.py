from app.vertex import generate_embedding, generate_answer
from app.qdrant_client import search_similar_docs
from app.prompt_engineer import build_prompt
import logging

COLLECTION_NAME = "rag-chatbot"

def ask_question(query: str) -> tuple[str, list[float]]:
    query_vector = generate_embedding(query)
    search_results = search_similar_docs(COLLECTION_NAME, query_vector)

    logging.info(f"\n🔍 Search results for query: '{query}'")
    for i, result in enumerate(search_results, 1):
        payload = result.payload
        score = result.score
        logging.info(f"{i}. Score: {score:.4f}")
        logging.info(f"   Q: {payload.get('question', '')}")
        logging.info(f"   A: {payload.get('answer', '')}")

    context_docs = []
    for result in search_results:
        payload = result.payload
        context_docs.append({
            "question": payload.get("question", ""),
            "answer": payload.get("answer", "")
        })

    prompt = build_prompt(query, context_docs)
    answer = generate_answer(prompt)

    return answer, query_vector

