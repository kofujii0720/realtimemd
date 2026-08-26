from fastapi import APIRouter
from app.api.v1.api_0101 import router as documents_list_router
from app.api.v1.api_0102 import router as documents_create_router
from app.api.v1.api_0103 import router as documents_update_router
from app.api.v1.api_0104 import router as documents_delete_router
from app.api.v1.api_0105 import router as documents_detail_router
from app.api.v1.api_0201 import router as preview_render_router
from app.api.v1.api_0301 import router as export_router

api_v1_router = APIRouter()
api_v1_router.include_router(documents_list_router)
api_v1_router.include_router(documents_create_router)
api_v1_router.include_router(documents_update_router)
api_v1_router.include_router(documents_delete_router)
api_v1_router.include_router(documents_detail_router)
api_v1_router.include_router(preview_render_router)
api_v1_router.include_router(export_router)


