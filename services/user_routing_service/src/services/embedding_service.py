from services.user_routing_service.src.clients.hf_client import embed_text

MAX_CHARS = 8000

async def embed_transcript(interviewHistories):
    # Concatenate all transcripts into one string
    transcript = "\n".join(doc.get("transcript", "") for doc in interviewHistories)
    return await embed_text(transcript)