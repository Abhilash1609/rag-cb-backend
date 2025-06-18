from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from uuid import uuid4
import google.api_core.exceptions

from app.rag_logic import ask_question
from app.vertex import get_access_token
from app.auth import verify_google_token
from app.qdrant_client import client, init_user_collections

app = FastAPI()

# -----------------------------
# Startup - Init Qdrant Collections
# -----------------------------
@app.on_event("startup")
def startup_event():
    init_user_collections()

class NewChatRequest(BaseModel):
    id_token: str

@app.post("/new_chat")
def new_chat(req: NewChatRequest):
    try:
        user_id = verify_google_token(req.id_token)
        new_chat_id = str(uuid4())

        client.upsert(
            collection_name="user_chats",
            points=[
                {
                    "id": str(uuid4()),
                    "vector": [0.0],  # dummy
                    "payload": {
                        "user_id": user_id,
                        "chat_id": new_chat_id,
                    }
                }
            ]
        )

        return {"status": "chat created", "chat_id": new_chat_id}
    except Exception as e:
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
            scroll_filter={
                "must": [
                    {"key": "chat_id", "match": {"value": req.chat_id}},
                    {"key": "user_id", "match": {"value": user_id}}
                ]
            },
            limit=100,
        )

        messages = [
            {
                "message": point.payload["message"],
                "role": point.payload["role"]
            }
            for point in results[0]
        ]

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

    chat_ids = [point.payload["chat_id"] for point in results[0]]
    return {"chat_ids": chat_ids}

# -----------------------------
# Ask Endpoint (RAG Logic)
# -----------------------------
class QuestionRequest(BaseModel):
    question: str

@app.post("/ask")
def ask(request: QuestionRequest):
    try:
        response = ask_question(request.question)
        return {"response": response}
    except google.api_core.exceptions.Unauthenticated:
        print("Unauthenticated - refreshing token and retrying...")
        get_access_token()
        try:
            response = ask_question(request.question)
            return {"response": response}
        except Exception as retry_error:
            raise HTTPException(status_code=500, detail=f"Retry failed: {retry_error}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")

# -----------------------------
# Add Chat Message Endpoint
# -----------------------------
class ChatMessageRequest(BaseModel):
    id_token: str
    chat_id: str
    message: str
    role: str  # "user" or "assistant"

@app.post("/add_message")
def add_message(req: ChatMessageRequest):
    try:
        user_id = verify_google_token(req.id_token)

        client.upsert(
            collection_name="chat_messages",
            points=[
                {
                    "id": str(uuid4()),
                    "vector": [0.0],  # dummy vector
                    "payload": {
                        "user_id": user_id,
                        "chat_id": req.chat_id,
                        "message": req.message,
                        "role": req.role,
                    }
                }
            ]
        )
        return {"status": "message added", "user_id": user_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
