import logging
from typing import Dict, Any
from app.schemas.request import TicketRequest
from app.schemas.response import TicketResponse
from app.services.reasoning_service import ReasoningService
from app.services.llm_service import LLMService
from app.services.safety_service import SafetyService

logger = logging.getLogger("app.investigation_service")

class InvestigationService:
    @staticmethod
    async def investigate(request: TicketRequest) -> TicketResponse:
        """
        Coordinates the entire ticket analysis pipeline.
        1. Runs deterministic reasoning.
        2. Clean complaint & check prompt injections.
        3. Calls LLM to generate summaries and replies.
        4. Runs safety post-processing on LLM outputs.
        5. Formulates and returns the final TicketResponse.
        """
        # 1. Deterministic reasoning
        facts = ReasoningService.analyze_ticket(request)
        
        # Check prompt injection
        is_injection = SafetyService.detect_prompt_injection(request.complaint)
        if is_injection:
            logger.warning(f"Potential prompt injection detected in ticket {request.ticket_id}")
            # If prompt injection is detected, we can force the verdict to "insufficient_data" or case_type to "other",
            # or just let it go through but overwrite the output completely with fallback templates to guarantee safety.
            facts["case_type"] = "other"
            facts["evidence_verdict"] = "insufficient_data"
            facts["human_review_required"] = False
            facts["reason_codes"].append("prompt_injection_blocked")
            # Bypass LLM call entirely for prompt injection to prevent LLM exploitation/leakage
            llm_output = {
                "agent_summary": "Potential prompt injection detected in customer complaint. LLM generation bypassed for safety.",
                "recommended_next_action": "",
                "customer_reply": ""
            }
        else:
            # 2. Call LLM for summarization & drafting
            llm_output = await LLMService.generate_response(
                ticket_id=request.ticket_id,
                complaint=request.complaint,
                user_type=request.user_type,
                channel=request.channel,
                transaction_history=request.transaction_history or [],
                facts=facts
            )

        # 3. Handle fallbacks if LLM failed to generate
        agent_summary = llm_output.get("agent_summary", "").strip()
        recommended_next_action = llm_output.get("recommended_next_action", "").strip()
        customer_reply = llm_output.get("customer_reply", "").strip()

        # Fallbacks for empty summaries
        if not agent_summary:
            tx_id_str = facts["relevant_transaction_id"] or "N/A"
            if facts["case_type"] == "phishing_or_social_engineering":
                agent_summary = "Customer reports an unsolicited call claiming to be from the company and asking for OTP. Likely social engineering attempt."
            elif facts["evidence_verdict"] == "insufficient_data":
                agent_summary = f"Customer reports a vague concern without specifying transaction or issue. Insufficient detail to identify relevant transaction."
            else:
                agent_summary = f"Customer reports issue with transaction {tx_id_str}. Case classified as {facts['case_type']} with verdict {facts['evidence_verdict']}."

        # If LLM response fields are empty or fail safety checks
        # 4. Enforce strict safety guardrails
        safe_reply, safe_next_action = SafetyService.validate_and_sanitize_outputs(
            reply=customer_reply or "",
            next_action=recommended_next_action or "",
            case_type=facts["case_type"],
            tx_id=facts["relevant_transaction_id"],
            lang=facts["language"]
        )

        # Determine confidence
        confidence = 0.90
        reason_codes = facts["reason_codes"]
        
        if "ambiguous_match" in reason_codes:
            confidence = 0.65
        elif "empty_history" in reason_codes or "vague_complaint" in reason_codes:
            confidence = 0.60
        elif facts["case_type"] == "phishing_or_social_engineering":
            confidence = 0.95
        elif facts["evidence_verdict"] == "inconsistent":
            confidence = 0.75
        elif facts["evidence_verdict"] == "consistent":
            confidence = 0.90

        # Construct response
        response = TicketResponse(
            ticket_id=request.ticket_id,
            relevant_transaction_id=facts["relevant_transaction_id"],
            evidence_verdict=facts["evidence_verdict"],
            case_type=facts["case_type"],
            severity=facts["severity"],
            department=facts["department"],
            agent_summary=agent_summary,
            recommended_next_action=safe_next_action,
            customer_reply=safe_reply,
            human_review_required=facts["human_review_required"],
            confidence=confidence,
            reason_codes=reason_codes
        )

        return response
