from bson import ObjectId
from services.user_routing_service.src.clients.mongo_client import interview_collection

interview_cache = {}

async def fetch_latest_interview_history(user_id: str):
    try:
        query = {"userId": ObjectId(user_id)}
    except Exception:
        query = {"userId": user_id}

    docs = list(interview_collection.find(query))
    
    return docs