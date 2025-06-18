from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance, PayloadSchemaType
from app.config import get_env_variable

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
    existing_collections = [c.name for c in client.get_collections().collections]

    # ✅ user_chats: 3072-dim dummy vector
    if "user_chats" not in existing_collections:
        client.recreate_collection(
            collection_name="user_chats",
            vectors_config=VectorParams(size=3072, distance=Distance.COSINE),  # fixed dimension
            on_disk_payload=True
        )
        client.create_payload_index("user_chats", "user_id", PayloadSchemaType.KEYWORD)
        client.create_payload_index("user_chats", "chat_id", PayloadSchemaType.KEYWORD)
        client.create_payload_index("user_chats", "chat_title", PayloadSchemaType.KEYWORD)

    # ✅ chat_messages: real 3072-dim vectors
    if "chat_messages" not in existing_collections:
        client.recreate_collection(
            collection_name="chat_messages",
            vectors_config=VectorParams(size=3072, distance=Distance.COSINE),
            on_disk_payload=True
        )
        client.create_payload_index("chat_messages", "user_id", PayloadSchemaType.KEYWORD)
        client.create_payload_index("chat_messages", "chat_id", PayloadSchemaType.KEYWORD)


def search_similar_docs(collection_name: str, query_vector: list[float], top_k: int = 3):
    return client.search(
        collection_name=collection_name,
        query_vector=query_vector,
        limit=top_k
    )
