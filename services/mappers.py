from data.ui_models import UIMatch
from datetime import datetime
from utils.helpers import parse_datetime
from data import crud_ipv4 as crud

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


def build_ui_match_from_match_request(mr: dict, db=None) -> UIMatch:
    offer = mr.get("offers")
    request = mr.get("requests")

    # --- Offer profile ---
    offer_profiles = offer.get("profiles") if offer else None
    if isinstance(offer_profiles, list):
        offer_profile = offer_profiles[0] if offer_profiles else None
    elif isinstance(offer_profiles, dict):
        offer_profile = offer_profiles
    elif mr.get("offerer_id") and db:
        offer_profile = crud.get_profile(db, mr["offerer_id"])
    else:
        offer_profile = None

    # --- Request profile ---
    request_profiles = request.get("profiles") if request else None
    if isinstance(request_profiles, list):
        request_profile = request_profiles[0] if request_profiles else None
    elif isinstance(request_profiles, dict):
        request_profile = request_profiles
    elif mr.get("requester_id") and db:
        request_profile = crud.get_profile(db, mr["requester_id"])
    else:
        request_profile = None

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
        requester_id=mr.get("requester_id"),
        offerer_id=mr.get("offerer_id"),

        # enriched fields
        offer_title=offer.get("title") if offer else None,
        request_title=request.get("title") if request else None,
        offer_user_name=offer_profile.get("full_name") if offer_profile else None,
        request_user_name=request_profile.get("full_name") if request_profile else None,
        offer_postal=offer_profile.get("postal_code") if offer_profile else None,
        request_postal=request_profile.get("postal_code") if request_profile else None,

        # contact info
        offerer_contact_mode=mr.get("offerer_contact_mode"),
        offerer_contact_value=mr.get("offerer_contact_value"),
        requester_contact_mode=mr.get("requester_contact_mode"),
        requester_contact_value=mr.get("requester_contact_value"),
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
    )



def get_profile(profile_data):
    if not profile_data:
        return None
    if isinstance(profile_data, list) and len(profile_data) > 0:
        return profile_data[0]
    if isinstance(profile_data, dict):
        return profile_data
    return None