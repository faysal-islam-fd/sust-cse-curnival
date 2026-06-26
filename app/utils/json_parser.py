import json
import re
from typing import Any, Dict

def extract_json_from_text(text: str) -> Dict[str, Any]:
    """
    Extracts and parses the first JSON object found in the text.
    Handles markdown blocks and stray text.
    """
    if not text:
        raise ValueError("Empty text received for JSON parsing")

    cleaned_text = text.strip()
    
    # Try direct parsing first
    try:
        return json.loads(cleaned_text)
    except json.JSONDecodeError:
        pass

    # Regex to find text between ```json and ```
    json_block = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', cleaned_text)
    if json_block:
        try:
            return json.loads(json_block.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Fallback: find the first '{' and matching '}' or just the last '}'
    # This regex matches the first occurrence of '{' followed by everything up to the last '}'
    brace_match = re.search(r'(\{[\s\S]*\})', cleaned_text)
    if brace_match:
        try:
            return json.loads(brace_match.group(1).strip())
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not extract valid JSON from text: {text[:200]}...")
