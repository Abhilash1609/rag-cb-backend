from fastapi import FastAPI
from pydantic import BaseModel
from app.rag_logic import ask_question
from app.vertex import get_access_token  # Ensure this exists and refreshes token
import google.api_core.exceptions

app = FastAPI()

class QuestionRequest(BaseModel):
    question: str

@app.post("/ask")
def ask(request: QuestionRequest):
    try:
        response = ask_question(request.question)
        return {"response": response}
    except google.api_core.exceptions.Unauthenticated as e:
        # Refresh the token manually
        print("Unauthenticated - refreshing token and retrying...")
        get_access_token()  # This should refresh and cache token internally if needed

        # Retry once
        try:
            response = ask_question(request.question)
            return {"response": response}
        except Exception as retry_error:
            raise Exception(f"Retry after token refresh failed: {retry_error}")
    except Exception as e:
        raise Exception(f"Unexpected error: {e}")
