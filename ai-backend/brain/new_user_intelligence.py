"""New User Intelligence Handler for Saraswati Food Delivery.

Provides smart recommendations for users with no order history.
Based on time of day, location trends, popular restaurants, seasonal foods.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List
from datetime import datetime


@dataclass
class NewUserRecommendation:
    """Recommendation for new user."""
    restaurant_name: str
    cuisine_type: str
    reason: str
    confidence: float
    category: str  # "trending" | "time_based" | "popular" | "seasonal"


class NewUserIntelligence:
    """Generate smart recommendations for new Saraswati users."""

    def __init__(self) -> None:
        # Local trends and popular restaurants (can be updated from external data)
        self.time_based_preferences = {
            "morning": {  # 6-10
                "cuisines": ["Bakery", "Cafe", "Breakfast", "Smoothie Bar"],
                "description": "breakfast",
            },
            "lunch": {  # 11-14
                "cuisines": ["Indian", "Asian", "Mediterranean", "Salad", "Fast Food"],
                "description": "lunch",
            },
            "afternoon": {  # 14-17
                "cuisines": ["Cafe", "Bakery", "Dessert", "Fast Food"],
                "description": "snacks",
            },
            "dinner": {  # 18-21
                "cuisines": ["Italian", "Indian", "Asian", "Mediterranean", "Steakhouse"],
                "description": "dinner",
            },
            "late": {  # 21-23
                "cuisines": ["Pizza", "Burgers", "Chinese", "Fast Food"],
                "description": "late night",
            },
            "night": {  # 23-6
                "cuisines": ["Delivery Pizza", "Noodles", "Biryani", "Dessert"],
                "description": "night snacks",
            },
        }

        self.seasonal_foods = {
            "summer": ["Ice Cream", "Beverages", "Salads", "Light Meals", "Smoothies"],
            "monsoon": ["Hot Tea", "Snacks", "Indian Comfort Food", "Soups"],
            "winter": ["Hot Coffee", "Desserts", "Indian Cuisine", "Chinese"],
            "spring": ["Fresh Food", "Healthy Options", "Salads", "Light Meals"],
        }

    def get_season(self) -> str:
        """Determine current season."""
        month = datetime.utcnow().month
        if month in [12, 1, 2]:
            return "winter"
        elif month in [3, 4, 5]:
            return "spring"
        elif month in [6, 7, 8]:
            return "summer"
        else:
            return "monsoon"

    def get_time_period(self, local_hour: int | None = None) -> str:
        """Get meal time period."""
        local_hour = local_hour or datetime.utcnow().hour
        if 6 <= local_hour < 10:
            return "morning"
        elif 11 <= local_hour < 14:
            return "lunch"
        elif 14 <= local_hour < 17:
            return "afternoon"
        elif 18 <= local_hour < 21:
            return "dinner"
        elif 21 <= local_hour < 23:
            return "late"
        else:
            return "night"

    def recommend(
        self,
        available_restaurants: List[Dict[str, Any]] | None = None,
        local_hour: int | None = None,
        location_trending: List[str] | None = None,
        featured_offers: List[Dict[str, Any]] | None = None,
    ) -> List[NewUserRecommendation]:
        """Generate recommendations for new user.
        
        Args:
            available_restaurants: List of all available restaurants
            local_hour: Current hour for time-based recommendation
            location_trending: Trending cuisines/restaurants in user location
            featured_offers: Current promotional offers
        
        Returns:
            Ranked list of recommendations
        """
        available_restaurants = available_restaurants or []
        location_trending = location_trending or []
        featured_offers = featured_offers or []

        recommendations: List[NewUserRecommendation] = []
        local_hour = local_hour or datetime.utcnow().hour
        time_period = self.get_time_period(local_hour)
        season = self.get_season()

        # 1. Time-based recommendations (highest priority)
        time_prefs = self.time_based_preferences.get(time_period, {})
        time_cuisines = time_prefs.get("cuisines", [])
        time_desc = time_prefs.get("description", "the current time")

        for rest in available_restaurants:
            if rest.get("cuisine") in time_cuisines:
                rec = NewUserRecommendation(
                    restaurant_name=rest.get("name", "Unknown"),
                    cuisine_type=rest.get("cuisine", "Mixed"),
                    reason=f"Perfect choice for {time_desc}",
                    confidence=75.0,
                    category="time_based",
                )
                recommendations.append(rec)
                if len(recommendations) >= 3:
                    break

        # 2. Trending in location (if available)
        if location_trending:
            for trend in location_trending[:2]:
                matching = [
                    r for r in available_restaurants 
                    if trend.lower() in (r.get("cuisine") or "").lower()
                    and r.get("name") not in [rec.restaurant_name for rec in recommendations]
                ]
                for rest in matching[:1]:
                    rec = NewUserRecommendation(
                        restaurant_name=rest.get("name", "Unknown"),
                        cuisine_type=rest.get("cuisine", "Mixed"),
                        reason=f"Trending in your area",
                        confidence=70.0,
                        category="trending",
                    )
                    recommendations.append(rec)

        # 3. Featured offers
        for offer in featured_offers[:2]:
            rest_name = offer.get("restaurant")
            matching = [
                r for r in available_restaurants
                if r.get("name") == rest_name
                and r.get("name") not in [rec.restaurant_name for rec in recommendations]
            ]
            for rest in matching:
                rec = NewUserRecommendation(
                    restaurant_name=rest.get("name", "Unknown"),
                    cuisine_type=rest.get("cuisine", "Mixed"),
                    reason=f"Special offer: {offer.get('description', 'Limited time deal')}",
                    confidence=65.0,
                    category="seasonal",
                )
                recommendations.append(rec)

        # 4. Seasonal recommendations
        seasonal_cuisines = self.seasonal_foods.get(season, [])
        for rest in available_restaurants:
            if (rest.get("cuisine") in seasonal_cuisines 
                and rest.get("name") not in [rec.restaurant_name for rec in recommendations]):
                rec = NewUserRecommendation(
                    restaurant_name=rest.get("name", "Unknown"),
                    cuisine_type=rest.get("cuisine", "Mixed"),
                    reason=f"Seasonal favorite",
                    confidence=68.0,
                    category="seasonal",
                )
                recommendations.append(rec)
                if len([r for r in recommendations if r.category == "seasonal"]) >= 2:
                    break

        # 5. Popular restaurants (fallback)
        if len(recommendations) < 6:
            sorted_by_rating = sorted(
                [r for r in available_restaurants if r.get("name") not in [rec.restaurant_name for rec in recommendations]],
                key=lambda r: (-r.get("rating", 0), -r.get("order_count", 0)),
            )
            for rest in sorted_by_rating[:3]:
                rec = NewUserRecommendation(
                    restaurant_name=rest.get("name", "Unknown"),
                    cuisine_type=rest.get("cuisine", "Mixed"),
                    reason=f"Popular restaurant ({rest.get('order_count', '1000')}+ orders)",
                    confidence=72.0,
                    category="popular",
                )
                recommendations.append(rec)

        # Sort by confidence
        recommendations.sort(key=lambda r: -r.confidence)
        return recommendations[:8]

    def get_onboarding_message(self, local_hour: int | None = None) -> str:
        """Get a personalized onboarding message for new user."""
        local_hour = local_hour or datetime.utcnow().hour
        time_period = self.get_time_period(local_hour)
        season = self.get_season()

        time_descs = {
            "morning": "🌅 Start your day with a delicious breakfast",
            "lunch": "🍽️ Lunchtime! Explore cuisines trending in your area",
            "afternoon": "☕ Time for a quick snack and coffee break",
            "dinner": "🌙 Let's find the perfect dinner for you",
            "late": "🌮 Craving late-night bites? We've got you covered",
            "night": "🌙 Night owl? Check out our late-night specials",
        }

        seasonal_msgs = {
            "summer": "Beat the heat with cool, refreshing meals 🌤️",
            "monsoon": "Monsoon comfort food specials available now 🌧️",
            "winter": "Warm up with our cozy winter favorites ❄️",
            "spring": "Fresh spring specials coming your way 🌸",
        }

        msg = f"Welcome to Saraswati!\n\n{time_descs.get(time_period, 'Welcome!')}\n{seasonal_msgs.get(season, '')}"
        return msg
