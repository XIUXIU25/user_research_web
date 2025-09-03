from pymongo import MongoClient
from services.user_routing_service.src.config.settings import settings

client = MongoClient(settings.MONGO_URI)
db = client[settings.MONGO_DB]
interview_collection = db[settings.MONGO_COLLECTION]