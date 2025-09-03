import hashlib
from fastapi import FastAPI, Request
import httpx

# List of backend servers (replicas of user_routing_service)
USER_ROUTING_SERVERS = [
    "http://localhost:8080",
    "http://localhost:8081",
    "http://localhost:8082"
]

app = FastAPI(title="Gateway with Consistent Hashing")

def get_server_for_user(user_id: str) -> str:
    # Compute hash of user_id
    h = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
    # Map to one of the servers
    idx = h % len(USER_ROUTING_SERVERS)
    return USER_ROUTING_SERVERS[idx]

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy(request: Request, path: str):
    # Extract userId header
    user_id = request.headers.get("userId")
    if not user_id:
        return {"error": "Missing userId header"}

    target_server = get_server_for_user(user_id)
    url = f"{target_server}/{path}"

    async with httpx.AsyncClient() as client:
        body = await request.body()
        headers = dict(request.headers)
        resp = await client.request(
            request.method,
            url,
            content=body,
            headers=headers,
            params=request.query_params,
        )
        return resp.json() if "application/json" in resp.headers.get("content-type", "") else resp.text