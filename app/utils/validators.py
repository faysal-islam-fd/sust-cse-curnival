import re
from typing import List

# Mapping of Bengali digits to English digits
BANGLA_DIGIT_MAP = {
    '০': '0', '১': '1', '২': '2', '৩': '3', '৪': '4',
    '৫': '5', '৬': '6', '৭': '7', '৮': '8', '৯': '9'
}

def normalize_bangla_digits(text: str) -> str:
    """
    Replaces all Bengali digits in a string with their English equivalents.
    """
    if not text:
        return ""
    result = []
    for char in text:
        if char in BANGLA_DIGIT_MAP:
            result.append(BANGLA_DIGIT_MAP[char])
        else:
            result.append(char)
    return "".join(result)

def extract_numbers(text: str) -> List[float]:
    """
    Extracts all numerical values from text (handling both English and Bengali digits).
    Examples: 5000, 1,200 (parsed as 1200), etc.
    """
    normalized = normalize_bangla_digits(text)
    # Remove commas between digits to handle formats like 1,200 or 15,000
    cleaned = re.sub(r'(\d),(\d)', r'\1\2', normalized)
    # Extract digit sequences, optionally with decimals
    matches = re.findall(r'\d+(?:\.\d+)?', cleaned)
    
    numbers = []
    for m in matches:
        try:
            numbers.append(float(m))
        except ValueError:
            pass
    return numbers

def detect_language(text: str) -> str:
    """
    Simple check to guess if text is primarily 'bn', 'en', or 'mixed'.
    If it contains Bengali characters, it's 'bn' or 'mixed'.
    """
    if not text:
        return "en"
    # Bengali unicode block: U+0980 to U+09FF
    has_bangla = any('\u0980' <= char <= '\u09ff' for char in text)
    # Check if there are English words as well
    has_english = any('a' <= char.lower() <= 'z' for char in text)
    
    if has_bangla and has_english:
        return "mixed"
    elif has_bangla:
        return "bn"
    return "en"
