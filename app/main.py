"""FastAPI application entry point.

The integration router is added by Member 6. Until that folder is merged,
the health endpoint remains available so the base repository can be checked.
"""

from fastapi import FastAPI
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


# Member 6 should import and register api_integration.routes.router here
# after that module has been added to the repository.
try:
    from api_integration.routes import router as integration_router
except ImportError:
    integration_router = None

if integration_router is not None:
    app.include_router(integration_router)
