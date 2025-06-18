from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from uuid import uuid4
import google.api_core.exceptions
from fastapi.middleware.cors import CORSMiddleware
from app.rag_logic import ask_question
from app.vertex import get_access_token
from app.auth import verify_google_token
from app.qdrant_client import client, init_user_collections
from qdrant_client.models import Filter, FieldCondition, MatchValue
import spacy

nlp = spacy.load("en_core_web_sm")

def generate_chat_title(prompt: str) -> str:
    doc = nlp(prompt)

    # Try to extract first noun phrase (e.g., "backend engineer interview")
    noun_phrases = [chunk.text for chunk in doc.noun_chunks]
    if noun_phrases:
        return noun_phrases[0].strip().capitalize()

    # Fallback to first few words if no noun chunks
    return " ".join(prompt.strip().split()[:5]).capitalize() or "New Chat"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers including Authorization, Content-Type
)

# -----------------------------
# Startup - Init Qdrant Collections
# -----------------------------
@app.on_event("startup")
def startup_event():
    init_user_collections()

class NewChatRequest(BaseModel):
    id_token: str
    first_prompt: str

@app.post("/new_chat")
def new_chat(req: NewChatRequest):
    try:
        user_id = verify_google_token(req.id_token)
        new_chat_id = str(uuid4())

        chat_title = generate_chat_title(req.first_prompt)

        client.upsert(
            collection_name="user_chats",
            points=[
                {
                    "id": str(uuid4()),
                    "vector": [0.0] * 3072,  # dummy vector
                    "payload": {
                        "user_id": user_id,
                        "chat_id": new_chat_id,
                        "chat_title": chat_title,
                    }
                }
            ]
        )

        return {"status": "chat created", "chat_id": new_chat_id, "chat_title": chat_title}
    except Exception as e:
        print("❌ ERROR in /new_chat", e)
        raise HTTPException(status_code=400, detail=str(e))



class GetChatHistoryRequest(BaseModel):
    id_token: str
    chat_id: str

@app.post("/get_chat_history")
def get_chat_history(req: GetChatHistoryRequest):
    try:
        user_id = verify_google_token(req.id_token)

        results = client.scroll(
            collection_name="chat_messages",
            scroll_filter=Filter(
                must=[
                    FieldCondition(key="chat_id", match=MatchValue(value=req.chat_id)),
                    FieldCondition(key="user_id", match=MatchValue(value=user_id)),
                ]
            ),
            limit=100,
        )


        messages = []
        for point in results[0]:
            payload = point.payload
            if "question" in payload and "answer" in payload:
                messages.append({"role": "user", "message": payload["question"]})
                messages.append({"role": "assistant", "message": payload["answer"]})

        return {"messages": messages}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class ListChatsRequest(BaseModel):
    id_token: str

@app.post("/list_chats")
def list_chats(req: ListChatsRequest):
    user_id = verify_google_token(req.id_token)

    results = client.scroll(
        collection_name="user_chats",
        scroll_filter={"must": [{"key": "user_id", "match": {"value": user_id}}]},
        limit=100
    )

    chats = [
        {
            "chat_id": point.payload["chat_id"],
            "chat_title": point.payload.get("chat_title", "Untitled Chat")
        }
        for point in results[0]
    ]

    return {"chats": chats}


# -----------------------------
# Ask Endpoint (RAG Logic)
# -----------------------------
class AskRequest(BaseModel):
    id_token: str
    chat_id: str
    question: str

@app.post("/ask")
def ask(req: AskRequest):
    try:
        print("ASK PAYLOAD:", req)
        user_id = verify_google_token(req.id_token)
        print("✅ Token verified. User ID:", user_id)

        # 🧠 RAG logic now returns both answer and embedding
        answer, vector = ask_question(req.question)
        print("✅ RAG answer:", answer[:50])

        # 📝 Store Q&A as a single point
        client.upsert(
            collection_name="chat_messages",
            points=[
                {
                    "id": str(uuid4()),
                    "vector": vector,
                    "payload": {
                        "user_id": user_id,
                        "chat_id": req.chat_id,
                        "question": req.question,
                        "answer": answer,
                    }
                }
            ]
        )
        print("✅ Stored Q&A to Qdrant")
        return {"response": answer}
    except Exception as e:
        print("❌ ERROR in /ask:", e)
        raise HTTPException(status_code=400, detail=str(e))
