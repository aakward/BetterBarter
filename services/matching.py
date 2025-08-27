from sqlalchemy.orm import Session
from data import models

def is_nearby(postal1: str, postal2: str, level: int = 3) -> bool:
    """Check if two postal codes are 'nearby' based on first N digits."""
    if not postal1 or not postal2:
        return False
    return postal1[:level] == postal2[:level]

def find_matches_for_user(db: Session, user_id: int, max_results: int = 10, proximity_level: int = 2):
    """
    Find potential matches for a user:
    - Match user's offers to other users' requests
    - Match user's requests to other users' offers
    Returns a list of dictionaries with details for UI.
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        return []

    matches = []

    # --- Match offers to requests ---
    for offer in user.offers:
        potential_requests = (
            db.query(models.Request)
            .filter(models.Request.user_id != user_id)
            .filter(models.Request.title.ilike(f"%{offer.title}%"))
            .all()
        )
        for req in potential_requests:
            score = 1.0 if is_nearby(user.postal_code, req.user.postal_code, level=proximity_level) else 0.5
            matches.append({
                "offer_title": offer.title,
                "offer_user_name": user.name,
                "offer_postal": user.postal_code,
                "request_title": req.title,
                "request_user_name": req.user.name,
                "request_postal": req.user.postal_code,
                "score": score
            })

    # --- Match requests to offers ---
    for req in user.requests:
        potential_offers = (
            db.query(models.Offer)
            .filter(models.Offer.user_id != user_id)
            .filter(models.Offer.title.ilike(f"%{req.title}%"))
            .all()
        )
        for offer in potential_offers:
            score = 1.0 if is_nearby(user.postal_code, offer.user.postal_code, level=proximity_level) else 0.5
            matches.append({
                "offer_title": offer.title,
                "offer_user_name": offer.user.name,
                "offer_postal": offer.user.postal_code,
                "request_title": req.title,
                "request_user_name": user.name,
                "request_postal": user.postal_code,
                "score": score
            })

    # Sort matches by score descending
    matches.sort(key=lambda x: x["score"], reverse=True)
    return matches[:max_results]
