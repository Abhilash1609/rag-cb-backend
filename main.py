import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel
from uuid import uuid4
import spacy
from fastapi.middleware.cors import CORSMiddleware
from app.vertex import get_access_token
from app.auth import verify_google_token
from app.qdrant_client import client, init_user_collections
from app.rag_logic import ask_question
from qdrant_client.models import Filter, FieldCondition, MatchValue

# Logging config
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load Spacy model
nlp = spacy.load("en_core_web_sm")

def generate_chat_title(prompt: str) -> str:
    doc = nlp(prompt)
    noun_phrases = [chunk.text for chunk in doc.noun_chunks]
    if noun_phrases:
        return noun_phrases[0].strip().capitalize()
    return " ".join(prompt.strip().split()[:5]).capitalize() or "New Chat"

# FastAPI app
app = FastAPI()

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Suppress livereload noise
@app.middleware("http")
async def suppress_livereload_404(request: Request, call_next):
    if request.url.path.startswith("/livereload/"):
        return Response(status_code=204)
    return await call_next(request)

# Initialize Qdrant collections on startup
@app.on_event("startup")
def startup_event():
    logger.info("🚀 Initializing Qdrant collections...")
    init_user_collections()


# --------------------------- MODELS ---------------------------
class NewChatRequest(BaseModel):
    id_token: str
    first_prompt: str

class GetChatHistoryRequest(BaseModel):
    id_token: str
    chat_id: str

class ListChatsRequest(BaseModel):
    id_token: str

class AskRequest(BaseModel):
    id_token: str
    chat_id: str
    question: str


# --------------------------- ROUTES ---------------------------
@app.post("/new_chat")
def new_chat(req: NewChatRequest):
    logger.info("📦 /new_chat body: %s", req.model_dump())
    try:
        user_id = verify_google_token(req.id_token)
        logger.info("✅ Verified user ID: %s", user_id)

        new_chat_id = str(uuid4())
        chat_title = generate_chat_title(req.first_prompt)

        client.upsert(
            collection_name="user_chats",
            points=[{
                "id": str(uuid4()),
                "vector": [0.0] * 3072,
                "payload": {
                    "user_id": user_id,
                    "chat_id": new_chat_id,
                    "chat_title": chat_title,
                }
            }]
        )
        logger.info("✅ New chat created with ID: %s", new_chat_id)
        return {"status": "chat created", "chat_id": new_chat_id, "chat_title": chat_title}

    except Exception as e:
        logger.error("❌ Error in /new_chat: %s", e)
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/get_chat_history")
def get_chat_history(req: GetChatHistoryRequest):
    try:
        user_id = verify_google_token(req.id_token)
        results = client.scroll(
            collection_name="chat_messages",
            scroll_filter=Filter(must=[
                FieldCondition(key="chat_id", match=MatchValue(value=req.chat_id)),
                FieldCondition(key="user_id", match=MatchValue(value=user_id)),
            ]),
            limit=100,
        )

        messages = []
        for point in results[0]:
            payload = point.payload
            if "question" in payload and "answer" in payload:
                messages.append({"question": payload["question"], "answer": payload["answer"]})

        return {"messages": messages}
    except Exception as e:
        logger.error("❌ Error in /get_chat_history: %s", e)
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/list_chats")
def list_chats(req: ListChatsRequest):
    try:
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
    except Exception as e:
        logger.error("❌ Error in /list_chats: %s", e)
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/ask")
def ask(req: AskRequest):
    try:
        logger.info("🧠 /ask request: %s", req.model_dump())
        user_id = verify_google_token(req.id_token)
        answer, vector = ask_question(req.question)
        logger.info("✅ Answer: %s...", answer[:50])

        client.upsert(
            collection_name="chat_messages",
            points=[{
                "id": str(uuid4()),
                "vector": vector,
                "payload": {
                    "user_id": user_id,
                    "chat_id": req.chat_id,
                    "question": req.question,
                    "answer": answer,
                }
            }]
        )
        logger.info("✅ Stored answer to Qdrant.")
        return {"response": answer}
    except Exception as e:
        logger.error("❌ Error in /ask: %s", e)
        raise HTTPException(status_code=400, detail=str(e))
