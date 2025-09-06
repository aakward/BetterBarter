from typing import Literal
from supabase import Client as SupabaseClient
from utils import auth, helpers
import datetime
from data.models import MatchStatus
from services.email_service import send_match_request_email, send_match_accepted_email
import streamlit as st

MAX_MATCH_REQUESTS_PER_DAY = 3  # adjustable
REQUEST_BUCKET_NAME = "request-images"
OFFER_BUCKET_NAME = "offer-images"

# -----------------------------
# Helper class to pass to email service
# -----------------------------
class UserEmailObj:
    def __init__(self, profile: dict):
        self.email = profile.get("email")
        self.name = profile.get("full_name")
        self.phone = profile.get("phone")  # optional, adjust if you store unhashed

# -----------------------------
# PROFILE CRUD
# -----------------------------
def create_profile(
    supabase_client: SupabaseClient,
    supabase_id: str,
    full_name: str,
    postal_code: str,
    phone: str = None,
    email: str = None,
    share_phone: bool = False
):
    response = supabase_client.table("profiles").insert({
        "id": supabase_id,
        "full_name": full_name,
        "postal_code": postal_code,
        "phone": phone,
        "email": email,
        "share_phone": share_phone,
        "karma": 1
    }).execute()

    return response.data[0] if response.data else None


def get_profile(supabase_client: SupabaseClient, profile_id: str):
    response = supabase_client.table("profiles").select("*").eq("id", profile_id).execute()
    return response.data[0] if response.data else None


def update_profile(supabase_client: SupabaseClient, profile_id: str, phone: str = None, share_phone: bool = None, **kwargs):
    update_data = kwargs.copy()
    if phone is not None:
        update_data["phone"] = phone
    if share_phone is not None:
        update_data["share_phone"] = share_phone

    response = supabase_client.table("profiles").update(update_data).eq("id", profile_id).execute()
    return response.data[0] if response.data else None


def delete_profile(supabase_client: SupabaseClient, profile_id: str):
    # Delete Supabase Auth user
    supabase_client.auth.admin.delete_user(profile_id)
    # Delete profile row
    response = supabase_client.table("profiles").delete().eq("id", profile_id).execute()
    return response.data[0] if response.data else None


# -----------------------------
# OFFER CRUD
# -----------------------------
def create_offer(supabase_client: SupabaseClient, profile_id: str, title: str, description: str = None, category: str = None, subcategory: str = None, image_file_name: str = None):
    offer_data = {
        "profile_id": profile_id,
        "title": title,
        "description": description,
        "category": category,
        "subcategory": subcategory,
        "is_active": True,
    }
    if image_file_name:
        offer_data["image_file_name"] = image_file_name
    response = supabase_client.table("offers").insert(offer_data).execute()

    # Increment karma
    add_karma(supabase_client, profile_id, points=3)

    return response.data[0] if response.data else None


def get_offers(supabase_client: SupabaseClient, exclude_profile_id: str = None, limit: int = 100):
    query = supabase_client.table("offers").select("*").limit(limit)
    if exclude_profile_id:
        query = query.neq("profile_id", exclude_profile_id)
    response = query.execute()
    return response.data


def update_offer(supabase_client: SupabaseClient, offer_id: int, **kwargs):
    response = supabase_client.table("offers").update(kwargs).eq("id", offer_id).execute()
    return response.data[0] if response.data else None


def delete_offer(supabase_client: SupabaseClient, offer_id: int):
    # Fetch offer
    resp = supabase_client.table("offers").select("*").eq("id", offer_id).execute()
    offers = resp.data or []
    if not offers:
        return None

    offer = offers[0]

    # Deduct karma
    add_karma(supabase_client, offer["profile_id"], points=-3)

    # Delete related match requests
    supabase_client.table("match_requests").delete().eq("offer_id", offer_id).execute()

    # Delete image from storage if exists
    image_file_name = offer.get("image_file_name")
    if image_file_name:
        try:
            supabase_client.storage.from_(OFFER_BUCKET_NAME).remove([image_file_name])
        except Exception as e:
            print(f"Warning: could not delete image {image_file_name}: {e}")

    # Delete the offer itself
    del_response = supabase_client.table("offers").delete().eq("id", offer_id).execute()
    return del_response.data[0] if del_response.data else None


def mark_offer_matched(supabase_client: SupabaseClient, offer_id: int):
    offer = supabase_client.table("offers").update({"is_active": False}).eq("id", offer_id).execute()
    if offer.data:
        add_karma(supabase_client, offer.data[0]["profile_id"], points=5)
    return offer.data[0] if offer.data else None


# -----------------------------
# REQUEST CRUD
# -----------------------------
def create_request(supabase_client: SupabaseClient, profile_id: str, title: str, description: str = None, category: str = None, subcategory: str = None, image_file_name: str = None):
    request_data = {
        "profile_id": profile_id,
        "title": title,
        "description": description,
        "category": category,
        "subcategory": subcategory,
        "is_active": True,
    }
    if image_file_name:
        request_data["image_file_name"] = image_file_name
    response = supabase_client.table("requests").insert(request_data).execute()
    add_karma(supabase_client, profile_id, points=1)
    return response.data[0] if response.data else None


def get_requests(supabase_client: SupabaseClient, exclude_profile_id: str = None, limit: int = 100):
    query = supabase_client.table("requests").select("*").limit(limit)
    if exclude_profile_id:
        query = query.neq("profile_id", exclude_profile_id)
    response = query.execute()
    return response.data


def update_request(supabase_client: SupabaseClient, request_id: int, **kwargs):
    response = supabase_client.table("requests").update(kwargs).eq("id", request_id).execute()
    return response.data[0] if response.data else None
    


def delete_request(supabase_client: SupabaseClient, request_id: int):
    # Fetch request
    resp = supabase_client.table("requests").select("*").eq("id", request_id).execute()
    requests = resp.data or []
    if not requests:
        return None

    req = requests[0]

    # Deduct karma
    add_karma(supabase_client, req["profile_id"], points=-1)

    # Delete related match requests
    supabase_client.table("match_requests").delete().eq("request_id", request_id).execute()

    # Delete image from storage if exists
    image_file_name = req.get("image_file_name")
    if image_file_name:
        try:
            supabase_client.storage.from_(REQUEST_BUCKET_NAME).remove([image_file_name])
        except Exception as e:
            print(f"Warning: could not delete image {image_file_name}: {e}")

    # Delete the request itself
    del_response = supabase_client.table("requests").delete().eq("id", request_id).execute()
    return del_response.data[0] if del_response.data else None


def mark_request_matched(supabase_client: SupabaseClient, request_id: int):
    request = supabase_client.table("requests").update({"is_active": False}).eq("id", request_id).execute()
    if request.data:
        add_karma(supabase_client, request.data[0]["profile_id"], points=5)
    return request.data[0] if request.data else None


# -----------------------------
# AUTHENTICATION via Supabase
# -----------------------------
def authenticate_user(supabase_client: SupabaseClient, email: str, password: str):
    response = supabase_client.auth.sign_in_with_password({"email": email, "password": password})
    return response.user if response.user else None


# -----------------------------
# Karma system helper
# -----------------------------
def add_karma(supabase_client: SupabaseClient, profile_id: str, points: int):
    profile = supabase_client.table("profiles").select("*").eq("id", profile_id).execute().data
    if profile:
        new_karma = (profile[0]["karma"] or 0) + points
        supabase_client.table("profiles").update({"karma": new_karma}).eq("id", profile_id).execute()
        return supabase_client.table("profiles").select("*").eq("id", profile_id).execute().data[0]
    return None


# -----------------------------
# Match Request CRUD
# -----------------------------

def can_send_match_request(supabase_client: SupabaseClient, requester_id: str) -> bool:
    today_start = datetime.datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    response = supabase_client.table("match_requests")\
        .select("*", count="exact")\
        .eq("requester_id", requester_id)\
        .gte("created_at", today_start)\
        .execute()
    return response.count < MAX_MATCH_REQUESTS_PER_DAY


def get_existing_match_request(
    supabase_client: SupabaseClient,
    initiator_id: str,
    request_id: int = None,
    offer_id: int = None
):
    """
    Checks if the given user has already created a match request for the same offer/request.
    """
    query = supabase_client.table("match_requests").select("*").eq("initiator_id", initiator_id)

    if request_id is not None:
        query = query.eq("request_id", request_id)
    if offer_id is not None:
        query = query.eq("offer_id", offer_id)

    resp = query.execute()
    return resp.data[0] if resp.data else None


def create_match_request(
    supabase_client: SupabaseClient,
    caller_id: str,
    offer_id: int = None,
    request_id: int = None,
    message: str = None,
    contact_mode: str = None,
    contact_value: str = None,
    initiator_type: Literal["request", "offer"] = "request",
):
    """
    Create a match request. Handles both:
    - Caller owns a request and wants an offer (initiator_type="request")
    - Caller owns an offer and wants to respond to a request (initiator_type="offer")
    """
    # --- Basic validations ---
    if not can_send_match_request(supabase_client, caller_id):
        raise Exception(f"Daily limit of {MAX_MATCH_REQUESTS_PER_DAY} match requests reached.")

    if not offer_id and not request_id:
        raise Exception("Either offer_id or request_id must be provided.")

    if not contact_mode or not contact_value:
        raise Exception("Contact mode and contact details must be provided.")

    requester_id = offerer_id = None

    if initiator_type == "request":
        # Caller is the requester, must provide target offer
        if not offer_id:
            raise Exception("offer_id must be provided when initiator_type='request'")
        requester_id = caller_id

        resp = supabase_client.table("offers").select("profile_id, is_active").eq("id", offer_id).execute()
        if not resp.data:
            raise Exception("Offer not found")
        if not resp.data[0].get("is_active", True):
            raise Exception("Cannot send a match request to a deactivated offer")
        offerer_id = resp.data[0]["profile_id"]

        if offerer_id == caller_id:
            raise Exception("Cannot send a match request to your own offer")
        
        initiator_id = caller_id  


    elif initiator_type == "offer":
        # Caller is the offerer, must provide target request
        if not request_id:
            raise Exception("request_id must be provided when initiator_type='offer'")
        offerer_id = caller_id

        resp = supabase_client.table("requests").select("profile_id, is_active").eq("id", request_id).execute()
        if not resp.data:
            raise Exception("Request not found")
        if not resp.data[0].get("is_active", True):
            raise Exception("Cannot send a match request to a deactivated request")
        requester_id = resp.data[0]["profile_id"]

        if requester_id == caller_id:
            raise Exception("Cannot send a match request to your own request")

        initiator_id = caller_id  

    else:
        raise Exception("Invalid initiator_type. Must be 'request' or 'offer'.")

    # --- Prevent duplicate match requests ---
    if get_existing_match_request(supabase_client, initiator_id=caller_id, request_id=request_id, offer_id=offer_id):
        raise Exception("You have already sent a match request here.")

    # --- Prepare match data ---
    match_data = {
        "requester_id": requester_id,
        "offerer_id": offerer_id,
        "initiator_id": initiator_id,  
        "request_id": request_id,
        "offer_id": offer_id,
        "message": message,
        "status": "pending",
        "created_at": datetime.datetime.utcnow().isoformat(),
        "notified": False,
        "requester_contact_mode": contact_mode if initiator_type == "request" else None,
        "requester_contact_value": contact_value if initiator_type == "request" else None,
        "offerer_contact_mode": contact_mode if initiator_type == "offer" else None,
        "offerer_contact_value": contact_value if initiator_type == "offer" else None,
    }

    # --- Insert into DB ---
    resp = supabase_client.table("match_requests").insert(match_data).execute()
    add_karma(supabase_client, caller_id, 1)

    # --- Send email notification ---
    if resp.data:
        caller_profile = get_profile(supabase_client, caller_id)
        other_profile = get_profile(
            supabase_client, 
            offerer_id if initiator_type == "request" else requester_id
        )

        if caller_profile and other_profile:
            send_match_request_email(
                receiver=UserEmailObj(other_profile),
                sender=UserEmailObj(caller_profile),
            )

    return resp.data[0] if resp.data else None





def get_match_requests_for_offer(supabase_client: SupabaseClient, offer_id: int, status: str = "pending"):
    resp = supabase_client.table("match_requests")\
        .select("*")\
        .eq("offer_id", offer_id)\
        .eq("status", status)\
        .execute()
    return resp.data


def get_sent_match_requests(db, profile_id: str, status: str = None):
    query = (
        db.table("match_requests")
        .select("*, offers:offer_id(*, profiles:profile_id(*)), requests:request_id(*, profiles:profile_id(*))")
        .eq("initiator_id", profile_id)  # only requests created by this user
    )
    if status:
        query = query.eq("status", status)

    resp = query.execute()
    filtered = [
        mr for mr in resp.data
        if (
            (mr.get("offers") and mr["offers"].get("is_active", True)) or
            (mr.get("requests") and mr["requests"].get("is_active", True))
        )
    ]
    return filtered


def get_incoming_match_requests(db, profile_id: str, status: str = None):
    query = (
        db.table("match_requests")
        .select("*, offers:offer_id(*, profiles:profile_id(*)), requests:request_id(*, profiles:profile_id(*))")
        .neq("initiator_id", profile_id)  # only requests initiated by someone else
        .or_(f"offerer_id.eq.{profile_id},requester_id.eq.{profile_id}")  # user is on the other side
    )
    if status:
        query = query.eq("status", status)

    resp = query.execute()
    filtered = [
        mr for mr in resp.data
        if (
            (mr.get("offers") and mr["offers"].get("is_active", True)) or
            (mr.get("requests") and mr["requests"].get("is_active", True))
        )
    ]
    return filtered



def update_match_request_status(
    supabase_client: SupabaseClient,
    match_request_id: int,
    status: str,
    profile_id: str,  # the one performing the action
    contact_mode: str = None,
    contact_value: str = None,
):
    """
    Updates the status of a match request.
    Updates the contact info of the accepter (offerer or requester).
    """
    status_str = status.value if isinstance(status, MatchStatus) else str(status)
    match_req_resp = supabase_client.table("match_requests").select("*").eq("id", match_request_id).execute()
    match_req = match_req_resp.data[0] if match_req_resp.data else None
    if not match_req:
        return None

    update_data = {"status": status_str, "updated_at": datetime.datetime.utcnow().isoformat()}

    # Determine which side is performing the acceptance
    if status == MatchStatus.accepted and contact_mode and contact_value:
        if profile_id == match_req.get("offerer_id"):
            update_data["offerer_contact_mode"] = contact_mode
            update_data["offerer_contact_value"] = contact_value
        elif profile_id == match_req.get("requester_id"):
            update_data["requester_contact_mode"] = contact_mode
            update_data["requester_contact_value"] = contact_value

    resp = supabase_client.table("match_requests").update(update_data).eq("id", match_request_id).execute()
    match_req = resp.data[0] if resp.data else None

    # Karma and marking as matched
    if status == MatchStatus.accepted:
        if match_req.get("offer_id"):
            mark_offer_matched(supabase_client, match_req["offer_id"])
            if match_req.get("requester_id"):
                add_karma(supabase_client, match_req["requester_id"], 5)
        if match_req.get("request_id"):
            mark_request_matched(supabase_client, match_req["request_id"])
            if match_req.get("offerer_id"):
                add_karma(supabase_client, match_req["offerer_id"], 5)

        # Send emails
        requester_profile = get_profile(supabase_client, match_req["requester_id"])
        offerer_profile = get_profile(supabase_client, match_req["offerer_id"])
        if requester_profile and offerer_profile:
            requester_user = UserEmailObj(requester_profile)
            offerer_user = UserEmailObj(offerer_profile)

            # Use stored contact info from match_request
            requester_contact = {
                "mode": match_req.get("requester_contact_mode"),
                "value": match_req.get("requester_contact_value"),
            }
            offerer_contact = {
                "mode": match_req.get("offerer_contact_mode"),
                "value": match_req.get("offerer_contact_value"),
            }

            send_match_accepted_email(
                requester_user,
                offerer_user,
                user1_contact=requester_contact,
                user2_contact=offerer_contact
            )

    return match_req



def cancel_match_request(supabase_client: SupabaseClient, match_request_id: int, requester_id: str):
    resp = supabase_client.table("match_requests")\
        .delete()\
        .eq("id", match_request_id)\
        .eq("requester_id", requester_id)\
        .eq("status", MatchStatus.pending.value)\
        .execute()
    
    add_karma(supabase_client, requester_id, -1)

    return bool(resp.data)


def mark_match_request_notified(supabase_client: SupabaseClient, match_request_id: int):
    resp = supabase_client.table("match_requests")\
        .update({"notified": True})\
        .eq("id", match_request_id)\
        .execute()
    return resp.data[0] if resp.data else None

def get_all_requests(supabase_client: SupabaseClient, exclude_profile_id: str = None, include_inactive: bool = False):
    query = supabase_client.table("requests").select("*")
    if exclude_profile_id:
        query = query.neq("profile_id", exclude_profile_id)
    if not include_inactive:
        query = query.eq("is_active", True)
    resp = query.execute()
    return resp.data if resp.data else []


def get_all_offers(supabase_client: SupabaseClient, exclude_profile_id: str = None, include_inactive: bool = False):
    query = supabase_client.table("offers").select("*")
    if exclude_profile_id:
        query = query.neq("profile_id", exclude_profile_id)
    if not include_inactive:
        query = query.eq("is_active", True)
    resp = query.execute()
    return resp.data if resp.data else []



# -----------------------------
# MATCH CRUD
# -----------------------------


def match_request_exists(supabase_client: SupabaseClient , requester_id, request_id, offer_id):
    res = supabase_client.table("match_requests")\
        .select("id")\
        .eq("requester_id", requester_id)\
        .eq("request_id", request_id)\
        .eq("offer_id", offer_id)\
        .execute()
    return bool(res.data)



def get_potential_matches(supabase_client, profile_id: str):
    """
    Return potential matches for the logged-in profile.
    Excludes matches where requester and offerer are the same profile.
    """
    candidates = []

    # Fetch active offers and requests
    all_offers = supabase_client.table("offers")\
        .select("*, profiles(full_name, postal_code)")\
        .eq("is_active", True)\
        .execute().data or []

    all_requests = supabase_client.table("requests")\
        .select("*, profiles(full_name, postal_code)")\
        .eq("is_active", True)\
        .execute().data or []

    # Separate my vs others
    my_offers = [o for o in all_offers if o["profile_id"] == profile_id]
    my_requests = [r for r in all_requests if r["profile_id"] == profile_id]

    others_offers = [o for o in all_offers if o["profile_id"] != profile_id]
    others_requests = [r for r in all_requests if r["profile_id"] != profile_id]

    # Pre-fetch existing match requests
    existing = supabase_client.table("match_requests")\
        .select("offer_id, request_id")\
        .or_(f"requester_id.eq.{profile_id},offerer_id.eq.{profile_id}")\
        .execute().data or []

    existing_pairs = {
        (mr["offer_id"], mr["request_id"])
        for mr in existing
        if mr.get("offer_id") is not None and mr.get("request_id") is not None
    }

    # 1. My requests -> Others' offers
    for req in my_requests:
        for offer in others_offers:
            # Skip self-match (shouldn’t happen, but just in case)
            if req["profile_id"] == offer["profile_id"]:
                continue
            if (offer["id"], req["id"]) not in existing_pairs:
                candidates.append((offer, req))

    # 2. My offers -> Others' requests
    for offer in my_offers:
        for req in others_requests:
            if offer["profile_id"] == req["profile_id"]:
                continue
            if (offer["id"], req["id"]) not in existing_pairs:
                candidates.append((offer, req))

    return candidates






def accept_match_request(
    supabase_client: SupabaseClient,
    match_request_id: int,
    profile_id: str,
    contact_mode: str = None,
    contact_value: str = None,
):
    """
    Accept a match request. The profile performing the acceptance can be either the offerer or requester.
    Prevents accepting if the linked offer or request is deactivated.
    """
    # Fetch match request
    resp = supabase_client.table("match_requests")\
        .select("*")\
        .eq("id", match_request_id)\
        .execute()

    match_req = resp.data[0] if resp.data else None
    if not match_req:
        return None

    # --- Check if linked offer/request are active ---
    offer_id = match_req.get("offer_id")
    request_id = match_req.get("request_id")

    if offer_id:
        offer_resp = supabase_client.table("offers").select("is_active").eq("id", offer_id).execute()
        if not offer_resp.data or not offer_resp.data[0].get("is_active", True):
            raise Exception("Cannot accept match: the offer has been deactivated.")

    if request_id:
        request_resp = supabase_client.table("requests").select("is_active").eq("id", request_id).execute()
        if not request_resp.data or not request_resp.data[0].get("is_active", True):
            raise Exception("Cannot accept match: the request has been deactivated.")

    # Call the central updater
    return update_match_request_status(
        supabase_client,
        match_request_id,
        status=MatchStatus.accepted,
        profile_id=profile_id,
        contact_mode=contact_mode,
        contact_value=contact_value
    )



def decline_match_request(supabase_client: SupabaseClient, match_request_id: int, profile_id: str):
    """
    Decline a match request. 
    Updates status to 'declined' instead of deleting.
    Only the offerer can decline.
    """
    resp = supabase_client.table("match_requests")\
        .select("*")\
        .eq("id", match_request_id)\
        .eq("offerer_id", profile_id)\
        .execute()

    match_req = resp.data[0] if not resp.error and resp.data else None
    if not match_req:
        return None

    # Update status → declined
    updated = update_match_request_status(supabase_client, match_request_id, MatchStatus.declined)

    return updated


def toggle_offer_active(supabase_client: SupabaseClient, offer_id: int, is_active: bool):
    return update_offer(supabase_client, offer_id, is_active=is_active)

def toggle_request_active(supabase_client: SupabaseClient, request_id: int, is_active: bool):
    return update_request(supabase_client, request_id, is_active=is_active)
