from services.user_routing_service.src.clients.es_client import knn_search

async def get_recommendations(vector, interviewHistories, top_k=1):
    # Convert NumPy array (or nested array) into a plain list
    if hasattr(vector, "tolist"):
        vector = vector.tolist()

    hits = await knn_search(vector)

    # Filter out hits already in interviewHistories
    existing_ids = {str(doc["projectId"]) for doc in interviewHistories}
    hits = [h for h in hits if str(h["_id"]) not in existing_ids]

    # Return top_k hits
    result = [{"id": h["_id"], "score": h["_score"], "source": h["_source"]} for h in hits[:top_k]] if hits else None

    return result