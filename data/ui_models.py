from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class UIMatch:
    id: int
    offer_id: Optional[int]
    request_id: Optional[int]
    offer_description: Optional[str]
    request_description: Optional[str]
    offer_image: Optional[str]
    request_image: Optional[str]
    status: str
    created_at: datetime
    message: Optional[str] = None
    initiator_id: Optional[str] = None
    responder_id: Optional[str] = None
    # new fields
    offer_title: Optional[str] = None
    request_title: Optional[str] = None
    offer_user_name: Optional[str] = None
    request_user_name: Optional[str] = None
    offer_postal: Optional[str] = None
    request_postal: Optional[str] = None
    message: Optional[str] = None
    initiator_id: Optional[str] = None
    responder_id: Optional[str] = None
