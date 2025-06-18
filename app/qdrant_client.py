from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance
from app.config import get_env_variable
from qdrant_client.http.models import PayloadSchemaType

QDRANT_URL = get_env_variable("QDRANT_URL")
QDRANT_API_KEY = get_env_variable("QDRANT_API_KEY")

client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY
)

def init_qdrant_collection(collection_name: str = "chatbot_chunks", vector_size: int = 3072):
    if collection_name not in [c.name for c in client.get_collections().collections]:
        client.recreate_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
        )

def init_user_collections():
    # user_chats: stores user_id -> chat_id (can have multiple)
    if "user_chats" not in [c.name for c in client.get_collections().collections]:
        client.recreate_collection(
            collection_name="user_chats",
            vectors_config=VectorParams(size=1, distance=Distance.COSINE),  # dummy vector
            on_disk_payload=True,
            optimizers_config=None,
        )

    # chat_messages: stores messages linked to chat_id
    if "chat_messages" not in [c.name for c in client.get_collections().collections]:
        client.recreate_collection(
            collection_name="chat_messages",
            vectors_config=VectorParams(size=1, distance=Distance.COSINE),  # dummy vector
            on_disk_payload=True,
            optimizers_config=None,
        )

def search_similar_docs(collection_name: str, query_vector: list[float], top_k: int = 3):
    return client.search(
        collection_name=collection_name,
        query_vector=query_vector,
        limit=top_k
    )
