from sqlalchemy.orm import Session
from data.models import Profile, Offer, Request

def is_nearby(postal1: str, postal2: str, level: int = 3) -> bool:
    """Check if two postal codes are 'nearby' based on first N digits."""
    if not postal1 or not postal2:
        return False
    return postal1[:level] == postal2[:level]

def find_matches_for_user(
    db: Session,
    profile_id: str,
    max_results: int = 10,
    proximity_level: int = 3
):
    """
    Find potential matches for a profile:
    - Match profile's offers to other profiles' requests
    - Match profile's requests to other profiles' offers
    Returns a list of dictionaries with details for UI.
    """
    profile = db.query(Profile).filter(Profile.id == profile_id).first()
    if not profile:
        return []

    matches = []

    # --- Match profile's offers to other profiles' requests ---
    for offer in profile.offers:
        potential_requests = (
            db.query(Request)
            .join(Profile, Profile.id == Request.profile_id)
            .filter(Request.profile_id != profile_id)
            .filter(Request.title.ilike(f"%{offer.title}%"))
            .all()
        )
        for req in potential_requests:
            score = 1.0 if is_nearby(profile.postal_code, req.profile.postal_code, level=proximity_level) else 0.5
            matches.append({
                "offer_title": offer.title,
                "offer_profile_name": profile.full_name,
                "offer_postal": profile.postal_code,
                "request_title": req.title,
                "request_profile_name": req.profile.full_name,
                "request_postal": req.profile.postal_code,
                "score": score
            })

    # --- Match profile's requests to other profiles' offers ---
    for req in profile.requests:
        potential_offers = (
            db.query(Offer)
            .join(Profile, Profile.id == Offer.profile_id)
            .filter(Offer.profile_id != profile_id)
            .filter(Offer.title.ilike(f"%{req.title}%"))
            .all()
        )
        for offer in potential_offers:
            score = 1.0 if is_nearby(profile.postal_code, offer.profile.postal_code, level=proximity_level) else 0.5
            matches.append({
                "offer_title": offer.title,
                "offer_profile_name": offer.profile.full_name,
                "offer_postal": offer.profile.postal_code,
                "request_title": req.title,
                "request_profile_name": profile.full_name,
                "request_postal": profile.postal_code,
                "score": score
            })

    # Sort matches by score descending
    matches.sort(key=lambda x: x["score"], reverse=True)
    return matches[:max_results]
