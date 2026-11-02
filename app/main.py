from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pymongo.errors import DuplicateKeyError, PyMongoError

from app.config import settings
from app.database import create_client, ensure_indexes
from app.errors import InvalidListenError, ListenNotFoundError
from app.routes.listens import router


def create_app(collection=None):
    @asynccontextmanager
    async def lifespan(application):
        if collection is not None:
            application.state.collection = collection
            yield
            return
        client = create_client()
        try:
            client.admin.command("ping")
            application.state.collection = client[settings.database_name][settings.collection_name]
            ensure_indexes(application.state.collection)
            yield
        finally:
            client.close()

    application = FastAPI(title="ListenBrainz REST API", version="1.0.0", lifespan=lifespan)
    application.include_router(router)

    @application.exception_handler(InvalidListenError)
    async def invalid_listen_error(request: Request, error: InvalidListenError):
        return JSONResponse(status_code=400, content={"detail": str(error)})

    @application.exception_handler(ListenNotFoundError)
    async def missing_listen_error(request: Request, error: ListenNotFoundError):
        return JSONResponse(status_code=404, content={"detail": str(error)})

    @application.exception_handler(DuplicateKeyError)
    async def duplicate_error(request: Request, error: DuplicateKeyError):
        return JSONResponse(status_code=400, content={"detail": "Duplicate listen"})

    @application.exception_handler(PyMongoError)
    async def database_error(request: Request, error: PyMongoError):
        return JSONResponse(status_code=503, content={"detail": "Database operation unavailable"})

    return application


app = create_app()
