from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class UIMatch:
    id: int
    offer_id: Optional[int]
    request_id: Optional[int]
    offer_title: Optional[str] = None
    request_title: Optional[str] = None
    offer_description: Optional[str] = None
    request_description: Optional[str] = None
    offer_image: Optional[str] = None
    request_image: Optional[str] = None
    offer_user_name: Optional[str] = None
    request_user_name: Optional[str] = None
    offer_postal: Optional[str] = None
    request_postal: Optional[str] = None
    status: str = "pending"
    created_at: datetime = None
    message: Optional[str] = None
    initiator_id: Optional[str] = None
    responder_id: Optional[str] = None
    # new contact info fields
    offerer_contact_mode: Optional[str] = None
    offerer_contact_value: Optional[str] = None
    requester_contact_mode: Optional[str] = None
    requester_contact_value: Optional[str] = None
