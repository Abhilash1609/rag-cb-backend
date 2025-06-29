import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 1. Local development - load from secrets/.env if present
local_env_path = os.path.join(BASE_DIR, "..", "secrets", ".env")
if os.path.exists(local_env_path):
    load_dotenv(dotenv_path=local_env_path)

# 2. Cloud Run - load from mounted Secret Manager volume
cloudrun_secret_path = "/etc/secrets/rag-cb-secret"
if os.getenv("GOOGLE_CLOUD_ENV") == "cloudrun" and os.path.exists(cloudrun_secret_path):
    load_dotenv(dotenv_path=cloudrun_secret_path)

# 3. For local only: convert relative path to absolute path
if os.getenv("GOOGLE_CLOUD_ENV") != "cloudrun":
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if credentials_path:
        project_root = os.path.abspath(os.path.join(BASE_DIR, ".."))
        abs_credentials_path = os.path.join(project_root, credentials_path)
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = abs_credentials_path

# GCP
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
GCP_LOCATION = os.getenv("GCP_LOCATION", "us-central1")

# Qdrant
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

def get_env_variable(name: str) -> str:
    value = os.getenv(name)
    if value is None:
        raise EnvironmentError(f"Required environment variable '{name}' not found.")
    return value
