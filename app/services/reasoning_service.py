import re
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
from app.schemas.request import TicketRequest, Transaction
from app.utils.validators import normalize_bangla_digits, extract_numbers, detect_language
from app.config import settings

class ReasoningService:
    @staticmethod
    def analyze_ticket(request: TicketRequest) -> Dict[str, Any]:
        """
        Determines the structural analysis fields deterministically using rules.
        Returns a dict of analysis facts.
        """
        complaint = request.complaint.strip()
        history = request.transaction_history or []
        
        # 1. Normalize and detect language
        normalized_complaint = normalize_bangla_digits(complaint).lower()
        detected_lang = request.language or detect_language(complaint)
        
        # 2. Determine case type by keyword and history checks
        case_type = ReasoningService._classify_case_type(normalized_complaint, request.user_type, history)
        
        # 3. Find relevant transaction
        relevant_tx, verdict, reason_codes = ReasoningService._match_transaction(
            normalized_complaint, history, case_type
        )
        
        # Adjust case_type based on matched transaction if necessary
        if relevant_tx:
            if relevant_tx.status == "failed" and case_type not in ("phishing_or_social_engineering", "duplicate_payment"):
                case_type = "payment_failed"
            elif relevant_tx.type == "settlement" and relevant_tx.status == "pending":
                case_type = "merchant_settlement_delay"
            elif relevant_tx.type == "cash_in" and relevant_tx.status == "pending":
                case_type = "agent_cash_in_issue"
        
        # If duplicate payment is claimed and confirmed
        if "duplicate_payment" in reason_codes:
            case_type = "duplicate_payment"
            
        # 4. Determine department and human review required
        department, human_review = ReasoningService._determine_routing_and_review(
            case_type, verdict, relevant_tx
        )
        
        # 5. Determine severity
        severity = ReasoningService._determine_severity(case_type, verdict, relevant_tx)
        
        # Extract relevant ID
        relevant_transaction_id = relevant_tx.transaction_id if relevant_tx else None
        
        return {
            "relevant_transaction_id": relevant_transaction_id,
            "evidence_verdict": verdict,
            "case_type": case_type,
            "severity": severity,
            "department": department,
            "human_review_required": human_review,
            "reason_codes": reason_codes,
            "language": detected_lang
        }

    @staticmethod
    def _classify_case_type(text: str, user_type: Optional[str], history: List[Transaction]) -> str:
        """
        Classifies the complaint into a case_type enum based on keywords and user type.
        """
        # Phishing checks (highest priority for safety)
        phishing_words = [
            "otp", "pin", "password", "passward", "card number", "cvv", "caller", "call center",
            "block", "scam", "phishing", "fraud", "পিন", "ওটিপি", "পাসওয়ার্ড", "কার্ড নম্বর",
            "লক", "ব্লক", "প্রতারক", "মিথ্যা কল"
        ]
        if any(w in text for w in phishing_words):
            # Check if someone is asking for credentials
            if any(req in text for req in ["ask", "demand", "share", "চাই", "বলুন", "চেয়েছে", "জিজ্ঞেস"]):
                return "phishing_or_social_engineering"
            return "phishing_or_social_engineering"

        # Duplicate payment check
        dup_words = ["duplicate", "twice", "double", "two times", "double charge", "দুইবার", "২ বার", "ডাবল", "কেটেছে"]
        if any(w in text for w in dup_words):
            return "duplicate_payment"

        # Merchant settlement check
        settlement_words = ["settlement", "settle", "sales", "merchant account", "সেটেলমেন্ট", "সেটেল", "বিক্রি", "মার্চেন্ট"]
        if user_type == "merchant" or any(w in text for w in settlement_words):
            return "merchant_settlement_delay"

        # Agent cash-in check
        agent_words = ["agent", "cash in", "cash-in", "deposit", "এজেন্ট", "ক্যাশ ইন", "ক্যাশ-ইন"]
        if any(w in text for w in agent_words) and "cash" in text or "টাকা" in text:
            return "agent_cash_in_issue"

        # Failed payment check
        failed_words = ["failed", "fail", "deducted", "recharge", "electricity", "bill", "ব্যর্থ", "ফেইল", "কেটেছে", "রিচার্জ", "বিল"]
        if any(w in text for w in failed_words):
            return "payment_failed"

        # Wrong transfer check
        wrong_words = ["wrong", "wrong number", "wrong recipient", "wrong person", "mistake", "ভুল", "ভুল নম্বর", "ভুল নাম্বার", "ভুল সেন্ড"]
        if any(w in text for w in wrong_words):
            return "wrong_transfer"

        # Refund request check
        refund_words = ["refund", "return money", "change mind", "cancel", "রিফান্ড", "ফেরত"]
        if any(w in text for w in refund_words):
            return "refund_request"

        return "other"

    @staticmethod
    def _match_transaction(
        text: str, history: List[Transaction], case_type: str
    ) -> Tuple[Optional[Transaction], str, List[str]]:
        """
        Matches a complaint to a specific transaction in the history.
        Returns (Matched Transaction, Verdict, Reason Codes).
        """
        if not history:
            # If history is empty, phishing and other safety cases are fine
            if case_type == "phishing_or_social_engineering":
                return None, "insufficient_data", ["phishing", "critical_escalation"]
            return None, "insufficient_data", ["empty_history", "vague_complaint"]

        reason_codes = []

        # 1. Match by explicit Transaction ID
        for tx in history:
            tx_id_lower = tx.transaction_id.lower()
            if tx_id_lower in text:
                reason_codes.append("explicit_tx_id_match")
                # Now verify if consistent
                verdict = ReasoningService._verify_consistency(tx, text, case_type, history)
                if verdict == "inconsistent":
                    reason_codes.append("evidence_inconsistent")
                else:
                    reason_codes.append("transaction_match")
                return tx, verdict, reason_codes

        # 2. Match by Amount
        extracted_amounts = extract_numbers(text)
        if not extracted_amounts:
            # Check if there's only one transaction in history, maybe it refers to it
            if len(history) == 1:
                tx = history[0]
                verdict = ReasoningService._verify_consistency(tx, text, case_type, history)
                reason_codes.extend(["single_tx_history", "assumed_match"])
                return tx, verdict, reason_codes
            return None, "insufficient_data", ["no_amounts_extracted", "vague_complaint"]

        # Find transactions whose amount matches any extracted amounts
        matched_txs = []
        for amt in extracted_amounts:
            for tx in history:
                # Allow a small float margin or exact matches
                if abs(tx.amount - amt) < 0.01:
                    matched_txs.append(tx)

        # De-duplicate matches
        matched_txs = list({tx.transaction_id: tx for tx in matched_txs}.values())

        if not matched_txs:
            return None, "insufficient_data", ["no_matching_amount_in_history"]

        # 3. Handle duplicate payments
        if case_type == "duplicate_payment" or "duplicate" in text or "দুইবার" in text:
            # Look for duplicate transactions: same amount, same type, same counterparty, within 5 minutes (300 seconds)
            # Sort matched transactions by timestamp
            sorted_history = sorted(history, key=lambda x: x.timestamp)
            for i in range(len(sorted_history) - 1):
                tx1 = sorted_history[i]
                tx2 = sorted_history[i+1]
                if (tx1.amount == tx2.amount and 
                    tx1.type == tx2.type and 
                    tx1.counterparty == tx2.counterparty and
                    tx1.status == "completed" and 
                    tx2.status == "completed"):
                    # Check time difference
                    try:
                        t1 = datetime.fromisoformat(tx1.timestamp.replace('Z', '+00:00'))
                        t2 = datetime.fromisoformat(tx2.timestamp.replace('Z', '+00:00'))
                        diff = abs((t2 - t1).total_seconds())
                        if diff <= 300: # 5 minutes
                            # The second one is the duplicate
                            reason_codes.extend(["duplicate_payment", "transaction_match"])
                            return tx2, "consistent", reason_codes
                    except Exception:
                        # Fallback if timestamp parsing fails: just assume the second one in sequence is the duplicate
                        reason_codes.extend(["duplicate_payment", "transaction_match"])
                        return tx2, "consistent", reason_codes

        # 4. Handle unique match
        if len(matched_txs) == 1:
            tx = matched_txs[0]
            verdict = ReasoningService._verify_consistency(tx, text, case_type, history)
            reason_codes.append("transaction_match")
            if verdict == "inconsistent":
                reason_codes.append("evidence_inconsistent")
            return tx, verdict, reason_codes

        # 5. Multiple matches: Check if we can disambiguate by transaction type
        # E.g. if the complaint is about a wrong transfer, filter matching transfers
        filtered_by_type = []
        target_types = []
        if case_type == "wrong_transfer":
            target_types = ["transfer"]
        elif case_type == "payment_failed":
            target_types = ["payment"]
        elif case_type == "agent_cash_in_issue":
            target_types = ["cash_in"]
        elif case_type == "merchant_settlement_delay":
            target_types = ["settlement"]

        if target_types:
            filtered_by_type = [tx for tx in matched_txs if tx.type in target_types]

        if len(filtered_by_type) == 1:
            tx = filtered_by_type[0]
            verdict = ReasoningService._verify_consistency(tx, text, case_type, history)
            reason_codes.append("transaction_match")
            if verdict == "inconsistent":
                reason_codes.append("evidence_inconsistent")
            return tx, verdict, reason_codes

        # Still ambiguous
        reason_codes.append("ambiguous_match")
        return None, "insufficient_data", reason_codes

    @staticmethod
    def _verify_consistency(tx: Transaction, text: str, case_type: str, history: List[Transaction]) -> str:
        """
        Determines whether the matched transaction is consistent or inconsistent with the complaint.
        """
        # Case 1: Wrong transfer check - check established recipient pattern
        if case_type == "wrong_transfer" or "wrong" in text or "ভুল" in text:
            # Count how many completed transfers have been made to this counterparty in the past
            counterparty = tx.counterparty
            prior_transfers = [
                t for t in history 
                if t.counterparty == counterparty 
                and t.type == "transfer" 
                and t.status == "completed"
                and t.timestamp < tx.timestamp
            ]
            if len(prior_transfers) >= 2:
                # Established relationship, makes wrong transfer claim highly inconsistent
                return "inconsistent"
            return "consistent"

        # Case 2: Failed payment check
        if case_type == "payment_failed" or "fail" in text or "ব্যর্থ" in text:
            if tx.status == "failed":
                return "consistent"
            elif tx.status == "completed":
                # User claims failed but it's completed in history -> inconsistent
                return "inconsistent"

        # Case 3: Merchant settlement delay
        if case_type == "merchant_settlement_delay":
            if tx.status == "pending":
                return "consistent"
            return "inconsistent"

        # Case 4: Agent cash-in issue
        if case_type == "agent_cash_in_issue":
            if tx.status == "pending":
                return "consistent"
            return "inconsistent"

        # Default consistent
        return "consistent"

    @staticmethod
    def _determine_routing_and_review(
        case_type: str, verdict: str, tx: Optional[Transaction]
    ) -> Tuple[str, bool]:
        """
        Determines department and human_review_required based on enums and rules.
        """
        # Department mapping
        if case_type == "wrong_transfer":
            dept = "dispute_resolution"
        elif case_type == "payment_failed":
            dept = "payments_ops"
        elif case_type == "refund_request":
            # Default to customer_support unless it's inconsistent/contested
            dept = "dispute_resolution" if verdict == "inconsistent" else "customer_support"
        elif case_type == "duplicate_payment":
            dept = "payments_ops"
        elif case_type == "merchant_settlement_delay":
            dept = "merchant_operations"
        elif case_type == "agent_cash_in_issue":
            dept = "agent_operations"
        elif case_type == "phishing_or_social_engineering":
            dept = "fraud_risk"
        else:
            dept = "customer_support"

        # Human Review Required rules
        if case_type == "phishing_or_social_engineering":
            review = True
        elif verdict == "insufficient_data":
            # For vague/ambiguous complaints, we ask customer for clarification. No human review yet.
            review = False
        elif verdict == "inconsistent":
            # Discrepancy between data and user claim always requires human review.
            review = True
        elif case_type in ("wrong_transfer", "duplicate_payment", "agent_cash_in_issue"):
            # These are disputes or cash issues that require operations actions.
            review = True
        elif tx and tx.amount >= settings.HIGH_VALUE_THRESHOLD:
            # High value transactions require human review
            review = True
        else:
            review = False

        return dept, review

    @staticmethod
    def _determine_severity(case_type: str, verdict: str, tx: Optional[Transaction]) -> str:
        """
        Determines severity based on case type, verdict, and transaction amount.
        """
        if case_type == "phishing_or_social_engineering":
            return "critical"
            
        amount = tx.amount if tx else 0.0
        
        # High value check
        if amount >= settings.HIGH_VALUE_THRESHOLD:
            return "high"

        if case_type == "wrong_transfer":
            return "high" if verdict == "consistent" else "medium"
        elif case_type == "duplicate_payment":
            return "high"
        elif case_type == "payment_failed":
            return "high" if verdict == "consistent" else "medium"
        elif case_type == "agent_cash_in_issue":
            return "high" if verdict == "consistent" else "medium"
        elif case_type == "merchant_settlement_delay":
            return "medium"
        elif case_type == "refund_request":
            return "low"
        
        return "low"
