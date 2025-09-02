from supabase import Client as SupabaseClient
from utils import auth, helpers
import datetime
from data.models import MatchStatus
import re

MAX_MATCH_REQUESTS_PER_DAY = 3  # adjustable
REQUEST_BUCKET_NAME = "request-images"
OFFER_BUCKET_NAME = "offer-images"


# -----------------------------
# PROFILE CRUD
# -----------------------------
def create_profile(
    supabase_client: SupabaseClient,
    supabase_id: str,
    full_name: str,
    postal_code: str,
    phone: str = None,
    share_phone: bool = False
):
    """
    Create a profile entry in Supabase.
    """
    hashed_phone = helpers.hash_phone(phone) if phone else None

    response = supabase_client.table("profiles").insert({
        "id": supabase_id,
        "full_name": full_name,
        "postal_code": postal_code,
        "phone_hash": hashed_phone,
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
        update_data["phone_hash"] = helpers.hash_phone(phone)
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
def create_offer(supabase_client: SupabaseClient, profile_id: str, title: str, description: str = None, category: str = None):
    offer_data = {
        "profile_id": profile_id,
        "title": title,
        "description": description,
        "category": category,
        "is_active": True
    }
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
    response = supabase_client.table("offers").select("*").eq("id", offer_id).execute().data
    offers = response.data or []

    if not offers:
        return None
    
    offer=offers[0]

    add_karma(supabase_client, offer["profile_id"], points=-3)
    
    # Delete image from storage if exists
    image_file_name = offer.get("image_file_name")
    if image_file_name:
        try:
            supabase_client.storage.from_(OFFER_BUCKET_NAME).remove([image_file_name])
        except Exception as e:
            print(f"Warning: could not delete image {image_file_name}: {e}")

    # Delete the request from DB
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
def create_request(supabase_client: SupabaseClient, profile_id: str, title: str, description: str = None, category: str = None, image_file_name: str = None):
    request_data = {
        "profile_id": profile_id,
        "title": title,
        "description": description,
        "category": category,
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
    # Fetch the request
    response = supabase_client.table("requests").select("*").eq("id", request_id).execute()
    requests = response.data or []

    if not requests:
        return None

    request = requests[0]

    # Deduct karma
    add_karma(supabase_client, request["profile_id"], points=-1)

    # Delete image from storage if exists
    image_file_name = request.get("image_file_name")
    if image_file_name:
        try:
            supabase_client.storage.from_(REQUEST_BUCKET_NAME).remove([image_file_name])
        except Exception as e:
            print(f"Warning: could not delete image {image_file_name}: {e}")

    # Delete the request from DB
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


def get_existing_match_request(supabase_client: SupabaseClient, requester_id: str, request_id: int = None, offer_id: int = None):
    query = supabase_client.table("match_requests").select("*").eq("requester_id", requester_id)
    if request_id is not None:
        query = query.eq("request_id", request_id)
    if offer_id is not None:
        query = query.eq("offer_id", offer_id)
    response = query.execute()
    return response.data[0] if response.data else None


def create_match_request(
    supabase_client: SupabaseClient,
    requester_id: str,
    offer_id: int = None,
    request_id: int = None,
    message: str = None,
):
    if not can_send_match_request(supabase_client, requester_id):
        raise Exception(f"Daily limit of {MAX_MATCH_REQUESTS_PER_DAY} match requests reached.")

    if not offer_id and not request_id:
        raise Exception("Either offer_id or request_id must be provided.")

    existing = get_existing_match_request(supabase_client, requester_id, request_id, offer_id)
    if existing:
        raise Exception("You have already expressed interest or sent a match request here.")

    offerer_id = None
    if offer_id:
        offer_resp = supabase_client.table("offers").select("profile_id").eq("id", offer_id).execute()
        if offer_resp.data:
            offerer_id = offer_resp.data[0]["profile_id"]

    match_data = {
        "requester_id": requester_id,
        "offer_id": offer_id,
        "request_id": request_id,
        "offerer_id": offerer_id,
        "message": message,
        "status": MatchStatus.pending,
        "created_at": datetime.datetime.utcnow().isoformat()
    }

    resp = supabase_client.table("match_requests").insert(match_data).execute()
    add_karma(supabase_client, requester_id, 1)
    return resp.data[0] if resp.data else None


def get_match_requests_for_offer(supabase_client: SupabaseClient, offer_id: int, status: str = "pending"):
    resp = supabase_client.table("match_requests")\
        .select("*")\
        .eq("offer_id", offer_id)\
        .eq("status", status)\
        .execute()
    return resp.data


def get_match_requests_by_requester(supabase_client: SupabaseClient, requester_id: str, status: str = None):
    query = supabase_client.table("match_requests").select("*").eq("requester_id", requester_id)
    if status:
        query = query.eq("status", status)
    resp = query.execute()
    return resp.data


def get_match_requests_for_offerer(supabase_client: SupabaseClient, offerer_id: str, status: str = None):
    query = supabase_client.table("match_requests").select("*").eq("offerer_id", offerer_id)
    if status:
        query = query.eq("status", status)
    resp = query.execute()
    return resp.data


def update_match_request_status(supabase_client: SupabaseClient, match_request_id: int, status: str):
    resp = supabase_client.table("match_requests").update({
        "status": status,
        "updated_at": datetime.datetime.utcnow().isoformat()
    }).eq("id", match_request_id).execute()

    match_req = resp.data[0] if resp.data else None
    if not match_req:
        return None

    if status == MatchStatus.accepted:
        if match_req.get("offer_id"):
            mark_offer_matched(supabase_client, match_req["offer_id"])
        if match_req.get("request_id"):
            mark_request_matched(supabase_client, match_req["request_id"])

    if status == MatchStatus.completed:
        if match_req.get("requester_id"):
            add_karma(supabase_client, match_req["requester_id"], 5)
        if match_req.get("offerer_id"):
            add_karma(supabase_client, match_req["offerer_id"], 5)

    return match_req


def cancel_match_request(supabase_client: SupabaseClient, match_request_id: int, requester_id: str):
    resp = supabase_client.table("match_requests")\
        .delete()\
        .eq("id", match_request_id)\
        .eq("requester_id", requester_id)\
        .eq("status", MatchStatus.pending)\
        .execute()
    return bool(resp.data)


def mark_match_request_notified(supabase_client: SupabaseClient, match_request_id: int):
    resp = supabase_client.table("match_requests")\
        .update({"notified": True})\
        .eq("id", match_request_id)\
        .execute()
    return resp.data[0] if resp.data else None

def get_all_requests(supabase_client: SupabaseClient, exclude_profile_id: str = None):
    query = supabase_client.table("requests").select("*")
    if exclude_profile_id:
        query = query.neq("profile_id", exclude_profile_id)
    resp = query.execute()
    return resp.data if resp.data else []


def get_all_offers(supabase_client: SupabaseClient, exclude_profile_id: str = None):
    query = supabase_client.table("offers").select("*")
    if exclude_profile_id:
        query = query.neq("profile_id", exclude_profile_id)
    resp = query.execute()
    return resp.data if resp.data else []