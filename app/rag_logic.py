from app.vertex import generate_embedding, generate_answer
from app.qdrant_client import search_similar_docs
from app.prompt_engineer import build_prompt

COLLECTION_NAME = "rag-chatbot"

def ask_question(query: str) -> str:
    query_vector = generate_embedding(query)
    search_results = search_similar_docs(COLLECTION_NAME, query_vector)

    context_docs = []
    for result in search_results:
        payload = result.payload
        context_docs.append({
            "question": payload.get("question", ""),
            "answer": payload.get("answer", "")
        })

    prompt = build_prompt(query, context_docs)
    return generate_answer(prompt)
