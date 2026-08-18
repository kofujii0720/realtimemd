from fastapi import APIRouter
from app.api.v1.api_0102 import router as documents_create_router
from app.api.v1.api_0103 import router as documents_update_router

api_v1_router = APIRouter()
api_v1_router.include_router(documents_create_router)
api_v1_router.include_router(documents_update_router)

