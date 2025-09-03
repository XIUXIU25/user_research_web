from fastapi import APIRouter
from services.user_routing_service.src.controllers.recommendations_controller import recommendations

router = APIRouter()
router.get("/recommendations")(recommendations)