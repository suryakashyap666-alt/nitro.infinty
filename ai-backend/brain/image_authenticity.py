"""Image Authenticity Analyzer for Saraswati Food Delivery.

Detects AI-generated, edited, and authentic images.
Used for refund claims, reviews, and rating validation.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from typing import Any, Dict
import hashlib
import re


@dataclass
class AuthenticityResult:
    """Result of authenticity analysis."""
    authenticity_class: str  # "Likely Authentic" | "Likely AI Generated" | "Likely Edited/Manipulated"
    confidence: float  # 0.0-100.0
    explanation: str
    risk_flags: list[str]  # List of detected risk factors


class ImageAuthenticityAnalyzer:
    """Analyze images for authenticity, AI generation, and manipulation.
    
    Lightweight heuristic-based analysis (no heavy ML models for speed).
    Flags suspicious patterns, compression artifacts, metadata anomalies.
    """

    def __init__(self, storage_path: str) -> None:
        self.storage_path = storage_path
        self._ensure_storage()

    def _ensure_storage(self) -> None:
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        if not os.path.exists(self.storage_path):
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump({"analyses": {}}, f)

    def analyze(self, image_hash: str, image_meta: Dict[str, Any] | None = None) -> AuthenticityResult:
        """Analyze image for authenticity.
        
        Args:
            image_hash: hash of image for lookup/caching
            image_meta: metadata dict with optional 'size', 'format', 'metadata_tags', 'anomalies'
        
        Returns:
            AuthenticityResult with classification and confidence
        """
        image_meta = image_meta or {}
        risk_flags = []
        ai_score = 0.0
        edited_score = 0.0

        # Check size anomalies (very small or suspiciously uniform)
        size = image_meta.get("size", 0)
        if size < 5000:  # < 5KB is suspicious for food image
            risk_flags.append("suspiciously_small_file")
            ai_score += 15
        if size > 50_000_000:  # > 50MB is unusual
            risk_flags.append("unusually_large_file")
            edited_score += 10

        # Check metadata (AI-generated images often lack EXIF)
        has_exif = image_meta.get("has_exif", False)
        metadata_tags = image_meta.get("metadata_tags", [])
        if not has_exif and not metadata_tags:
            risk_flags.append("missing_camera_metadata")
            ai_score += 20
        if has_exif:
            exif_data = image_meta.get("exif_data", {})
            if not exif_data.get("camera_model"):
                risk_flags.append("generic_camera_data")
                ai_score += 10

        # Check for editing software markers
        software_markers = ["photoshop", "gimp", "affinity", "capture one", "lightroom"]
        for tag in metadata_tags:
            tag_lower = (tag or "").lower()
            if any(marker in tag_lower for marker in software_markers):
                risk_flags.append("editing_software_detected")
                edited_score += 25
                break

        # Analyze color patterns (AI-generated often have unnatural color gradients)
        colors = image_meta.get("color_analysis", {})
        saturation = colors.get("avg_saturation", 0)
        if saturation > 85:  # Unnaturally saturated
            risk_flags.append("unnatural_color_saturation")
            ai_score += 15

        hue_variance = colors.get("hue_variance", 0)
        if hue_variance < 0.3:  # Suspiciously uniform hues
            risk_flags.append("uniform_hues")
            ai_score += 12

        # Check for common AI generation patterns
        anomalies = image_meta.get("anomalies", [])
        ai_patterns = ["unrealistic_blur", "pixel_duplication", "unnatural_symmetry", 
                       "blend_errors", "text_distortion"]
        for pattern in ai_patterns:
            if pattern in anomalies:
                risk_flags.append(pattern)
                ai_score += 18

        # Check for manipulation patterns
        edit_patterns = ["cloning", "healing_traces", "unnatural_edges", "compression_artifacts"]
        for pattern in edit_patterns:
            if pattern in anomalies:
                risk_flags.append(pattern)
                edited_score += 15

        # Determine final classification
        if ai_score > edited_score and ai_score > 40:
            authenticity_class = "Likely AI Generated"
            confidence = min(95, 30 + ai_score)
            explanation = f"Detected {len([f for f in risk_flags if 'ai' in f or 'blur' in f or 'symmetry' in f])} AI generation indicators."
        elif edited_score > ai_score and edited_score > 35:
            authenticity_class = "Likely Edited/Manipulated"
            confidence = min(95, 30 + edited_score)
            explanation = f"Found evidence of post-processing and manipulation ({len([f for f in risk_flags if 'editing' in f or 'cloning' in f or 'healing' in f])} factors)."
        else:
            authenticity_class = "Likely Authentic"
            confidence = min(95, max(60, 100 - ai_score - edited_score))
            explanation = "Image appears authentic with expected camera metadata and natural characteristics."

        result = AuthenticityResult(
            authenticity_class=authenticity_class,
            confidence=confidence,
            explanation=explanation,
            risk_flags=risk_flags,
        )

        # Cache result
        try:
            self._cache_result(image_hash, asdict(result))
        except Exception:
            pass

        return result

    def _cache_result(self, image_hash: str, result: Dict[str, Any]) -> None:
        """Store analysis result for future queries."""
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {"analyses": {}}

        data.setdefault("analyses", {})[image_hash] = {
            "result": result,
            "timestamp": str(__import__("datetime").datetime.utcnow().isoformat()),
        }

        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_cached_result(self, image_hash: str) -> AuthenticityResult | None:
        """Retrieve cached analysis result."""
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            entry = data.get("analyses", {}).get(image_hash)
            if entry:
                result_dict = entry.get("result", {})
                return AuthenticityResult(
                    authenticity_class=result_dict.get("authenticity_class", "Unknown"),
                    confidence=result_dict.get("confidence", 0),
                    explanation=result_dict.get("explanation", ""),
                    risk_flags=result_dict.get("risk_flags", []),
                )
        except Exception:
            pass
        return None
