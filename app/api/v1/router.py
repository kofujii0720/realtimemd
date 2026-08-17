from fastapi import APIRouter
from app.api.v1.api_0102 import router as documents_router

api_v1_router = APIRouter()
api_v1_router.include_router(documents_router)
