"""FastAPI endpoints for machine generation and simulation."""

from functools import lru_cache
import logging

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.schemas import ConditionRequest, RunRequest

from api_integration.service import MachineService
from api_integration.response_formatter import format_error_response


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/machine",
    tags=["machine"],
)


@lru_cache(maxsize=1)
def get_service() -> MachineService:
    """Create the service using the shared module implementations."""

    from nlp_interpreter import interpret_condition
    from rag_pipeline import retrieve_context
    from rule_parser import parse_rules, validate_machine

    dependencies = {
        "interpret_condition": interpret_condition,
        "retrieve_context": retrieve_context,
        "parse_rules": parse_rules,
        "validate_machine": validate_machine,
    }
    for name, dependency in dependencies.items():
        if not callable(dependency):
            raise TypeError(f"Integration dependency {name} is not callable.")

    return MachineService(
        interpreter=interpret_condition,
        retriever=retrieve_context,
        parser=parse_rules,
        validator=validate_machine,
    )


def get_service_dependency():
    """Handle unavailable integration dependencies."""

    try:
        return get_service()

    except Exception as exc:
        logger.exception(
            "Integration dependency initialization failed (%s).",
            type(exc).__name__,
        )

        return None


def make_response(result: dict) -> JSONResponse:
    """Convert service results into HTTP responses."""

    if result.get("success") is True:
        return JSONResponse(
            status_code=200,
            content=result,
        )

    error_code = result.get("error", {}).get("code")

    status_codes = {
        "INVALID_CONDITION": 400,
        "INVALID_ALPHABET": 400,
        "INVALID_INPUT": 400,
        "INVALID_INPUT_SYMBOL": 400,
        "INVALID_STEP_LIMIT": 400,
        "ALPHABET_MISMATCH": 400,
        "AMBIGUOUS_CONDITION": 422,
        "MACHINE_BUILD_ERROR": 422,
        "INTERPRETATION_ERROR": 500,
        "MACHINE_VALIDATION_ERROR": 500,
        "EXECUTION_ERROR": 500,
        "INTERNAL_ERROR": 500,
        "RETRIEVAL_ERROR": 503,
        "SERVICE_UNAVAILABLE": 503,
    }

    return JSONResponse(
        status_code=status_codes.get(error_code, 500),
        content=result,
    )


@router.post("/generate")
def generate_machine(
    request: ConditionRequest,
    service=Depends(get_service_dependency),
):
    """Generate a validated Turing Machine."""

    if service is None:
        return make_response(
            format_error_response(
                "SERVICE_UNAVAILABLE",
                "Integration dependencies are unavailable.",
            )
        )

    result = service.generate_machine(
        condition=request.condition,
        alphabet=request.alphabet,
    )

    return make_response(result)


@router.post("/run")
def simulate_machine(
    request: RunRequest,
    service=Depends(get_service_dependency),
):
    """Generate and execute a Turing Machine."""

    if service is None:
        return make_response(
            format_error_response(
                "SERVICE_UNAVAILABLE",
                "Integration dependencies are unavailable.",
            )
        )

    result = service.simulate_machine(
        condition=request.condition,
        input_string=request.input_string,
        alphabet=request.alphabet,
        max_steps=request.max_steps,
    )

    return make_response(result)