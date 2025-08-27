# data/models.py
from sqlalchemy import Column, String, Integer, ForeignKey, Boolean, Text, Float, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from data.db import Base
import enum
import hashlib

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
    postal_code = Column(String(20), nullable=False)
    phone_hash = Column(String(64), nullable=True)  # SHA256 hash
    share_phone = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    offers = relationship("Offer", back_populates="profile")
    requests = relationship("Request", back_populates="profile")

    def __repr__(self):
        return f"<Profile(id={self.id}, full_name={self.full_name})>"

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
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    profile = relationship("Profile", back_populates="offers")
    matches = relationship("Match", back_populates="offer")

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
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    profile = relationship("Profile", back_populates="requests")
    matches = relationship("Match", back_populates="request")

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
