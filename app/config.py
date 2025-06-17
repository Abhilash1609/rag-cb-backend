import os
from dotenv import load_dotenv

# Load environment variables from secrets/.env
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, "..", "secrets", ".env")
load_dotenv(dotenv_path=ENV_PATH)

# Set GOOGLE_APPLICATION_CREDENTIALS explicitly (important for subprocesses or libs that don't re-read env)
credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
if credentials_path:
    # Use abspath directly from project root (not from app/)
    project_root = os.path.abspath(os.path.join(BASE_DIR, ".."))
    abs_credentials_path = os.path.join(project_root, credentials_path)
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = abs_credentials_path

# GCP Config
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
GCP_LOCATION = os.getenv("GCP_LOCATION", "us-central1")

# Qdrant Config
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

def get_env_variable(name: str) -> str:
    """
    Fetch a required environment variable or raise an error if not found.
    """
    value = os.getenv(name)
    if value is None:
        raise EnvironmentError(f"Required environment variable '{name}' not found.")
    return value
