import logging
from fastapi import APIRouter, HTTPException, status
from app.schemas.request import TicketRequest
from app.schemas.response import TicketResponse
from app.services.investigation_service import InvestigationService

logger = logging.getLogger("app.routes")
router = APIRouter()

@router.post(
    "/analyze-ticket",
    response_model=TicketResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze a customer support ticket against transaction history"
)
async def analyze_ticket(request: TicketRequest):
    """
    Main analysis endpoint. Accepts the customer ticket and transaction history,
    performs deterministic reasoning and LLM-assisted drafting, and returns
    the structured investigation copilot response.
    """
    try:
        response = await InvestigationService.investigate(request)
        return response
    except Exception as e:
        logger.error(f"Error analyzing ticket {request.ticket_id}: {str(e)}", exc_info=True)
        # Avoid exposing stack traces in production
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected internal error occurred while processing the ticket."
        )
