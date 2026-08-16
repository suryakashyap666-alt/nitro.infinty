"""Food Recommendation Engine for Saraswati Food Delivery.

Personalized restaurant and food suggestions based on:
- Order history
- Browsing behavior
- Favorite cuisines
- Time of day
- Local trends
- User preferences
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from typing import Any, Dict, List
from datetime import datetime
import statistics


@dataclass
class FoodRecommendation:
    """A personalized food or restaurant recommendation."""
    restaurant_id: str
    restaurant_name: str
    cuisine_type: str
    reason: str  # "Based on your order history" | "Trending in your area" | etc
    confidence: float  # 0.0-100.0
    offer: str | None  # Optional promotional offer
    estimated_delivery_time: int  # minutes
    rating: float  # 1.0-5.0


@dataclass
class UserFoodProfile:
    """User's food preferences and behavior."""
    user_id: str
    favorite_cuisines: List[str]
    favorite_restaurants: List[str]
    order_history: List[Dict[str, Any]]
    search_history: List[str]
    disabled_personalization: bool = False


class FoodRecommendationEngine:
    """Generate personalized food recommendations for Saraswati users.
    
    Lightweight heuristic-based engine that respects privacy settings.
    """

    def __init__(self, storage_path: str) -> None:
        self.storage_path = storage_path
        self._ensure_storage()

    def _ensure_storage(self) -> None:
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        if not os.path.exists(self.storage_path):
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump({"users": {}, "restaurants": {}}, f)

    def _load_data(self) -> Dict[str, Any]:
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"users": {}, "restaurants": {}}

    def _save_data(self, data: Dict[str, Any]) -> None:
        tmp = self.storage_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, self.storage_path)

    def _is_guest(self, user_id: str) -> bool:
        """Guest users have minimal history tracking."""
        return isinstance(user_id, str) and user_id.startswith("guest_")

    def get_or_create_profile(self, user_id: str) -> UserFoodProfile:
        """Get or initialize user profile."""
        data = self._load_data()
        users = data.setdefault("users", {})
        u = users.setdefault(user_id, {})

        return UserFoodProfile(
            user_id=user_id,
            favorite_cuisines=u.get("favorite_cuisines", []),
            favorite_restaurants=u.get("favorite_restaurants", []),
            order_history=u.get("order_history", []),
            search_history=u.get("search_history", []),
            disabled_personalization=u.get("disabled_personalization", False),
        )

    def record_search(self, user_id: str, search_query: str) -> None:
        """Record user food search."""
        if self._is_guest(user_id):
            return  # Don't persist guest searches

        data = self._load_data()
        users = data.setdefault("users", {})
        u = users.setdefault(user_id, {})
        
        history = u.get("search_history", [])
        history.append(search_query)
        u["search_history"] = history[-100:]  # Keep last 100
        
        self._save_data(data)

    def record_order(self, user_id: str, order: Dict[str, Any]) -> None:
        """Record user order for preference learning."""
        if self._is_guest(user_id):
            return  # Don't persist guest orders

        data = self._load_data()
        users = data.setdefault("users", {})
        u = users.setdefault(user_id, {})

        order_history = u.get("order_history", [])
        order_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "restaurant_id": order.get("restaurant_id"),
            "restaurant_name": order.get("restaurant_name"),
            "cuisine": order.get("cuisine"),
            "items": order.get("items", []),
            "rating": order.get("rating"),
        }
        order_history.append(order_entry)
        u["order_history"] = order_history[-50:]  # Keep last 50

        # Update favorite cuisines
        cuisine = order.get("cuisine")
        if cuisine:
            cuisines = u.get("favorite_cuisines", [])
            if cuisine not in cuisines:
                cuisines.append(cuisine)
            u["favorite_cuisines"] = cuisines[-20:]

        # Update favorite restaurants
        rest_name = order.get("restaurant_name")
        if rest_name:
            restaurants = u.get("favorite_restaurants", [])
            if rest_name not in restaurants:
                restaurants.append(rest_name)
            u["favorite_restaurants"] = restaurants[-15:]

        self._save_data(data)

    def set_personalization_enabled(self, user_id: str, enabled: bool) -> None:
        """Allow user to disable personalization."""
        if self._is_guest(user_id):
            return

        data = self._load_data()
        users = data.setdefault("users", {})
        u = users.setdefault(user_id, {})
        u["disabled_personalization"] = not enabled
        self._save_data(data)

    def recommend(
        self,
        user_id: str,
        available_restaurants: List[Dict[str, Any]] | None = None,
        local_hour: int | None = None,
        location: str | None = None,
    ) -> List[FoodRecommendation]:
        """Generate recommendations for user.
        
        Args:
            user_id: User ID
            available_restaurants: List of restaurants with metadata
            local_hour: Current hour (0-23) for time-based recommendations
            location: User location for trending recommendations
        
        Returns:
            Ranked list of recommendations
        """
        available_restaurants = available_restaurants or []
        local_hour = local_hour or datetime.utcnow().hour
        
        profile = self.get_or_create_profile(user_id)

        if profile.disabled_personalization:
            # Return generic recommendations only
            return self._recommend_generic(available_restaurants, local_hour)

        recommendations: List[FoodRecommendation] = []

        # 1. Favorite restaurants (high confidence)
        for rest_name in profile.favorite_restaurants[:5]:
            matching = [r for r in available_restaurants if r.get("name") == rest_name]
            for rest in matching:
                rec = FoodRecommendation(
                    restaurant_id=rest.get("id", rest_name),
                    restaurant_name=rest_name,
                    cuisine_type=rest.get("cuisine", "Mixed"),
                    reason="Based on your order history",
                    confidence=85.0,
                    offer=rest.get("current_offer"),
                    estimated_delivery_time=rest.get("delivery_time", 30),
                    rating=rest.get("rating", 4.0),
                )
                recommendations.append(rec)
                break

        # 2. Cuisine preferences (medium confidence)
        seen_rest_ids = {r.restaurant_id for r in recommendations}
        for cuisine in profile.favorite_cuisines[:3]:
            matching = [
                r for r in available_restaurants 
                if r.get("cuisine") == cuisine and r.get("id") not in seen_rest_ids
            ]
            for rest in matching[:2]:
                rec = FoodRecommendation(
                    restaurant_id=rest.get("id"),
                    restaurant_name=rest.get("name", cuisine),
                    cuisine_type=cuisine,
                    reason=f"You love {cuisine}",
                    confidence=75.0,
                    offer=rest.get("current_offer"),
                    estimated_delivery_time=rest.get("delivery_time", 30),
                    rating=rest.get("rating", 4.0),
                )
                recommendations.append(rec)
                seen_rest_ids.add(rest.get("id"))

        # 3. Time-based recommendations
        time_recs = self._recommend_by_time(available_restaurants, local_hour)
        for rec in time_recs:
            if rec.restaurant_id not in seen_rest_ids:
                recommendations.append(rec)
                seen_rest_ids.add(rec.restaurant_id)

        return recommendations[:10]  # Top 10

    def _recommend_generic(
        self,
        available_restaurants: List[Dict[str, Any]],
        local_hour: int,
    ) -> List[FoodRecommendation]:
        """Generic recommendations for new users or disabled personalization."""
        recommendations: List[FoodRecommendation] = []

        # Filter by hour and popularity
        is_breakfast = 6 <= local_hour < 10
        is_lunch = 11 <= local_hour < 14
        is_dinner = 18 <= local_hour < 22

        time_label = "breakfast" if is_breakfast else ("lunch" if is_lunch else ("dinner" if is_dinner else "snacks"))

        # Sort by rating and delivery time
        sorted_rests = sorted(
            available_restaurants,
            key=lambda r: (-r.get("rating", 0), r.get("delivery_time", 999)),
        )

        for rest in sorted_rests[:8]:
            rec = FoodRecommendation(
                restaurant_id=rest.get("id", rest.get("name")),
                restaurant_name=rest.get("name", "Unknown"),
                cuisine_type=rest.get("cuisine", "Mixed"),
                reason=f"Popular for {time_label}",
                confidence=70.0,
                offer=rest.get("current_offer"),
                estimated_delivery_time=rest.get("delivery_time", 30),
                rating=rest.get("rating", 4.0),
            )
            recommendations.append(rec)

        return recommendations

    def _recommend_by_time(
        self,
        available_restaurants: List[Dict[str, Any]],
        local_hour: int,
    ) -> List[FoodRecommendation]:
        """Time-based recommendations."""
        recommendations: List[FoodRecommendation] = []

        is_breakfast = 6 <= local_hour < 10
        is_lunch = 11 <= local_hour < 14
        is_dinner = 18 <= local_hour < 22
        is_late = 22 <= local_hour or local_hour < 6

        # Filter restaurants that serve current meal
        cuisine_prefs = {
            "breakfast": ["Bakery", "Cafe", "Breakfast", "American"],
            "lunch": ["Indian", "Asian", "Mediterranean", "American"],
            "dinner": ["Italian", "Indian", "Asian", "Mediterranean"],
            "late": ["Pizza", "Burgers", "Cafe", "Asian"],
        }

        preferred_cuisines = []
        if is_breakfast:
            preferred_cuisines = cuisine_prefs["breakfast"]
        elif is_lunch:
            preferred_cuisines = cuisine_prefs["lunch"]
        elif is_dinner:
            preferred_cuisines = cuisine_prefs["dinner"]
        elif is_late:
            preferred_cuisines = cuisine_prefs["late"]

        for rest in available_restaurants:
            if rest.get("cuisine") in preferred_cuisines:
                rec = FoodRecommendation(
                    restaurant_id=rest.get("id", rest.get("name")),
                    restaurant_name=rest.get("name", "Unknown"),
                    cuisine_type=rest.get("cuisine", "Mixed"),
                    reason=f"Perfect for {['breakfast', 'lunch', 'dinner', 'late night'][int(is_breakfast) + int(is_lunch)*2 + int(is_dinner)*3 + int(is_late)*4]}",
                    confidence=72.0,
                    offer=rest.get("current_offer"),
                    estimated_delivery_time=rest.get("delivery_time", 30),
                    rating=rest.get("rating", 4.0),
                )
                recommendations.append(rec)

        return recommendations[:5]

    def get_personalized_ads(self, user_id: str) -> List[Dict[str, Any]]:
        """Get personalized ads based on user preferences."""
        profile = self.get_or_create_profile(user_id)
        
        if profile.disabled_personalization:
            return []

        ads = []

        # Create ads for favorite cuisines
        for cuisine in profile.favorite_cuisines[:3]:
            ads.append({
                "type": "cuisine_spotlight",
                "cuisine": cuisine,
                "message": f"New {cuisine} restaurant in your area",
                "cta": f"Explore {cuisine}",
            })

        # Create loyalty ads for frequent restaurants
        if len(profile.order_history) >= 3:
            top_restaurant = profile.favorite_restaurants[0] if profile.favorite_restaurants else None
            if top_restaurant:
                ads.append({
                    "type": "loyalty",
                    "restaurant": top_restaurant,
                    "message": f"You've ordered from {top_restaurant} {len([o for o in profile.order_history if o.get('restaurant_name') == top_restaurant])} times",
                    "offer": "Get 20% off your next order",
                    "cta": "Claim offer",
                })

        return ads
