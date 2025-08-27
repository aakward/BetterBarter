from sqlalchemy.orm import Session
from . import models
from utils import auth, helpers
from supabase import Client as SupabaseClient
from pathlib import Path
import sys

# Ensure project root is in sys.path
sys.path.append(str(Path(__file__).parent.parent))

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
    hashed_phone = helpers.hash_phone(phone) if phone else None

    profile = models.Profile(
        id=supabase_id,
        full_name=full_name,
        postal_code=postal_code,
        phone_hash=hashed_phone,
        share_phone=share_phone
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
        profile.phone_hash = helpers.hash_phone(phone)
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
def create_offer(db: Session, profile_id: str, title: str, description: str = None, category: str = None):
    offer = models.Offer(profile_id=profile_id, title=title, description=description, category=category)
    db.add(offer)
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
    db.delete(offer)
    db.commit()
    return offer

# -----------------------------
# REQUEST CRUD
# -----------------------------
def create_request(db: Session, profile_id: str, title: str, description: str = None, category: str = None):
    req = models.Request(profile_id=profile_id, title=title, description=description, category=category)
    db.add(req)
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
    db.delete(req)
    db.commit()
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
