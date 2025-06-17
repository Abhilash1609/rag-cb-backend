import os
import requests
import json
from google.oauth2 import service_account
import google.auth.transport.requests
from app.config import get_env_variable

# Load environment variables
PROJECT_ID = os.getenv("GCP_PROJECT_ID")
LOCATION = os.getenv("GCP_LOCATION", "us-central1")
EMBEDDING_MODEL_ID = "gemini-embedding-001"
GENERATION_MODEL_ID = "gemini-2.0-flash-001"
SERVICE_ACCOUNT_FILE = get_env_variable("GOOGLE_APPLICATION_CREDENTIALS")

SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]

# ----------------------------
# Auth: Get access token
# ----------------------------
def get_access_token():
    if not SERVICE_ACCOUNT_FILE:
        raise ValueError("GOOGLE_APPLICATION_CREDENTIALS is not set")

    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    auth_req = google.auth.transport.requests.Request()
    credentials.refresh(auth_req)
    return credentials.token

# ----------------------------
# Embedding logic
# ----------------------------
def call_vertex_embedding_api(text: str, token: str):
    url = (
        f"https://{LOCATION}-aiplatform.googleapis.com/v1/projects/{PROJECT_ID}"
        f"/locations/{LOCATION}/publishers/google/models/{EMBEDDING_MODEL_ID}:predict"
    )

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "instances": [
            {
                "content": text,
                "task_type": "RETRIEVAL_DOCUMENT"
            }
        ]
    }

    response = requests.post(url, headers=headers, json=payload)
    return response

def generate_embedding(text: str):
    token = get_access_token()
    response = call_vertex_embedding_api(text, token)

    if response.status_code == 401:
        token = get_access_token()
        response = call_vertex_embedding_api(text, token)

    if response.status_code != 200:
        raise Exception(f"[Embedding] Error {response.status_code}: {response.text}")

    return response.json()["predictions"][0]["embeddings"]["values"]

# ----------------------------
# Text Generation logic for Gemini Flash
# ----------------------------
def call_vertex_generation_api(prompt: str, token: str):
    url = (
        f"https://{LOCATION}-aiplatform.googleapis.com/v1/projects/{PROJECT_ID}"
        f"/locations/{LOCATION}/publishers/google/models/{GENERATION_MODEL_ID}:generateContent"
    )

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.7,
            "topK": 40,
            "topP": 1.0,
            "maxOutputTokens": 512
        }
    }

    response = requests.post(url, headers=headers, json=payload)
    return response

def generate_answer(prompt: str) -> str:
    token = get_access_token()
    response = call_vertex_generation_api(prompt, token)

    if response.status_code == 401:
        token = get_access_token()
        response = call_vertex_generation_api(prompt, token)

    if response.status_code != 200:
        raise Exception(f"[Text Generation] Error {response.status_code}: {response.text}")

    try:
        return response.json()["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        raise Exception(f"[Text Generation] Failed to parse response: {e} - Full: {response.text}")
