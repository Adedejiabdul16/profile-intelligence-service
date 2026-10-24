from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .database import engine
from .classify import classify_name
from .profile_service import ExternalAPIError
from .routers import profiles


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()


app = FastAPI(
    title="Profile Intelligence Service",
    description="Stage 0, Stage 1, and Stage 2 backend assignment",
    version="2.0.0",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    for error in exc.errors():
        location = error.get("loc", ())
        error_type = error.get("type")

        if "name" in location:
            if error_type == "missing":
                return JSONResponse(
                    status_code=400,
                    content={
                        "status": "error",
                        "message": "Name is required",
                    },
                )

            return JSONResponse(
                status_code=422,
                content={
                    "status": "error",
                    "message": "Name must be a string",
                },
            )

    return JSONResponse(
        status_code=422,
        content={
            "status": "error",
            "message": "Invalid query parameters",
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(
    request: Request,
    exc: HTTPException,
):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": str(exc.detail),
        },
        headers=exc.headers,
    )


@app.exception_handler(ExternalAPIError)
async def external_api_exception_handler(
    request: Request,
    exc: ExternalAPIError,
):
    return JSONResponse(
        status_code=502,
        content={
            "status": "502",
            "message": str(exc),
        },
    )


@app.exception_handler(RuntimeError)
async def runtime_error_handler(
    request: Request,
    exc: RuntimeError,
):
    return JSONResponse(
        status_code=502,
        content={
            "status": "error",
            "message": str(exc),
        },
    )


@app.exception_handler(Exception)
async def unexpected_exception_handler(
    request: Request,
    exc: Exception,
):
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal server error",
        },
    )


@app.get("/api/classify")
async def get_user(name: str):
    if not name.strip():
        raise HTTPException(
            status_code=400,
            detail="Name cannot be empty",
        )

    return await classify_name(name)


app.include_router(profiles.router)


@app.get("/")
async def root():
    return {
        "status": "success",
        "message": "Profile Intelligence Service is running",
    }
