import asyncio

import uvicorn
from fastapi import FastAPI, Request
from fastapi.concurrency import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.api.routers import router
from app.core.config import settings
from app.core.db import create_database_if_not_exists, master_db_engine
from app.core.base_model import Base
from logs.logging import logger

# Determines the environment based on the settings
ENV = settings.environment

# Disable documentation if in production
if ENV == "production":
    app = FastAPI(docs_url=None, redoc_url=None, root_path=settings.base_path)
else:
    app = FastAPI(title=settings.app_name, version=settings.app_version,
                  description="Code_Arena API documentation",
                  swagger_ui_parameters={"persistAuthorization": True},
                  root_path=settings.base_path
                  )

'''
=====================================================
# Middleware setup things happens here
=====================================================
'''
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allows all headers
)

# Middleware to enforce root_path
def path_conversion(path):
    if settings.base_path == "/":
        return path
    else:
        return settings.base_path + path

@app.middleware("http")
async def enforce_root_path(request: Request, call_next):
    if not request.url.path.startswith(settings.base_path):
        return RedirectResponse(url=path_conversion(request.url.path))
    return await call_next(request)


def include_router(router):
    """
    Include the router in the FastAPI app.
    """
    app.include_router(router)


# Include the router
include_router(router)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure the database exists before starting the application
    if create_database_if_not_exists():
        logger.info('[*] Database created successfully ✅')
    else:
        logger.info('[*] Database already exists')

    async with master_db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        logger.info('[*] PostgreSQL Database connected successfully.✅')
    yield

    logger.info('[*] Database disconnected successfully.✅')

app.router.lifespan_context = lifespan


if __name__ == "__main__":
    if ENV != "production":
        uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
    else:
        uvicorn.run("main:app", host="0.0.0.0", port=8000, workers=4)
