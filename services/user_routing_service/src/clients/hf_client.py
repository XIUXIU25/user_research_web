import os
from services.user_routing_service.src.config.settings import settings
import numpy as np
from huggingface_hub import InferenceClient

client = InferenceClient(
    provider="nebius",
    api_key=settings.HF_API_TOKEN,
)

async def embed_text(text: str) -> list[float]:
    result = client.feature_extraction(
        text,
        model=settings.HF_MODEL,
    )
    arr = np.array(result).squeeze()
    return arr.tolist()