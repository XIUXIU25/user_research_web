import os
from pymongo import MongoClient, ASCENDING
from typing import Dict, Any, List, Tuple
from huggingface_hub import InferenceClient
from dotenv import load_dotenv

from elasticsearch import Elasticsearch

ES_HOST = os.getenv("ES_HOST", "http://localhost:9200")
ES_INDEX = os.getenv("ES_INDEX", "projects")

es = Elasticsearch(ES_HOST)

load_dotenv()

PROJECT_MONGO_URI = os.getenv("PROJECT_MONGO_URI", "mongodb://root:example@localhost:27018/")
PROJECT_DB_NAME = os.getenv("PROJECT_DB_NAME", "project")
PROJECT_COLLECTION = os.getenv("PROJECT_COLLECTION", "projects")
HF_TOKEN = os.getenv("HF_TOKEN")


client = InferenceClient(
    provider="nebius",
    api_key=HF_TOKEN,
)


project_client = MongoClient(PROJECT_MONGO_URI)
projects_col = project_client[PROJECT_DB_NAME][PROJECT_COLLECTION]

def normalize_project(p: Dict[str, Any]) -> Dict[str, Any]:
    """Match your example project schema exactly."""
    guide = p.get("interviewGuide") or []
    if isinstance(guide, str):
        guide = [guide]
    guide = [str(q) for q in guide]

    return {
        "_id": p.get("_id"),  # ObjectId
        "name": p.get("name"),
        "interviewGuide": guide,
        "estimatedInterviewDuration": p.get("estimatedInterviewDuration"),
        "createdAt": p.get("createdAt"),
        "updatedAt": p.get("updatedAt"),
    }


def getProjects():
    projects_raw = list(projects_col.find({}))
    if not projects_raw:
        print("No projects found in mongo-project.")
        return

    return [normalize_project(p) for p in projects_raw]

def getEmbeddings(projects):
    embeddings = []

    for project in projects:
        embedding = client.feature_extraction(
            project["name"],
            model="Qwen/Qwen3-Embedding-8B"
        )
        embeddings.append(embedding)

    return embeddings

def saveToES(projects, embeddings):
    es.indices.create(
        index=ES_INDEX,
        mappings ={
            "properties": {
                "name": {"type": "text"},
                "interviewGuide": {"type": "text"},
                "embedding": {"type": "dense_vector", "dims": len(embeddings[0][0])},
                "estimatedInterviewDuration": {"type": "integer"},
                "createdAt": {"type": "date"},
                "updatedAt": {"type": "date"},
            }
        }
    )

    for project, embedding in zip(projects, embeddings):
        doc = {
            "name": project["name"],
            "interviewGuide": project["interviewGuide"],
            "estimatedInterviewDuration": project.get("estimatedInterviewDuration"),
            "createdAt": project.get("createdAt"),
            "updatedAt": project.get("updatedAt"),
            "embedding": embedding[0].tolist(),
        }
        es.index(index=ES_INDEX, id=str(project["_id"]), document=doc)


def main():
    # 1. fetch all projects from mongodb
    projects = getProjects()
    # 2. get projects' embedding by HF API
    embeddings = getEmbeddings(projects)

    print(embeddings)

    # # 3 save project and embeddings to ES
    saveToES(projects, embeddings)


if __name__ == "__main__":
    main()