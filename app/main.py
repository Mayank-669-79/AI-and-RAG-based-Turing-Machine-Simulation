"""FastAPI application entry point.

The integration router is added by Member 6. Until that folder is merged,
the health endpoint remains available so the base repository can be checked.
"""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from api_integration.routes import router as integration_router
from api_integration.response_formatter import format_error_response
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Natural Language Turing Machine Simulator",
    description=(
        "Translate supported natural-language language conditions into "
        "validated deterministic Turing Machines and simulate them."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:8000",
        "http://localhost:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", tags=["health"])
def health_check() -> dict[str, str]:
    """Simple health check for local development and deployment."""
    return {"status": "ok"}


@app.exception_handler(RequestValidationError)
async def request_validation_handler(request: Request, exc: RequestValidationError):
    errors = [
        {"location": list(error["loc"]), "message": error["msg"], "type": error["type"]}
        for error in exc.errors()
    ]
    return JSONResponse(status_code=422, content=format_error_response(
        "INVALID_REQUEST", "Request validation failed.", {"errors": errors}
    ))


@app.exception_handler(StarletteHTTPException)
async def http_error_handler(request: Request, exc: StarletteHTTPException):
    code = {404: "NOT_FOUND", 405: "METHOD_NOT_ALLOWED"}.get(exc.status_code, "HTTP_ERROR")
    message = exc.detail if isinstance(exc.detail, str) else "HTTP request failed."
    return JSONResponse(status_code=exc.status_code, headers=exc.headers,
                        content=format_error_response(code, message))


app.include_router(integration_router)
