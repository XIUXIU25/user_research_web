from fastapi import FastAPI
from services.user_routing_service.src.routes.recommendations_routes import router as reco_router
from services.user_routing_service.src.config.settings import settings

app = FastAPI(title="User Recommendation API")

app.include_router(reco_router)

# for docker run
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=settings.PORT, reload=True)