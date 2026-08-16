"""
Nitro Voice: Built-in voice synthesis engine for Nitro Infinity AI.

Supports offline speech synthesis with:
- Piper (default, optimized for 4GB RAM systems)
- Placeholders: Coqui XTTS, OpenVoice, F5-TTS (future implementation)

Features:
- Automatic provider detection and fallback
- Graceful degradation on failure
- Language-aware voice selection
- Base64 audio encoding
"""

from __future__ import annotations

import base64
import io
import logging
import os
from typing import Any, Dict, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class VoiceProvider(Enum):
    """Supported voice synthesis providers."""
    PIPER = "piper"
    COQUI_XTTS = "coqui_xtts"  # Placeholder
    OPENVOICE = "openvoice"    # Placeholder
    F5_TTS = "f5_tts"          # Placeholder


class PiperVoiceEngine:
    """
    Piper TTS engine: Offline, lightweight, optimized for 4GB RAM systems.
    
    Installation:
        pip install piper-tts
    
    Voice models are auto-downloaded on first use to ~/.local/share/piper_tts/
    """

    def __init__(self):
        self.engine = None
        self.voices = {}
        self._initialized = False
        self._init_lock = False
        
    def _lazy_init(self) -> bool:
        """Lazy initialization of Piper engine."""
        if self._initialized or self._init_lock:
            return self._initialized
            
        self._init_lock = True
        try:
            import piper
            self.engine = piper
            self._initialized = True
            logger.info("Piper voice engine initialized successfully")
            return True
        except ImportError:
            logger.debug("Piper not installed. Install with: pip install piper-tts")
            return False
        except Exception as e:
            logger.debug(f"Piper initialization failed: {e}")
            return False
        finally:
            self._init_lock = False

    def synthesize(self, text: str, language: str = "en") -> Optional[bytes]:
        """
        Synthesize speech from text using Piper.
        
        Args:
            text: Text to synthesize
            language: Language code (en, hi, ja, es, fr, de, pt, tr, it, ar, bn, ta, te, ur, zh, ru)
            
        Returns:
            WAV audio bytes or None on failure
        """
        if not text or not isinstance(text, str):
            return None
            
        if not self._lazy_init():
            return None

        try:
            # Map language codes to Piper voice models
            voice_map = {
                "en": "en_US-amy-medium",
                "hi": "hi_IN-google-medium",
                "ja": "ja_JP-google-medium",
                "es": "es_ES-carlfm-x-low",
                "fr": "fr_FR-siwis-medium",
                "de": "de_DE-eva_k-x-low",
                "pt": "pt_BR-edresson-medium",
                "ar": "ar_JO-kareem-medium",
                "tr": "tr_TR-dfki-medium",
                "it": "it_IT-riccardo-x-low",
                "bn": "bn_IN-bangla-medium",
                "ta": "ta_IN-google-medium",
                "te": "te_IN-google-medium",
                "ur": "ur_PK-google-medium",
                "zh": "zh_CN-huayan-medium",
                "ru": "ru_RU-denis-medium",
            }
            
            voice_name = voice_map.get(language, "en_US-amy-medium")
            
            # Synthesize using Piper
            try:
                # Try new Piper API
                from piper import PiperTTS
                tts = PiperTTS(voice_name=voice_name)
                wav_bytes = tts.synthesize(text)
                if isinstance(wav_bytes, bytes):
                    return wav_bytes
                if hasattr(wav_bytes, "read"):
                    return wav_bytes.read()
            except Exception as primary_error:
                logger.debug(f"Piper synthesis failed for voice: {voice_name}: {primary_error}")

            # Try the general piper module fallback patterns.
            try:
                if self.engine is not None:
                    if hasattr(self.engine, "PiperTTS"):
                        tts = self.engine.PiperTTS(voice_name=voice_name)
                        wav_bytes = tts.synthesize(text)
                        if isinstance(wav_bytes, bytes):
                            return wav_bytes
                        if hasattr(wav_bytes, "read"):
                            return wav_bytes.read()

                    if hasattr(self.engine, "Piper"):
                        tts = self.engine.Piper(voice_name=voice_name)
                        if hasattr(tts, "synthesize"):
                            wav_bytes = tts.synthesize(text)
                            if isinstance(wav_bytes, bytes):
                                return wav_bytes
                            if hasattr(wav_bytes, "read"):
                                return wav_bytes.read()

                    if hasattr(self.engine, "text_to_speech"):
                        wav_bytes = self.engine.text_to_speech(text=text, voice=voice_name)
                        if isinstance(wav_bytes, bytes):
                            return wav_bytes
                        if hasattr(wav_bytes, "read"):
                            return wav_bytes.read()

                    if hasattr(self.engine, "tts"):
                        wav_bytes = self.engine.tts(text=text, voice=voice_name)
                        if isinstance(wav_bytes, bytes):
                            return wav_bytes
                        if hasattr(wav_bytes, "read"):
                            return wav_bytes.read()
            except Exception as fallback_error:
                logger.debug(f"Piper fallback synthesis failed for voice: {voice_name}: {fallback_error}")

            return None
        except Exception as e:
            logger.debug(f"Piper synthesis error: {e}")
            return None

    def is_available(self) -> bool:
        """Check if Piper is available."""
        return self._lazy_init()


class CoquiXTTSVoiceEngine:
    """Placeholder for Coqui XTTS voice engine (future implementation)."""
    
    def synthesize(self, text: str, language: str = "en") -> Optional[bytes]:
        """Placeholder."""
        logger.debug("Coqui XTTS: Not implemented yet")
        return None
        
    def is_available(self) -> bool:
        """Placeholder always returns False."""
        return False


class OpenVoiceEngine:
    """Placeholder for OpenVoice engine (future implementation)."""
    
    def synthesize(self, text: str, language: str = "en") -> Optional[bytes]:
        """Placeholder."""
        logger.debug("OpenVoice: Not implemented yet")
        return None
        
    def is_available(self) -> bool:
        """Placeholder always returns False."""
        return False


class F5TTSEngine:
    """Placeholder for F5-TTS engine (future implementation)."""
    
    def synthesize(self, text: str, language: str = "en") -> Optional[bytes]:
        """Placeholder."""
        logger.debug("F5-TTS: Not implemented yet")
        return None
        
    def is_available(self) -> bool:
        """Placeholder always returns False."""
        return False


class NitroVoiceSystem:
    """
    Main Nitro Voice System: Orchestrates voice synthesis with automatic fallback.
    
    Priority order (fallback chain):
    1. Piper (default, offline, 4GB RAM optimized)
    2. Coqui XTTS (placeholder)
    3. OpenVoice (placeholder)
    4. F5-TTS (placeholder)
    """

    def __init__(self):
        self.piper = PiperVoiceEngine()
        self.coqui_xtts = CoquiXTTSVoiceEngine()
        self.openvoice = OpenVoiceEngine()
        self.f5_tts = F5TTSEngine()
        self.active_provider: Optional[VoiceProvider] = None
        
    def _get_provider_engine(self, provider: VoiceProvider) -> Optional[Any]:
        """Get engine instance for a provider."""
        engines = {
            VoiceProvider.PIPER: self.piper,
            VoiceProvider.COQUI_XTTS: self.coqui_xtts,
            VoiceProvider.OPENVOICE: self.openvoice,
            VoiceProvider.F5_TTS: self.f5_tts,
        }
        return engines.get(provider)

    def synthesize_to_base64(
        self,
        text: str,
        language: str = "en",
        provider: Optional[VoiceProvider] = None,
    ) -> Optional[str]:
        """
        Synthesize text to speech and return as base64-encoded WAV.
        
        Args:
            text: Text to synthesize
            language: Language code
            provider: Preferred provider (uses fallback chain if None)
            
        Returns:
            Base64-encoded WAV audio or None if synthesis fails
        """
        if not text or not isinstance(text, str):
            return None

        # Sanitize text
        text = text.strip()
        if len(text) > 5000:
            text = text[:5000]  # Cap at 5000 chars

        # Normalize language code
        language = str(language or "en").lower()[:2]
        
        # Attempt synthesis with provider priority
        providers_to_try = (
            [provider] if provider else []
        ) + [
            VoiceProvider.PIPER,
            VoiceProvider.COQUI_XTTS,
            VoiceProvider.OPENVOICE,
            VoiceProvider.F5_TTS,
        ]

        audio_bytes = None
        successful_provider = None

        for prov in providers_to_try:
            if prov is None:
                continue
                
            try:
                engine = self._get_provider_engine(prov)
                if not engine or not engine.is_available():
                    continue

                audio_bytes = engine.synthesize(text, language)
                if audio_bytes:
                    successful_provider = prov
                    self.active_provider = prov
                    logger.info(f"Voice synthesis successful with {prov.value}")
                    break
                    
            except Exception as e:
                logger.debug(f"Provider {prov.value} failed: {e}")
                continue

        if not audio_bytes:
            logger.warning(f"All voice providers failed to synthesize text")
            return None

        # Encode to base64
        try:
            audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
            return audio_b64
        except Exception as e:
            logger.error(f"Failed to encode audio to base64: {e}")
            return None

    def get_active_provider(self) -> Optional[str]:
        """Get currently active provider name."""
        return self.active_provider.value if self.active_provider else None

    def is_available(self) -> bool:
        """Check if any voice provider is available."""
        return any([
            self.piper.is_available(),
            self.coqui_xtts.is_available(),
            self.openvoice.is_available(),
            self.f5_tts.is_available(),
        ])


# Global instance
_nitro_voice: Optional[NitroVoiceSystem] = None


def get_nitro_voice() -> NitroVoiceSystem:
    """Get or initialize global Nitro Voice system."""
    global _nitro_voice
    if _nitro_voice is None:
        _nitro_voice = NitroVoiceSystem()
    return _nitro_voice


def synthesize_to_base64(
    text: str,
    language: str = "en",
    provider: Optional[str] = None,
) -> Optional[str]:
    """
    Convenience function to synthesize text to base64 audio.
    
    Args:
        text: Text to synthesize
        language: Language code
        provider: Preferred provider name (piper, coqui_xtts, openvoice, f5_tts)
        
    Returns:
        Base64-encoded WAV audio or None on failure
    """
    try:
        prov_enum = None
        if provider:
            try:
                prov_enum = VoiceProvider[provider.upper()]
            except (KeyError, AttributeError):
                logger.warning(f"Unknown provider: {provider}, using auto-fallback")

        voice_system = get_nitro_voice()
        return voice_system.synthesize_to_base64(text, language, prov_enum)
    except Exception as e:
        logger.error(f"Voice synthesis error: {e}")
        return None
