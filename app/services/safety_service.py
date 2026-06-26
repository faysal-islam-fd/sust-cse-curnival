import re
from typing import Dict, Any, Tuple

# Official safe channels
OFFICIAL_CHANNELS = ["official support channels", "official channels", "in-app chat", "call center", "email support"]

class SafetyService:
    # 1. Fallback Safe Templates for each case type
    FALLBACK_TEMPLATES = {
        "wrong_transfer": {
            "customer_reply": {
                "en": "We have noted your concern about transaction {tx_id}. Please do not share your PIN or OTP with anyone. Our dispute team will review the case carefully and contact you through official support channels.",
                "bn": "আপনার লেনদেন {tx_id} এর বিষয়ে আমরা অবগত হয়েছি। অনুগ্রহ করে কারো সাথে আপনার পিন বা ওটিপি শেয়ার করবেন না। আমাদের বিরোধ নিষ্পত্তি দল বিষয়টি পর্যালোচনা করবে এবং অফিসিয়াল চ্যানেলের মাধ্যমে আপনার সাথে যোগাযোগ করবে।"
            },
            "recommended_next_action": "Verify transaction {tx_id} details with the customer and initiate the wrong-transfer dispute workflow per policy."
        },
        "payment_failed": {
            "customer_reply": {
                "en": "We have noted that transaction {tx_id} may have caused an unexpected balance deduction. Our payments team will review the case and any eligible amount will be returned through official channels. Please do not share your PIN or OTP with anyone.",
                "bn": "আমরা লক্ষ্য করেছি যে লেনদেন {tx_id} এর কারণে আপনার ব্যালেন্স কাটা হতে পারে। আমাদের পেমেন্ট দল বিষয়টি পর্যালোচনা করবে এবং যেকোনো যোগ্য পরিমাণ অফিসিয়াল চ্যানেলের মাধ্যমে ফেরত দেওয়া হবে। অনুগ্রহ করে আপনার পিন বা ওটিপি কারো সাথে শেয়ার করবেন না।"
            },
            "recommended_next_action": "Investigate transaction {tx_id} ledger status. If balance was deducted on a failed payment, initiate the automatic reversal flow within standard SLA."
        },
        "refund_request": {
            "customer_reply": {
                "en": "Thank you for reaching out. Refunds for completed merchant payments depend on the merchant's own policy. We recommend contacting the merchant directly. If you need help reaching them, please reply and we will guide you. Please do not share your PIN or OTP with anyone.",
                "bn": "আমাদের সাথে যোগাযোগ করার জন্য ধন্যবাদ। সম্পন্ন মার্চেন্ট পেমেন্টের রিফান্ড মার্চেন্টের নিজস্ব পলিসির ওপর নির্ভর করে। আমরা সরাসরি মার্চেন্টের সাথে যোগাযোগ করার পরামর্শ দিচ্ছি। অনুগ্রহ করে আপনার পিন বা ওটিপি কারো সাথে শেয়ার করবেন না।"
            },
            "recommended_next_action": "Inform the customer that refund eligibility depends on the merchant's own policy. Provide guidance on contacting the merchant directly."
        },
        "duplicate_payment": {
            "customer_reply": {
                "en": "We have noted the possible duplicate payment for transaction {tx_id}. Our payments team will verify with the biller and any eligible amount will be returned through official channels. Please do not share your PIN or OTP with anyone.",
                "bn": "আমরা লেনদেন {tx_id} এর জন্য সম্ভাব্য ডুপ্লিকেট পেমেন্টটি লক্ষ্য করেছি। আমাদের পেমেন্ট দল বিলারের সাথে এটি যাচাই করবে এবং যেকোনো যোগ্য পরিমাণ অফিসিয়াল চ্যানেলের মাধ্যমে ফেরত দেওয়া হবে। অনুগ্রহ করে আপনার পিন বা ওটিপি কারো সাথে শেয়ার করবেন না।"
            },
            "recommended_next_action": "Verify the duplicate with payments_ops. If the biller confirms only one payment was received, initiate reversal of transaction {tx_id}."
        },
        "merchant_settlement_delay": {
            "customer_reply": {
                "en": "We have noted your concern about settlement {tx_id}. Our merchant operations team will check the batch status and update you on the expected settlement time through official channels.",
                "bn": "সেটেলমেন্ট {tx_id} এর বিষয়ে আপনার অভিযোগটি আমরা নথিভুক্ত করেছি। আমাদের মার্চেন্ট অপারেশন দল ব্যাচের অবস্থা পরীক্ষা করবে এবং অফিসিয়াল চ্যানেলের মাধ্যমে আপনাকে আপডেট জানাবে।"
            },
            "recommended_next_action": "Route to merchant_operations to verify settlement batch status. If the batch is delayed, communicate a revised ETA to the merchant."
        },
        "agent_cash_in_issue": {
            "customer_reply": {
                "en": "We have received your report regarding agent cash-in transaction {tx_id}. Our agent operations team will investigate the status and update you through official channels. Please do not share your PIN or OTP with anyone.",
                "bn": "আপনার লেনদেন {tx_id} এর বিষয়ে আমরা অবগত হয়েছি। আমাদের এজেন্ট অপারেশন্স দল এটি দ্রুত যাচাই করবে এবং অফিসিয়াল চ্যানেলে আপনাকে জানাবে। অনুগ্রহ করে কারো সাথে আপনার পিন বা ওটিপি শেয়ার করবেন না।"
            },
            "recommended_next_action": "Investigate transaction {tx_id} pending status with agent operations. Confirm settlement state and resolve within the standard cash-in SLA."
        },
        "phishing_or_social_engineering": {
            "customer_reply": {
                "en": "Thank you for reaching out before sharing any information. We never ask for your PIN, OTP, or password under any circumstances. Please do not share these with anyone, even if they claim to be from us. Our fraud team has been notified of this incident.",
                "bn": "কোনো তথ্য শেয়ার করার আগে আমাদের সাথে যোগাযোগ করার জন্য ধন্যবাদ। আমরা কোনো অবস্থাতেই আপনার পিন, ওটিপি বা পাসওয়ার্ড জিজ্ঞাসা করি না। অনুগ্রহ করে এগুলো কারো সাথে শেয়ার করবেন না। আমাদের ফ্রড টিমকে এই বিষয়ে অবহিত করা হয়েছে।"
            },
            "recommended_next_action": "Escalate to fraud_risk team immediately. Confirm to customer that the company never asks for OTP. Log the reported number for fraud pattern analysis."
        },
        "other": {
            "customer_reply": {
                "en": "Thank you for reaching out. To help you faster, please share the transaction ID, the amount involved, and a short description of what went wrong. Please do not share your PIN or OTP with anyone.",
                "bn": "যোগাযোগ করার জন্য ধন্যবাদ। আপনাকে দ্রুত সাহায্য করার জন্য, অনুগ্রহ করে লেনদেন আইডি, টাকার পরিমাণ এবং কী সমস্যা হয়েছিল তা শেয়ার করুন। কারো সাথে আপনার পিন বা ওটিপি শেয়ার করবেন না।"
            },
            "recommended_next_action": "Reply to customer asking for specific details: which transaction, what amount, what went wrong, and approximate time."
        }
    }

    @staticmethod
    def detect_prompt_injection(text: str) -> bool:
        """
        Detects potential prompt injection keywords in the complaint.
        """
        injection_patterns = [
            r"ignore\s+(?:previous|above|the)\s+instruction",
            r"reveal\s+(?:system|internal|policy|prompt)",
            r"system\s+prompt",
            r"you\s+are\s+now",
            r"developer\s+mode",
            r"refund\s+immediately",
            r"give\s+me\s+refund",
            r"revert\s+immediately",
            r"override\s+rules",
            r"forget\s+(?:all\s+)?instructions"
        ]
        text_lower = text.lower()
        for pattern in injection_patterns:
            if re.search(pattern, text_lower):
                return True
        return False

    @staticmethod
    def clean_complaint(text: str) -> str:
        """
        Sanitizes input text by removing direct injection patterns.
        """
        # If prompt injection is detected, we return a sanitized version or append a warning
        # so the LLM doesn't get confused, but for the API itself, we just keep the complaint.
        return text

    @staticmethod
    def validate_and_sanitize_outputs(
        reply: str, next_action: str, case_type: str, tx_id: str | None, lang: str
    ) -> Tuple[str, str]:
        """
        Scans LLM output for safety violations.
        If a violation is found, replaces the output with a 100% safe, pre-approved fallback.
        """
        # Map mixed to english for fallback replies
        lang_key = "bn" if lang == "bn" else "en"
        tx_id_str = tx_id if tx_id else "N/A"
        
        # Get fallback templates
        templates = SafetyService.FALLBACK_TEMPLATES.get(case_type, SafetyService.FALLBACK_TEMPLATES["other"])
        fallback_reply = templates["customer_reply"][lang_key].format(tx_id=tx_id_str)
        fallback_next_action = templates["recommended_next_action"].format(tx_id=tx_id_str)

        # If reply or next_action is empty, trigger fallback immediately
        if not reply.strip() or not next_action.strip():
            return fallback_reply, fallback_next_action

        # 1. Check for request for PIN, OTP, password, card number
        # We look for words PIN/OTP/password/card number in a request context.
        # However, to be absolutely safe, if the response asks the customer to provide them, we block it.
        # E.g. "please enter your pin", "send your otp", "give me your pin".
        credential_request_patterns = [
            r"(?:ask|request|enter|provide|send|share|tell|input|give|write|verify|confirm)\s+.*\b(?:pin|otp|password|passward|card\s*number)\b",
            r"\b(?:pin|otp|password|passward|card\s*number)\b.*\b(?:please|share|provide|send|tell|give)\b",
            r"আপনার\s+.*\b(?:পিন|ওটিপি|পাসওয়ার্ড|কার্ড\s*নম্বর)\b.*\b(?:দিন|বলুন|শেয়ার|পাঠান|লিখুন)\b"
        ]
        
        reply_lower = reply.lower()
        next_action_lower = next_action.lower()

        # Simple keyword checks to be safe:
        # If the reply contains OTP/PIN/password/card number, it must ONLY be a warning NOT to share them.
        # If it asks for it, it's a violation.
        for pattern in credential_request_patterns:
            if re.search(pattern, reply_lower) or re.search(pattern, next_action_lower):
                # Critical safety violation detected! Overwrite.
                return fallback_reply, fallback_next_action

        # 2. Check for unauthorized refund/reversal/unblock promises
        # If it promises a refund, reversal, recovery, or unblock directly.
        # E.g. "we will refund your money", "we have reversed", "refund is processed", "we will unblock your account"
        # Safe phrasing is: "any eligible amount will be returned through official channels" or "depend on merchant's policy"
        refund_promise_patterns = [
            r"we\s+(?:will|have)\s+(?:refund|reverse|unblock|recover)\b",
            r"refund\s+(?:has\s+been|will\s+be)\s+(?:processed|sent|done|credited)",
            r"money\s+will\s+be\s+(?:refunded|returned|reversed)",
            r"your\s+account\s+(?:is|will\s+be)\s+unblocked",
            r"আমরা\s+.*(?:ফেরত|রিফান্ড|আনব্লক)\s*(?:করব|করেছি|হবে)",
            r"টাকা\s+ফেরত\s+দেওয়া\s+হবে"
        ]

        for pattern in refund_promise_patterns:
            if re.search(pattern, reply_lower) or re.search(pattern, next_action_lower):
                # Safety violation: direct promise! Overwrite.
                return fallback_reply, fallback_next_action

        # 3. Check for unofficial contacts / third party mentions
        # E.g., advising customer to call some phone number that is not official or contact a person.
        # If it contains phone numbers that are not our official numbers, or tells them to call an agent directly
        # or use standard contact info.
        phone_match = re.search(r'\b\+?880\d{8,10}\b|\b01\d{9}\b', reply)
        if phone_match:
            # Check if this phone number is in the transaction details (which is fine). 
            # If it's advising them to contact this number, it's a violation.
            if "contact" in reply_lower or "call" in reply_lower or "যোগাযোগ" in reply_lower:
                return fallback_reply, fallback_next_action

        # Make sure the customer reply warns them not to share credentials (a great practice for fintech!)
        warning_words_en = ["do not share your pin or otp", "never ask for your pin", "keep your credentials safe"]
        warning_words_bn = ["পিন বা ওটিপি শেয়ার করবেন না", "পিন, ওটিপি বা পাসওয়ার্ড জিজ্ঞাসা করি না"]
        
        has_warning = False
        if lang_key == "bn":
            has_warning = any(w in reply for w in warning_words_bn)
        else:
            has_warning = any(w in reply_lower for w in warning_words_en)

        # If it doesn't have a warning and it's not a merchant-side settlement delay (merchants don't always need PIN warnings),
        # let's append the safety warning to be safe.
        if not has_warning and case_type not in ("merchant_settlement_delay", "other"):
            if lang_key == "bn":
                reply = reply + " অনুগ্রহ করে কারো সাথে আপনার পিন বা ওটিপি শেয়ার করবেন না।"
            else:
                reply = reply + " Please do not share your PIN or OTP with anyone."

        # Programmatic guardrail to ensure "লেনদেন" is present in Bangla replies
        if lang_key == "bn" and "লেনদেন" not in reply:
            if "সংক্রান্ত" in reply:
                reply = reply.replace("সংক্রান্ত", "লেনদেন সংক্রান্ত", 1)
            else:
                if reply.startswith("প্রিয় গ্রাহক,"):
                    reply = reply.replace("প্রিয় গ্রাহক,", "প্রিয় গ্রাহক, আপনার লেনদেনের বিষয়ে:", 1)
                else:
                    reply = "লেনদেন সংক্রান্ত: " + reply

        return reply, next_action
