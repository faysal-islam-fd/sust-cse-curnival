import json
import logging
import httpx
from typing import Dict, Any, Optional
from app.config import settings
from app.prompts.investigator_prompt import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from app.utils.json_parser import extract_json_from_text

logger = logging.getLogger("app.llm_service")

class LLMService:
    @staticmethod
    async def generate_response(
        ticket_id: str,
        complaint: str,
        user_type: Optional[str],
        channel: Optional[str],
        transaction_history: list,
        facts: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Sends the complaint, transaction history, and analysis facts to the LLM via OpenRouter.
        Returns a dict with 'agent_summary', 'recommended_next_action', and 'customer_reply'.
        """
        api_key = settings.OPENROUTER_API_KEY
        model_name = settings.MODEL_NAME
        
        # Format transaction history for prompt
        tx_list_str = []
        for tx in transaction_history:
            tx_dict = tx.model_dump() if hasattr(tx, "model_dump") else tx
            tx_list_str.append(json.dumps(tx_dict, indent=2))
        transaction_history_str = "\n".join(tx_list_str) if tx_list_str else "No recent transactions."

        # Format prompts
        system_content = SYSTEM_PROMPT.format(
            relevant_transaction_id=facts["relevant_transaction_id"] or "None",
            case_type=facts["case_type"],
            evidence_verdict=facts["evidence_verdict"],
            severity=facts["severity"],
            department=facts["department"],
            language=facts["language"]
        )
        
        user_content = USER_PROMPT_TEMPLATE.format(
            ticket_id=ticket_id,
            user_type=user_type or "unknown",
            channel=channel or "unknown",
            complaint=complaint,
            transaction_history_str=transaction_history_str
        )

        # Fallback dictionary if LLM is disabled or fails
        fallback_data = {
            "agent_summary": "",
            "recommended_next_action": "",
            "customer_reply": ""
        }

        if not api_key:
            logger.warning("OPENROUTER_API_KEY is not set. Using rule-based fallback generation.")
            return fallback_data

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/sust-cse-carnival/queuestorm-investigator",
            "X-Title": "QueueStorm Investigator"
        }

        data = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_content}
            ],
            "temperature": 0.1,  # Low temperature for highly deterministic/factual outputs
            "response_format": {"type": "json_object"}
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    f"{settings.OPENROUTER_BASE_URL}/chat/completions",
                    headers=headers,
                    json=data
                )
                response.raise_for_status()
                response_json = response.json()
                
                # Check choices
                choices = response_json.get("choices")
                if not choices:
                    raise ValueError("No choices returned from LLM API")
                
                content = choices[0]["message"]["content"]
                parsed_response = extract_json_from_text(content)
                
                # Validate the dictionary contains expected fields
                result = {}
                for key in ["agent_summary", "recommended_next_action", "customer_reply"]:
                    result[key] = str(parsed_response.get(key, "")).strip()
                
                return result

        except Exception as e:
            logger.error(f"Error communicating with LLM service: {str(e)}. Triggering safe fallback.")
            return fallback_data
