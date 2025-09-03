from fastapi import Request, HTTPException
from services.user_routing_service.src.services.interview_service import fetch_latest_interview_history
from services.user_routing_service.src.services.embedding_service import embed_transcript
from services.user_routing_service.src.services.recommendation_service import get_recommendations

recommendations_cache = {}

async def recommendations(request: Request):
    user_id = (
        request.headers.get("userId")
    )
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing userId header")
    
    # Return cached result if available
    if user_id in recommendations_cache:
        return recommendations_cache[user_id]

    interviewHistory = await fetch_latest_interview_history(user_id)
    vector = await embed_transcript(interviewHistory)
    projects = await get_recommendations(vector, interviewHistory)

    response = {"ok": True, "userId": user_id, "projects": projects}
    recommendations_cache[user_id] = response
    return response
