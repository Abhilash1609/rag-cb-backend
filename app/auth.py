# app/auth.py
from google.oauth2 import id_token
from google.auth.transport import requests

def verify_google_token(id_token_str: str) -> str:
    try:
        idinfo = id_token.verify_oauth2_token(id_token_str, requests.Request())
        return idinfo["sub"]  # Unique user ID
    except Exception as e:
        raise ValueError(f"Invalid token: {e}")
