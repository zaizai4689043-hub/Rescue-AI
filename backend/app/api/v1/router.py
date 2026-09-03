from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.disasters import router as disasters_router
from app.api.v1.resources import router as resources_router
from app.api.v1.volunteers import router as volunteers_router
from app.api.v1.assessments import router as assessments_router
from app.api.v1.trapped_persons import router as trapped_persons_router
from app.api.v1.users import router as users_router
from app.api.v1.map_data import router as map_data_router
from app.api.v1.ai_analysis import router as ai_analysis_router
from app.api.v1.ai_assistant import router as ai_assistant_router
from app.api.v1.social import router as social_router

router = APIRouter()

router.include_router(auth_router, prefix="")
router.include_router(disasters_router, prefix="/disasters")
router.include_router(resources_router, prefix="/resources")
router.include_router(volunteers_router, prefix="/volunteers")
router.include_router(assessments_router, prefix="/assessments")
router.include_router(trapped_persons_router, prefix="/trapped-persons")
router.include_router(users_router, prefix="/users")
router.include_router(map_data_router, prefix="/map-data")
router.include_router(ai_analysis_router, prefix="/ai-analysis")
router.include_router(ai_assistant_router, prefix="/ai-assistant")
router.include_router(social_router, prefix="/social")
