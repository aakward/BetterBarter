
# Purpose of geolocation.py

# Handle location-related logic separately from matching logic.

# Convert pin codes → coordinates (via an API like OpenStreetMap’s Nominatim, or Google Maps if you don’t mind API costs).

# Compute distance between users using latitude/longitude (e.g., Haversine formula).

# Keep matching rules flexible — you could then match by distance radius (e.g., 5 km) instead of only “same first 2 digits of pin code.”

import math

def haversine_distance(lat1, lon1, lat2, lon2):
    """Return distance in kilometers between two lat/lon points."""
    R = 6371  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.asin(math.sqrt(a))
    return R * c

def is_within_radius(user1, user2, radius_km: float = 10.0):
    """Check if two users are within a given distance radius."""
    if not user1.latitude or not user1.longitude or not user2.latitude or not user2.longitude:
        return False
    return haversine_distance(user1.latitude, user1.longitude, user2.latitude, user2.longitude) <= radius_km
