from __future__ import annotations

import base64
import hashlib
import urllib.request
from typing import Any, Dict, List, Optional

from .brain.core import CoreBrain
from .image.image_system import analyze_image_fake


class ImageAnalysisService:
    """External image analysis service for Nitro Infinity AI integrations."""

    def __init__(self, brain: CoreBrain) -> None:
        self.brain = brain
        self.authenticator = self.brain.get_engine("image_authenticity")

    @staticmethod
    def _strip_data_url(data: str) -> str:
        if data.startswith("data:") and "," in data:
            return data.split(",", 1)[1]
        return data

    @staticmethod
    def _decode_base64(data: str) -> bytes:
        try:
            return base64.b64decode(ImageAnalysisService._strip_data_url(data), validate=True)
        except Exception as exc:
            raise ValueError("Invalid base64 image data") from exc

    def _fetch_url(self, image_url: str) -> bytes:
        if not image_url.startswith(("http://", "https://")):
            raise ValueError("Unsupported image_url format")
        request = urllib.request.Request(
            image_url,
            headers={"User-Agent": "NitroAI/1.0"},
        )
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                return response.read()
        except Exception as exc:
            raise ValueError(f"Unable to download image from URL: {exc}") from exc

    def _normalize_image_source(
        self,
        image_base64: Optional[str],
        image_url: Optional[str],
    ) -> bytes:
        if image_base64:
            return self._decode_base64(image_base64)
        if image_url:
            return self._fetch_url(image_url)
        raise ValueError("Either image_base64 or image_url is required")

    def analyze(
        self,
        image_base64: Optional[str] = None,
        image_url: Optional[str] = None,
        prompt: Optional[str] = None,
        user_id: Optional[str] = None,
        image_meta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        image_bytes = self._normalize_image_source(image_base64, image_url)
        image_hash = hashlib.sha256(image_bytes).hexdigest()

        if image_meta and self.authenticator:
            result = self.authenticator.analyze(image_hash, image_meta)
            return {
                "image_hash": image_hash,
                "authenticity_class": result.authenticity_class,
                "confidence": float(result.confidence),
                "explanation": result.explanation,
                "risk_flags": result.risk_flags,
                "analysis_source": "image_authenticity_engine",
            }

        encoded_image = base64.b64encode(image_bytes).decode("ascii")
        analysis = analyze_image_fake(encoded_image, prompt or "")
        ai_probability = float(analysis["analysis"].get("ai_probability", 0.0))
        human_probability = float(analysis["analysis"].get("human_probability", 0.0))
        likely_label = str(analysis["analysis"].get("likely_label", "unknown"))
        confidence = round(max(ai_probability, human_probability) * 100.0, 1)
        risk_flags = ["likely_edit"] if "edited" in likely_label.lower() or "mixed" in likely_label.lower() else []

        return {
            "image_hash": image_hash,
            "authenticity_class": likely_label,
            "confidence": confidence,
            "explanation": f"Heuristic image analysis returned '{likely_label}'.",
            "risk_flags": risk_flags,
            "analysis_source": "heuristic_image_analysis",
            "raw_analysis": analysis["analysis"],
        }


class FoodRecommendationService:
    """Food recommendation service for integration endpoints."""

    def __init__(self, brain: CoreBrain) -> None:
        self.brain = brain

    def recommend(
        self,
        user_id: str,
        available_restaurants: Optional[List[Dict[str, Any]]] = None,
        local_hour: Optional[int] = None,
        location: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not user_id:
            raise ValueError("user_id is required")

        engine = self.brain.get_engine("food_recommendation")
        if engine is None:
            raise RuntimeError("Food recommendation engine not available")

        recommendations = engine.recommend(
            user_id=user_id,
            available_restaurants=available_restaurants or [],
            local_hour=local_hour,
            location=location,
        )

        ads = engine.get_personalized_ads(user_id)
        return {
            "recommendations": [
                {
                    "restaurant_id": recommendation.restaurant_id,
                    "restaurant_name": recommendation.restaurant_name,
                    "cuisine_type": recommendation.cuisine_type,
                    "reason": recommendation.reason,
                    "confidence": recommendation.confidence,
                    "offer": recommendation.offer,
                    "estimated_delivery_time": recommendation.estimated_delivery_time,
                    "rating": recommendation.rating,
                }
                for recommendation in recommendations
            ],
            "ads": ads or [],
            "user_id": user_id,
        }
