"""
ai-backend/app/api/providers.py

Provider registry & 16-agent free-tier architecture catalog for Nitro Infinity AI.
Maps every specialized capability to zero-cost, open-source, or free-tier models.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1", tags=["providers"])


class ProviderModelInfo(BaseModel):
    modelId: str
    displayName: str
    isDefault: bool = False
    contextWindow: Optional[int] = None
    description: Optional[str] = None
    freeTier: bool = True
    recommendedFor: Optional[List[str]] = None


class ProviderInfo(BaseModel):
    providerId: str
    displayName: str
    description: str
    requiresApiKey: bool
    envKeyName: Optional[str] = None
    isDefault: bool
    capabilities: List[str]
    defaultModel: str
    availableModels: List[ProviderModelInfo]


# ============================================================================
# 16-AGENT SPECIALIST ROLES REGISTRY (100% FREE & OPEN-SOURCE MATRIX)
# ============================================================================
SPECIALIZED_AGENT_MATRIX: List[Dict[str, Any]] = [
    {
        "roleId": "image_generator",
        "name": "1. Image Generation Studio",
        "providerId": "huggingface",
        "modelId": "black-forest-labs/FLUX.1-schnell",
        "freeTierSource": "Hugging Face Free Inference API / Local SVG",
        "envKey": "HUGGINGFACE_API_KEY",
    },
    {
        "roleId": "general_chat",
        "name": "2. Normal Chat & Conversation",
        "providerId": "groq",
        "modelId": "llama-3.3-70b-versatile",
        "freeTierSource": "Groq Free Tier / OpenRouter Free Tier",
        "envKey": "GROQ_API_KEY",
    },
    {
        "roleId": "coding_specialist",
        "name": "3. Coding & Software Architecture",
        "providerId": "openrouter",
        "modelId": "qwen/qwen-2.5-coder-32b-instruct:free",
        "freeTierSource": "OpenRouter Free Tier (Qwen 2.5 Coder 32B / DeepSeek)",
        "envKey": "OPENROUTER_API_KEY",
    },
    {
        "roleId": "english_grammar",
        "name": "4. English Grammar & Writing Coach",
        "providerId": "gemini",
        "modelId": "gemini-1.5-flash",
        "freeTierSource": "Google AI Studio Free Tier",
        "envKey": "GOOGLE_AI_STUDIO_API_KEY",
    },
    {
        "roleId": "math_logic",
        "name": "5. Math & Complex Logic Reasoning",
        "providerId": "openrouter",
        "modelId": "deepseek/deepseek-r1:free",
        "freeTierSource": "OpenRouter Free Tier (DeepSeek-R1 Distill Llama 70B)",
        "envKey": "OPENROUTER_API_KEY",
    },
    {
        "roleId": "hindi_grammar",
        "name": "6. Hindi Grammar & Multilingual Studies",
        "providerId": "gemini",
        "modelId": "gemini-1.5-flash",
        "freeTierSource": "Google AI Studio Free Tier",
        "envKey": "GOOGLE_AI_STUDIO_API_KEY",
    },
    {
        "roleId": "sst_science",
        "name": "7. SST & Science Educator",
        "providerId": "gemini",
        "modelId": "gemini-1.5-flash",
        "freeTierSource": "Google AI Studio Free Tier",
        "envKey": "GOOGLE_AI_STUDIO_API_KEY",
    },
    {
        "roleId": "evaluator_quiz",
        "name": "8. Quiz & Mock Test Generator (The Evaluator)",
        "providerId": "gemini",
        "modelId": "gemini-1.5-flash",
        "freeTierSource": "Google AI Studio Free Tier",
        "envKey": "GOOGLE_AI_STUDIO_API_KEY",
    },
    {
        "roleId": "grader_evaluator",
        "name": "9. Essay & Answer Evaluator (The Grader)",
        "providerId": "openrouter",
        "modelId": "deepseek/deepseek-r1:free",
        "freeTierSource": "OpenRouter Free Tier (DeepSeek-R1)",
        "envKey": "OPENROUTER_API_KEY",
    },
    {
        "roleId": "career_counselor",
        "name": "10. Career Counselor & Syllabus Planner",
        "providerId": "gemini",
        "modelId": "gemini-1.5-flash",
        "freeTierSource": "Google AI Studio Free Tier",
        "envKey": "GOOGLE_AI_STUDIO_API_KEY",
    },
    {
        "roleId": "oral_examiner",
        "name": "11. Speech-to-Text & Pronunciation (The Oral Examiner)",
        "providerId": "groq",
        "modelId": "whisper-large-v3-turbo",
        "freeTierSource": "GroqCloud Free Tier Whisper",
        "envKey": "GROQ_API_KEY",
    },
    {
        "roleId": "file_reader",
        "name": "12. Document & PDF Parsing (The File Reader)",
        "providerId": "gemini",
        "modelId": "gemini-1.5-flash",
        "freeTierSource": "Google AI Studio Free Tier (1M Context)",
        "envKey": "GOOGLE_AI_STUDIO_API_KEY",
    },
    {
        "roleId": "researcher_web",
        "name": "13. Live Web Search & Fact-Checking (The Researcher)",
        "providerId": "nitro-brain",
        "modelId": "duckduckgo-free-search",
        "freeTierSource": "Built-in Free DuckDuckGo Scraper",
        "envKey": None,
    },
    {
        "roleId": "code_sandbox",
        "name": "14. Code Execution & Graph Runner",
        "providerId": "nitro-brain",
        "modelId": "local-python-sandbox",
        "freeTierSource": "Local Python Runtime & MathEngine",
        "envKey": None,
    },
    {
        "roleId": "voice_reader",
        "name": "15. Text-to-Speech (The Voice Reader)",
        "providerId": "nitro-brain",
        "modelId": "edge-tts-free",
        "freeTierSource": "Edge-TTS / Piper Local Free Engine",
        "envKey": None,
    },
    {
        "roleId": "vector_memory",
        "name": "16. Vector Embeddings & Memory",
        "providerId": "gemini",
        "modelId": "text-embedding-004",
        "freeTierSource": "Google AI Studio Free Tier",
        "envKey": "GOOGLE_AI_STUDIO_API_KEY",
    },
]

# ============================================================================
# PROVIDER CATALOG WITH FREE TIER SPECS
# ============================================================================
_PROVIDER_CATALOG: List[Dict[str, Any]] = [
    {
        "providerId": "nitro",
        "displayName": "Nitro AI (Auto Free Cloud)",
        "description": "Nitro's automated zero-cost pipeline with intelligent failover between free-tier providers.",
        "requiresApiKey": False,
        "envKeyName": "NITRO_SYSTEM_API_KEY",
        "isDefault": True,
        "capabilities": ["chat", "streaming", "math", "coding"],
        "defaultModel": "meta-llama/llama-3.3-70b-instruct:free",
        "availableModels": [
            {
                "modelId": "meta-llama/llama-3.3-70b-instruct:free",
                "displayName": "Llama 3.3 70B (Free Tier)",
                "isDefault": True,
                "contextWindow": 128000,
                "description": "High intelligence general conversation",
                "freeTier": True,
                "recommendedFor": ["Normal Chat", "SST & Science"],
            },
        ],
    },
    {
        "providerId": "gemini",
        "displayName": "Google AI Studio (Gemini 1.5 Flash Free)",
        "description": "Google AI Studio free tier. Fast 1M token multimodal context for grammar, syllabus planning, and parsing.",
        "requiresApiKey": True,
        "envKeyName": "GOOGLE_AI_STUDIO_API_KEY",
        "isDefault": False,
        "capabilities": ["chat", "streaming", "document-parsing", "grammar", "embeddings"],
        "defaultModel": "gemini-1.5-flash",
        "availableModels": [
            {
                "modelId": "gemini-1.5-flash",
                "displayName": "Gemini 1.5 Flash (Free Tier)",
                "isDefault": True,
                "contextWindow": 1048576,
                "description": "Fast multimodal model for grammar, tests, document reading, and planning",
                "freeTier": True,
                "recommendedFor": [
                    "English Grammar",
                    "Hindi Grammar",
                    "SST and Science",
                    "Quiz Generator",
                    "Career Counselor",
                    "Document & PDF Parsing",
                ],
            },
            {
                "modelId": "text-embedding-004",
                "displayName": "Text Embedding 004 (Free Tier)",
                "isDefault": False,
                "contextWindow": 2048,
                "description": "High-density vector embeddings for semantic memory",
                "freeTier": True,
                "recommendedFor": ["Vector Embeddings & Semantic Search"],
            },
        ],
    },
    {
        "providerId": "groq",
        "displayName": "GroqCloud (LPUs Free Tier)",
        "description": "Ultra low-latency open model inference and Whisper audio transcriptions on Groq LPUs.",
        "requiresApiKey": True,
        "envKeyName": "GROQ_API_KEY",
        "isDefault": False,
        "capabilities": ["chat", "streaming", "stt"],
        "defaultModel": "llama-3.3-70b-versatile",
        "availableModels": [
            {
                "modelId": "llama-3.3-70b-versatile",
                "displayName": "Llama 3.3 70B Versatile (Free)",
                "isDefault": True,
                "contextWindow": 128000,
                "description": "High-throughput reasoning and dialogue",
                "freeTier": True,
                "recommendedFor": ["Normal Chat", "Concept Explanation"],
            },
            {
                "modelId": "llama-3.1-8b-instant",
                "displayName": "Llama 3.1 8B Instant (Free)",
                "isDefault": False,
                "contextWindow": 128000,
                "description": "Instant generation for quick answers",
                "freeTier": True,
                "recommendedFor": ["Fast Dialogues"],
            },
            {
                "modelId": "whisper-large-v3-turbo",
                "displayName": "Whisper Large V3 Turbo (Free STT)",
                "isDefault": False,
                "contextWindow": 448,
                "description": "State-of-the-art speech-to-text transcription",
                "freeTier": True,
                "recommendedFor": ["Speech-to-Text & Pronunciation"],
            },
        ],
    },
    {
        "providerId": "openrouter",
        "displayName": "OpenRouter (Free Tier Hub)",
        "description": "Access zero-cost open models: DeepSeek-R1 reasoning, Qwen 2.5 Coder, and Llama 3.",
        "requiresApiKey": False,
        "envKeyName": "OPENROUTER_API_KEY",
        "isDefault": False,
        "capabilities": ["chat", "streaming", "reasoning", "coding"],
        "defaultModel": "deepseek/deepseek-r1:free",
        "availableModels": [
            {
                "modelId": "deepseek/deepseek-r1:free",
                "displayName": "DeepSeek R1 (Free Reasoning)",
                "isDefault": True,
                "contextWindow": 64000,
                "description": "Chain-of-thought mathematical reasoning and code evaluation",
                "freeTier": True,
                "recommendedFor": ["Math & Complex Logic", "Essay & Answer Evaluator"],
            },
            {
                "modelId": "qwen/qwen-2.5-coder-32b-instruct:free",
                "displayName": "Qwen 2.5 Coder 32B (Free)",
                "isDefault": False,
                "contextWindow": 32768,
                "description": "Leading open coding specialist",
                "freeTier": True,
                "recommendedFor": ["Coding & Architecture"],
            },
            {
                "modelId": "meta-llama/llama-3.3-70b-instruct:free",
                "displayName": "Meta Llama 3.3 70B (Free)",
                "isDefault": False,
                "contextWindow": 128000,
                "description": "General conversational open model",
                "freeTier": True,
                "recommendedFor": ["Normal Chat"],
            },
        ],
    },
    {
        "providerId": "huggingface",
        "displayName": "Hugging Face (Free Inference API)",
        "description": "Zero-cost image generation and open models via Hugging Face Serverless API.",
        "requiresApiKey": True,
        "envKeyName": "HUGGINGFACE_API_KEY",
        "isDefault": False,
        "capabilities": ["image-generation", "chat"],
        "defaultModel": "black-forest-labs/FLUX.1-schnell",
        "availableModels": [
            {
                "modelId": "black-forest-labs/FLUX.1-schnell",
                "displayName": "FLUX.1 Schnell (Free)",
                "isDefault": True,
                "contextWindow": 1024,
                "description": "Ultra fast high quality image synthesis",
                "freeTier": True,
                "recommendedFor": ["Image Generation Studio"],
            },
            {
                "modelId": "stabilityai/stable-diffusion-3.5-large",
                "displayName": "Stable Diffusion 3.5 Large (Free)",
                "isDefault": False,
                "contextWindow": 1024,
                "description": "Photorealistic open weights image generator",
                "freeTier": True,
                "recommendedFor": ["Image Generation Studio"],
            },
        ],
    },
    {
        "providerId": "nitro-brain",
        "displayName": "Nitro Full Brain (100% Local & Free)",
        "description": "Offline local engine: MathEngine, DuckDuckGo researcher, Edge-TTS/Piper, and memory graph.",
        "requiresApiKey": False,
        "envKeyName": None,
        "isDefault": False,
        "capabilities": [
            "chat",
            "streaming",
            "education",
            "memory",
            "math",
            "coding",
            "puzzle",
            "web-research",
            "tts",
        ],
        "defaultModel": "nitro-brain-v1",
        "availableModels": [
            {
                "modelId": "nitro-brain-v1",
                "displayName": "Nitro Brain Engine (Local)",
                "isDefault": True,
                "contextWindow": 8192,
                "description": "Built-in local heuristics, math solver, and DuckDuckGo researcher",
                "freeTier": True,
                "recommendedFor": [
                    "Live Web Search",
                    "Code Execution Sandbox",
                    "Text-to-Speech",
                    "Offline Mode",
                ],
            },
        ],
    },
]


@router.get("/providers", response_model=Dict[str, Any])
def list_providers() -> Dict[str, Any]:
    """Returns the free-tier provider catalog and the 16-role specialist matrix."""
    return {
        "providers": _PROVIDER_CATALOG,
        "agentMatrix": SPECIALIZED_AGENT_MATRIX,
        "freeTierGuaranteed": True,
    }


@router.get("/providers/{provider_id}", response_model=Dict[str, Any])
def get_provider_details(provider_id: str) -> Dict[str, Any]:
    """Returns metadata and free model listings for a specific provider."""
    normalized_id = provider_id.strip().lower()
    for provider in _PROVIDER_CATALOG:
        if provider["providerId"] == normalized_id:
            return {"provider": provider}
    raise HTTPException(status_code=404, detail=f"Provider '{provider_id}' not found.")


@router.get("/agents/matrix", response_model=Dict[str, Any])
def get_agent_matrix() -> Dict[str, Any]:
    """Returns the complete mapping of all 16 specialized agents to free providers."""
    return {
        "rolesCount": len(SPECIALIZED_AGENT_MATRIX),
        "roles": SPECIALIZED_AGENT_MATRIX,
        "keysRequired": [
            {"key": "GOOGLE_AI_STUDIO_API_KEY", "optional": True, "description": "Google Gemini 1.5 Flash Free Tier"},
            {"key": "GROQ_API_KEY", "optional": True, "description": "GroqCloud Llama 3.3 & Whisper Free Tier"},
            {"key": "OPENROUTER_API_KEY", "optional": True, "description": "OpenRouter Free DeepSeek-R1 & Qwen Coder"},
            {"key": "HUGGINGFACE_API_KEY", "optional": True, "description": "Hugging Face Free Inference API"},
        ],
    }