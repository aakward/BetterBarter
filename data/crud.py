from sqlalchemy.orm import Session

from data import db
from . import models
from utils import auth, helpers
from supabase import Client as SupabaseClient
from pathlib import Path
import sys
import datetime
from data.models import MatchStatus
import re
import supabase

# Ensure project root is in sys.path
sys.path.append(str(Path(__file__).parent.parent))


MAX_MATCH_REQUESTS_PER_DAY = 3  # adjustable
REQUEST_BUCKET_NAME = "request-images"
OFFER_BUCKET_NAME = "offer-images"

# -----------------------------
# PROFILE CRUD
# -----------------------------
def create_profile(
    db: Session,
    supabase_client: SupabaseClient,
    supabase_id: str,
    full_name: str,
    postal_code: str,
    phone: str = None,
    share_phone: bool = False
):
    """
    Create a local profile entry after Supabase user creation.
    """

    profile = models.Profile(
        id=supabase_id,
        full_name=full_name,
        postal_code=postal_code,
        phone=phone,
        share_phone=share_phone,
        karma=1  # initial karma point
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile

def get_profile(db: Session, profile_id: str):
    return db.query(models.Profile).filter(models.Profile.id == profile_id).first()

def update_profile(db: Session, profile_id: str, phone: str = None, share_phone: bool = None, **kwargs):
    profile = db.query(models.Profile).filter(models.Profile.id == profile_id).first()
    if not profile:
        return None

    if phone is not None:
        profile.phone = phone
    if share_phone is not None:
        profile.share_phone = share_phone

    for key, value in kwargs.items():
        setattr(profile, key, value)

    db.commit()
    db.refresh(profile)
    return profile

def delete_profile(db: Session, profile_id: str, supabase_client: SupabaseClient):
    """
    Deletes user from Supabase Auth and then local profile table.
    """
    # Delete Supabase Auth user first
    supabase_client.auth.admin.delete_user(profile_id)

    # Then delete local DB profile
    profile = db.query(models.Profile).filter(models.Profile.id == profile_id).first()
    if profile:
        db.delete(profile)
        db.commit()
    return profile

# -----------------------------
# OFFER CRUD
# -----------------------------
def create_offer(db: Session, profile_id: str, title: str, description: str = None, category: str = None, image_file_name:str = None):
    offer = models.Offer(profile_id=profile_id, title=title, description=description, category=category, image_file_name=image_file_name)
    db.add(offer)

    # Increment karma of the profile
    add_karma(db=db, profile_id= profile_id, points=3)

    db.commit()
    db.refresh(offer)
    return offer

def get_offers(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Offer).offset(skip).limit(limit).all()

def update_offer(db: Session, offer_id: int, **kwargs):
    offer = db.query(models.Offer).filter(models.Offer.id == offer_id).first()
    if not offer:
        return None
    for key, value in kwargs.items():
        setattr(offer, key, value)
    db.commit()
    db.refresh(offer)
    return offer

def delete_offer(db: Session, offer_id: int):
    offer = db.query(models.Offer).filter(models.Offer.id == offer_id).first()
    if not offer:
        return None


    image_file_name = offer.get("image_file_name")
    if image_file_name:
        try:
            supabase.storage.from_(OFFER_BUCKET_NAME).remove([image_file_name])
        except Exception as e:
            print(f"Warning: could not delete image {image_file_name}: {e}")
    
    add_karma(db=db, profile_id= offer.profile_id, points=-1)

    del_response = supabase.table("offers").delete().eq("id", offer_id).execute()
    return del_response.data[0] if del_response.data else None

def mark_offer_matched(db: Session, offer_id: int):
    offer = db.query(models.Offer).filter(models.Offer.id == offer_id).first()
    if not offer:
        return None

    offer.is_active = False

    add_karma(db=db, profile_id= offer.profile_id, points=5)

    db.commit()
    db.refresh(offer)
    return offer

# -----------------------------
# REQUEST CRUD
# -----------------------------
def create_request(db: Session, profile_id: str, title: str, description: str = None, category: str = None,  image_file_name: str = None):
    req = models.Request(profile_id=profile_id, title=title, description=description, category=category, image_file_name=image_file_name)
    db.add(req)

    add_karma(db=db, profile_id= profile_id, points=1)

    db.commit()
    db.refresh(req)
    return req

def get_requests(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Request).offset(skip).limit(limit).all()

def update_request(db: Session, request_id: int, **kwargs):
    req = db.query(models.Request).filter(models.Request.id == request_id).first()
    if not req:
        return None
    for key, value in kwargs.items():
        setattr(req, key, value)
    db.commit()
    db.refresh(req)
    return req

def delete_request(db: Session, request_id: int):
    req = db.query(models.Request).filter(models.Request.id == request_id).first()
    if not req:
        return None


    image_file_name = req.get("image_file_name")
    if image_file_name:
        try:
            supabase.storage.from_(REQUEST_BUCKET_NAME).remove([image_file_name])
        except Exception as e:
            print(f"Warning: could not delete image {image_file_name}: {e}")
    
    add_karma(db=db, profile_id= req.profile_id, points=-1)

    del_response = supabase.table("requests").delete().eq("id", request_id).execute()
    return del_response.data[0] if del_response.data else None

def mark_request_matched(db: Session, request_id: int):
    req = db.query(models.Request).filter(models.Request.id == request_id).first()
    if not req:
        return None

    req.is_active = False
    add_karma(db=db, profile_id= req.profile_id, points=5)

    db.commit()
    db.refresh(req)
    return req

# -----------------------------
# AUTHENTICATION via Supabase
# -----------------------------
def authenticate_user(supabase_client: SupabaseClient, email: str, password: str):
    """
    Authenticate user via Supabase Auth.
    Returns Supabase user object if successful, else None.
    """
    response = supabase_client.auth.sign_in_with_password({"email": email, "password": password})
    return response.user if response.user else None

# -----------------------------
# Karma system helper
# -----------------------------

def add_karma(db: Session, profile_id: str, points: int):
    profile = db.query(models.Profile).filter(models.Profile.id == profile_id).first()
    if profile:
        profile.karma = (profile.karma or 0) + points
        db.commit()
        db.refresh(profile)
    return profile


# -----------------------------
# Match Request CRUD
# -----------------------------

def can_send_match_request(db: Session, requester_id: str) -> bool:
    today_start = datetime.datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    count = db.query(models.MatchRequest)\
              .filter(models.MatchRequest.requester_id == requester_id)\
              .filter(models.MatchRequest.created_at >= today_start)\
              .count()
    return count < MAX_MATCH_REQUESTS_PER_DAY


def create_match_request(
    db: Session,
    requester_id: str,
    offer_id: int = None,
    request_id: int = None,
    message: str = None,
):
    """
    Create a match request (supports both full match and interest-only).
    """
    if not can_send_match_request(db, requester_id):
        raise Exception(f"Daily limit of {MAX_MATCH_REQUESTS_PER_DAY} match requests reached.")

    if not offer_id and not request_id:
        raise Exception("Either offer_id or request_id must be provided.")

    # Ensure no duplicate request
    existing = get_existing_match_request(db, requester_id, request_id, offer_id)
    if existing:
        raise Exception("You have already expressed interest or sent a match request here.")

    # Derive offerer_id if offer exists
    offerer_id = None
    if offer_id:
        offer = db.query(models.Offer).filter_by(id=offer_id).first()
        if offer:
            offerer_id = offer.profile_id

    match_request = models.MatchRequest(
        requester_id=requester_id,
        offer_id=offer_id,
        request_id=request_id,
        offerer_id=offerer_id,
        message=message,
        status=MatchStatus.pending,
    )
    db.add(match_request)

    add_karma(db=db, profile_id=requester_id, points=1)
    db.commit()
    db.refresh(match_request)
    return match_request


def get_match_requests_for_offer(db: Session, offer_id: int):
    return db.query(models.MatchRequest)\
             .filter(models.MatchRequest.offer_id == offer_id, models.MatchRequest.status == "pending")\
             .all()


def get_match_requests_by_requester(db: Session, requester_id: str, status: str = None):
    query = db.query(models.MatchRequest).filter(models.MatchRequest.requester_id == requester_id)
    if status:
        query = query.filter(models.MatchRequest.status == status)
    return query.all()


def get_match_requests_for_offerer(db: Session, offerer_id: str, status: str = None):
    query = db.query(models.MatchRequest).filter(models.MatchRequest.offerer_id == offerer_id)
    if status:
        query = query.filter(models.MatchRequest.status == status)
    return query.all()


def update_match_request_status(db: Session, match_request_id: int, status: str):
    match_req = db.query(models.MatchRequest).filter_by(id=match_request_id).first()
    if not match_req:
        return None

    match_req.status = status
    match_req.updated_at = datetime.datetime.utcnow()

    if status == MatchStatus.accepted:
        if match_req.offer_id:
            mark_offer_matched(db, match_req.offer_id)
        if match_req.request_id:
            mark_request_matched(db, match_req.request_id)

    if status == MatchStatus.completed:
        # Reward karma to both sides
        if match_req.requester_id:
            add_karma(db, match_req.requester_id, 5)
        if match_req.offerer_id:
            add_karma(db, match_req.offerer_id, 5)

    db.commit()
    db.refresh(match_req)
    return match_req


def cancel_match_request(db: Session, match_request_id: int, requester_id: str):
    match_req = db.query(models.MatchRequest).filter_by(
        id=match_request_id,
        requester_id=requester_id,
        status=MatchStatus.pending
    ).first()
    if match_req:
        db.delete(match_req)
        db.commit()
        return True
    return False


def mark_match_request_notified(db: Session, match_request_id: int):
    match_req = db.query(models.MatchRequest).filter_by(id=match_request_id).first()
    if match_req:
        match_req.notified = True
        db.commit()
        db.refresh(match_req)
    return match_req


def get_existing_match_request(db: Session, requester_id: str, request_id: int = None, offer_id: int = None):
    query = db.query(models.MatchRequest).filter(models.MatchRequest.requester_id == requester_id)
    if request_id is not None:
        query = query.filter(models.MatchRequest.request_id == request_id)
    if offer_id is not None:
        query = query.filter(models.MatchRequest.offer_id == offer_id)
    return query.first()




def get_all_requests(db: Session, exclude_profile_id: str = None):
    query = db.query(models.Request)
    if exclude_profile_id:
        query = query.filter(models.Request.profile_id != exclude_profile_id)
    return query.all()

def get_all_offers(db: Session, exclude_profile_id: str = None):
    query = db.query(models.Offer)
    if exclude_profile_id:
        query = query.filter(models.Offer.profile_id != exclude_profile_id)
    return query.all()

# crud/matches.py
def get_potential_matches(db, profile_id: str):
    """
    Return potential matches for the logged-in profile.
    Includes (offer, request) pairs that are NOT already
    in Match or MatchRequest.
    """
    from models import Offer, Request, Match, MatchRequest

    # Requests by me
    my_requests = db.query(Request).filter(Request.profile_id == profile_id).all()
    # Offers by me
    my_offers = db.query(Offer).filter(Offer.profile_id == profile_id).all()

    # Candidate matches: other's offers ↔ my requests
    offer_candidates = db.query(Offer, Request).join(Request).filter(
        Request.profile_id == profile_id,
        Offer.profile_id != profile_id,
    ).all()

    # Candidate matches: other's requests ↔ my offers
    request_candidates = db.query(Offer, Request).join(Offer).filter(
        Offer.profile_id == profile_id,
        Request.profile_id != profile_id,
    ).all()

    candidates = offer_candidates + request_candidates

    # Filter out already existing confirmed/sent/received
    existing = db.query(MatchRequest).filter(
        (MatchRequest.requester_id == profile_id) |
        (MatchRequest.offerer_id == profile_id)
    ).all()
    existing_pairs = {(mr.offer_id, mr.request_id) for mr in existing}

    # Only keep fresh pairs
    return [
        (o, r) for (o, r) in candidates
        if (o.id, r.id) not in existing_pairs
    ]
