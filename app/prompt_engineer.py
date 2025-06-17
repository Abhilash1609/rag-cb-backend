def build_prompt(user_question: str, context_docs: list[dict]) -> str:
    context_blocks = []
    for doc in context_docs:
        question = doc.get("question", "").strip()
        answer = doc.get("answer", "").strip()
        context_blocks.append(f"Q: {question}\nA: {answer}")

    context = "\n\n".join(context_blocks)

    prompt = f"""You are Abhilash Nagisetty, a helpful and knowledgeable AI assistant trained on my resume and personal information.
Answer the user's question based on the context below. Be accurate, concise, and polite.

Context:
{context}

User Question: {user_question}

Answer:"""
    
    return prompt.strip()
