import os
from dotenv import load_dotenv
from io import StringIO

# Loading local .env during development
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOCAL_ENV_PATH = os.path.join(BASE_DIR, "..", "secrets", ".env")

if os.path.exists(LOCAL_ENV_PATH):
    load_dotenv(dotenv_path=LOCAL_ENV_PATH)

# Loading secret-based env vars if in Cloud Run
if os.getenv("GOOGLE_CLOUD_ENV") == "cloudrun":
    secret_env = os.getenv("ENV_CONFIG")
    if secret_env:
        load_dotenv(stream=StringIO(secret_env))

# Setting GOOGLE_APPLICATION_CREDENTIALS abs path only locally
if os.getenv("GOOGLE_CLOUD_ENV") != "cloudrun":
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if credentials_path:
        project_root = os.path.abspath(os.path.join(BASE_DIR, ".."))
        abs_path = os.path.join(project_root, credentials_path)
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = abs_path

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
