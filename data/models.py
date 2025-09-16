# data/models.py
from sqlalchemy import Column, String, Integer, ForeignKey, Boolean, Text, Float, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from data.db import Base
import enum
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB



# -----------------------------
# Enums
# -----------------------------
class MatchStatus(enum.Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"
    completed = "completed"

# -----------------------------
# Profiles (users authenticated via Supabase)
# -----------------------------
class Profile(Base):
    __tablename__ = "profiles"

    id = Column(String, primary_key=True)  # Supabase Auth UUID
    full_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=True, unique=True)  # NEW: email field
    postal_code = Column(String(20), nullable=False)
    phone = Column(String(64), nullable=True) 
    share_phone = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    karma = Column(Integer, default=0)
    daily_match_count = Column(Integer, default=0)
    daily_match_count_reset = Column(DateTime, default=datetime.utcnow)
    reports = Column(JSONB, default=list, nullable=True)

    offers = relationship("Offer", back_populates="profile")
    requests = relationship("Request", back_populates="profile")

    def __repr__(self):
        return f"<Profile(id={self.id}, full_name={self.full_name}, email={self.email})>"


# -----------------------------
# Offers
# -----------------------------
class Offer(Base):
    __tablename__ = "offers"
    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(String, ForeignKey("profiles.id"))
    title = Column(String(100), nullable=False)
    description = Column(Text)
    category = Column(String(50))
    subcategory = Column(String(50))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    image_file_name = Column(Text, nullable=True)
    reports = Column(JSONB, default=list, nullable=True)
  
    profile = relationship("Profile", back_populates="offers")
    matches = relationship("Match", back_populates="offer")
    match_requests = relationship("MatchRequest", back_populates="offer")

    def __repr__(self):
        return f"<Offer(id={self.id}, title={self.title}, profile_id={self.profile_id})>"

# -----------------------------
# Requests
# -----------------------------
class Request(Base):
    __tablename__ = "requests"
    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(String, ForeignKey("profiles.id"))
    title = Column(String(100), nullable=False)
    description = Column(Text)
    category = Column(String(50))
    subcategory = Column(String(50))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    image_file_name = Column(Text, nullable=True)
    reports = Column(JSONB, default=list, nullable=True)

    profile = relationship("Profile", back_populates="requests")
    matches = relationship("Match", back_populates="request")
    match_requests = relationship("MatchRequest", back_populates="request")

    def __repr__(self):
        return f"<Request(id={self.id}, title={self.title}, profile_id={self.profile_id})>"

# -----------------------------
# Matches
# -----------------------------
class Match(Base):
    __tablename__ = "matches"
    id = Column(Integer, primary_key=True, autoincrement=True)
    offer_id = Column(Integer, ForeignKey("offers.id"))
    request_id = Column(Integer, ForeignKey("requests.id"))
    score = Column(Float)
    status = Column(Enum(MatchStatus), default=MatchStatus.pending)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    offer = relationship("Offer", back_populates="matches")
    request = relationship("Request", back_populates="matches")

    def __repr__(self):
        return f"<Match(id={self.id}, offer_id={self.offer_id}, request_id={self.request_id}, status={self.status})>"

# -----------------------------
# Match Request
# -----------------------------
class MatchRequest(Base):
    __tablename__ = "match_requests"

    id = Column(Integer, primary_key=True, index=True)

    # Either one or both can be provided
    request_id = Column(Integer, ForeignKey("requests.id"), nullable=True)
    offer_id = Column(Integer, ForeignKey("offers.id"), nullable=True)

    requester_id = Column(String, ForeignKey("profiles.id"), nullable=True)
    offerer_id = Column(String, ForeignKey("profiles.id"), nullable=True)
    initiator_id = Column(String, ForeignKey("profiles.id"), nullable=True)  

    # Optional personalization
    message = Column(Text, nullable=True)

    # Contact details from requester (set when creating the request)
    requester_contact_mode = Column(String(20), nullable=True)   # e.g. "email", "phone", "whatsapp"
    requester_contact_value = Column(String(100), nullable=True)

    # Contact details from offerer (set when accepting the request)
    offerer_contact_mode = Column(String(20), nullable=True)
    offerer_contact_value = Column(String(100), nullable=True)

    # Status lifecycle
    status = Column(Enum(MatchStatus), default=MatchStatus.pending)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    notified = Column(Boolean, default=False, nullable=False)

    # Relationships
    request = relationship("Request", back_populates="match_requests")
    offer = relationship("Offer", back_populates="match_requests")
    requester = relationship("Profile", foreign_keys=[requester_id])
    offerer = relationship("Profile", foreign_keys=[offerer_id])
    initiator = relationship("Profile", foreign_keys=[initiator_id])  # <--- new relationship
