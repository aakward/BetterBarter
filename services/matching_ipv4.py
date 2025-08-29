def is_nearby(postal1: str, postal2: str, level: int = 3) -> bool:
    """Check if two postal codes are 'nearby' based on first N digits."""
    if not postal1 or not postal2:
        return False
    return postal1[:level] == postal2[:level]

def find_matches_for_user(
    supabase_client,
    profile_id: str,
    max_results: int = 10,
    proximity_level: int = 3
):
    """
    Find potential matches for a profile using Supabase client:
    - Match profile's offers to other profiles' requests
    - Match profile's requests to other profiles' offers
    Returns a list of dictionaries with details for UI.
    """
    # Fetch the user profile
    res = supabase_client.table("profiles").select("*").eq("id", profile_id).execute()
    if not res.data or len(res.data) == 0:
        return []
    profile = res.data[0]

    matches = []

    # --- Match user's offers to other profiles' requests ---
    offers_res = supabase_client.table("offers").select("*").eq("profile_id", profile_id).execute()
    offers = offers_res.data or []

    for offer in offers:
        req_res = (
            supabase_client.table("requests")
            .select("*")
            .neq("profile_id", profile_id)
            .like("title", f"%{offer['title']}%")
            .execute()
        )
        requests = req_res.data or []

        for req in requests:
            # Fetch requester's profile
            req_profile_res = supabase_client.table("profiles").select("*").eq("id", req["profile_id"]).execute()
            req_profile = req_profile_res.data[0] if req_profile_res.data else {}
            score = 1.0 if is_nearby(profile["postal_code"], req_profile.get("postal_code"), proximity_level) else 0.5
            matches.append({
                "offer_title": offer["title"],
                "offer_profile_name": profile["full_name"],
                "offer_postal": profile["postal_code"],
                "request_title": req["title"],
                "request_profile_name": req_profile.get("full_name"),
                "request_postal": req_profile.get("postal_code"),
                "score": score
            })

    # --- Match user's requests to other profiles' offers ---
    req_res = supabase_client.table("requests").select("*").eq("profile_id", profile_id).execute()
    user_requests = req_res.data or []

    for req in user_requests:
        offers_res = (
            supabase_client.table("offers")
            .select("*")
            .neq("profile_id", profile_id)
            .like("title", f"%{req['title']}%")
            .execute()
        )
        other_offers = offers_res.data or []

        for offer in other_offers:
            offer_profile_res = supabase_client.table("profiles").select("*").eq("id", offer["profile_id"]).execute()
            offer_profile = offer_profile_res.data[0] if offer_profile_res.data else {}
            score = 1.0 if is_nearby(profile["postal_code"], offer_profile.get("postal_code"), proximity_level) else 0.5
            matches.append({
                "offer_title": offer["title"],
                "offer_profile_name": offer_profile.get("full_name"),
                "offer_postal": offer_profile.get("postal_code"),
                "request_title": req["title"],
                "request_profile_name": profile["full_name"],
                "request_postal": profile["postal_code"],
                "score": score
            })

    # Sort matches by score descending
    matches.sort(key=lambda x: x["score"], reverse=True)
    return matches[:max_results]
