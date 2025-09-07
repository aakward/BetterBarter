from difflib import SequenceMatcher

def is_nearby(postal1: str, postal2: str, level: int = 3) -> bool:
    """Check if two postal codes are 'nearby' based on first N digits."""
    if not postal1 or not postal2:
        return False
    return postal1[:level] == postal2[:level]

def score_match(offer, request):
    """
    Score a potential match based on subcategory, title similarity, and pin code proximity.
    Returns 0 if subcategory doesn't match.
    """
    weights = {
        "subcategory" : 0.4,
        "title": 0.35,
        "pincode": 0.25
    }
    score = 0.0
    if offer.get("subcategory") == request.get("subcategory"):
        score += weights["subcategory"]

    # Title similarity
    title1 = offer.get("title", "").lower()
    title2 = request.get("title", "").lower()
    if title1 and title2:
        seq_ratio = SequenceMatcher(None, title1, title2).ratio()  # 0-1
        score += weights["title"] * seq_ratio

    # Pin code proximity
    if is_nearby(offer.get("postal_code"), request.get("postal_code")):
        score += weights["pincode"]

    return score
