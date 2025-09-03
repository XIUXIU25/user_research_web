import os

from dotenv import load_dotenv

load_dotenv()

class Settings:
    PORT: int = int(os.getenv("PORT", 8080))
    HF_API_TOKEN: str = os.getenv("HF_API_TOKEN")
    HF_MODEL: str = os.getenv("HF_EMBED_MODEL", "Qwen/Qwen3-Embedding-8B")

    MONGO_URI: str = os.getenv(
        "MONGO_INTERVIEW_URI",
        "mongodb://root:example@mongo-interview-history:27017/?authSource=admin"
    )
    MONGO_DB: str = os.getenv("MONGO_INTERVIEW_DB", "interview_history")
    MONGO_COLLECTION: str = os.getenv("MONGO_INTERVIEW_COLLECTION", "interview_histories")

    ES_URL: str = os.getenv("ES_URL", "http://elasticsearch:9200")
    ES_INDEX: str = os.getenv("ES_INDEX", "projects")

settings = Settings()