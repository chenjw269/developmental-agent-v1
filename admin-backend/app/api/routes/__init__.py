from fastapi import APIRouter
from app.api.routes import applications, credentials, internal, dashboard

api_router = APIRouter(prefix="/api/v1", tags=["api"])
api_router.include_router(applications.router, prefix="/applications", tags=["applications"])
api_router.include_router(credentials.router, prefix="/credentials", tags=["credentials"])
api_router.include_router(internal.router, prefix="/internal", tags=["internal"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
