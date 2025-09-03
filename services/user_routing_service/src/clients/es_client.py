from services.user_routing_service.src.config.settings import settings
from elasticsearch import AsyncElasticsearch

es = AsyncElasticsearch(hosts=[settings.ES_URL])

async def knn_search(vector: list[float], k: int = 6, num_candidates: int = 100):
    body = {
        "knn": {
            "field": "embedding",
            "query_vector": vector,
            "k": k,
            "num_candidates": num_candidates
        },
        "_source": {"excludes": ["embedding"]}
    }
    resp = await es.search(index=settings.ES_INDEX, body=body)
    return resp["hits"]["hits"]