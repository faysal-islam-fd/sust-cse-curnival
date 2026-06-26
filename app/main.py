import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app.api.routes import router
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("app.main")

app = FastAPI(
    title="QueueStorm Investigator",
    description="AI-powered SupportOps Copilot for Digital Finance Complaint Investigation",
    version="1.0.0"
)

# GET & HEAD /health endpoint
@app.get("/health", status_code=status.HTTP_200_OK)
@app.head("/health", status_code=status.HTTP_200_OK)
async def health():
    return {"status": "ok"}

# GET & HEAD / (root) endpoint
@app.get("/", status_code=status.HTTP_200_OK)
@app.head("/", status_code=status.HTTP_200_OK)
async def root():
    return {"message": "QueueStorm Investigator API is running. Check /health for status."}

# Register routes
app.include_router(router)

# Custom exception handlers matching the API contract
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handles validation errors.
    - Returns 400 for missing fields, missing body, or json syntax errors.
    - Returns 422 for semantically invalid fields (e.g. invalid enums).
    """
    errors = exc.errors()
    logger.warning(f"Validation error: {errors}")

    # Determine if it's a malformed/missing field error (400) or semantic validation error (422)
    is_missing_or_type_error = False
    error_messages = []
    
    for err in errors:
        loc = " -> ".join(str(l) for l in err.get("loc", []))
        msg = err.get("msg", "Invalid value")
        err_type = err.get("type", "")
        
        error_messages.append(f"{loc}: {msg}")
        
        # If a field is missing, or the entire body is missing/malformed, or JSON decoding fails
        if "missing" in err_type or "type_error" in err_type or "parsing" in err_type or "json" in err_type or err.get("loc") == ("body",):
            is_missing_or_type_error = True

    status_code = status.HTTP_400_BAD_REQUEST if is_missing_or_type_error else status.HTTP_422_UNPROCESSABLE_ENTITY
    
    return JSONResponse(
        status_code=status_code,
        content={
            "detail": "Validation failed",
            "errors": error_messages
        }
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Handles standard HTTP exceptions.
    """
    logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(Exception)
async def universal_exception_handler(request: Request, exc: Exception):
    """
    Catches all unexpected exceptions and returns a generic 500 response.
    Never exposes stack traces, secrets, or internal paths.
    """
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected internal server error occurred. Please try again later."}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
