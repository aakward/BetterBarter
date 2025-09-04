from data.ui_models import UIMatch
from datetime import datetime
from utils.helpers import parse_datetime

def _normalize_status(status) -> str:
    if status is None:
        return "unknown"
    if hasattr(status, "value"):  # Enum
        return status.value
    return str(status)


def build_ui_match_from_match(match: dict):
    offer = match.get("offer")
    request = match.get("request")

    return UIMatch(
        id=match["id"],
        offer_id=match.get("offer_id"),
        request_id=match.get("request_id"),
        offer_description=offer["description"] if offer else None,
        request_description=request["description"] if request else None,
        offer_image=offer.get("image_file_name") if offer else None,
        request_image=request.get("image_file_name") if request else None,
        status=_normalize_status(match.get("status")),  # string from Supabase
        created_at=parse_datetime(match.get("created_at")),
    )


def build_ui_match_from_match_request(mr: dict) -> UIMatch:
    offer = mr.get("offers")  # because of the alias in select
    request = mr.get("requests")

    offer_profile = None
    request_profile = None
    if offer:
        offer_profile = offer.get("profiles")
    if request:
        request_profile = request.get("profiles")

    return UIMatch(
        id=mr["id"],
        offer_id=mr.get("offer_id"),
        request_id=mr.get("request_id"),
        offer_description=offer.get("description") if offer else None,
        request_description=request.get("description") if request else None,
        offer_image=offer.get("image_file_name") if offer else None,
        request_image=request.get("image_file_name") if request else None,
        status=_normalize_status(mr.get("status")),
        created_at=parse_datetime(mr.get("created_at")),
        message=mr.get("message"),
        initiator_id=mr.get("requester_id"),
        responder_id=mr.get("offerer_id"),

        # enriched fields
        offer_title=offer.get("title") if offer else None,
        request_title=request.get("title") if request else None,
        offer_user_name=offer_profile.get("full_name") if offer_profile else None,
        request_user_name=request_profile.get("full_name") if request_profile else None,
        offer_postal=offer_profile.get("postal_code") if offer_profile else None,
        request_postal=request_profile.get("postal_code") if request_profile else None,
    )




def build_ui_match_from_offer_request_pair(offer: dict, request: dict) -> UIMatch:
    """
    Build a UIMatch object from an offer and request dict returned by Supabase.
    Both dicts are enriched with profile data in get_potential_matches.
    """
    return UIMatch(
        id=None,  # potential matches don’t exist yet in match_requests
        offer_id=offer.get("id"),
        request_id=request.get("id"),
        offer_description=offer.get("description"),
        request_description=request.get("description"),
        offer_image=offer.get("image_file_name"),
        request_image=request.get("image_file_name"),
        status="potential",
        created_at=datetime.utcnow(),

        # enriched fields
        offer_title=offer.get("title"),
        request_title=request.get("title"),
        offer_user_name=offer.get("profiles", {}).get("full_name"),
        request_user_name=request.get("profiles", {}).get("full_name"),
        offer_postal=offer.get("profiles", {}).get("postal_code"),
        request_postal=request.get("profiles", {}).get("postal_code"),

        # unused for potential matches
        message=None,
        initiator_id=None,
        responder_id=None,
    )
