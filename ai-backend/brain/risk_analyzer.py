from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple


class RiskAnalyzer:
    """Detects dangerous/illegal behavior and returns protective guidance."""

    def __init__(self) -> None:
        self.block_patterns: List[Tuple[str, List[str]]] = [
            (
                "weapons_and_violence",
                [
                    r"\b(bomb|explosive|pipe\s*bomb|detonator|IED|grenade)\b",
                    r"\b(make\s*a\s*bomb|how\s*to\s*build\s*a\s*bomb)\b",
                    r"\b(attack|kill|murder|assassinate)\b",
                    r"\b(how\s*to\s*hurt)\b",
                ],
            ),
            (
                "cyber_harm",
                [
                    r"\b(hack|hacking|phish|phishing|malware|ransomware|ddos|sql\s*injection)\b",
                    r"\b(how\s*to\s*steal\s*password|steal\s*credentials)\b",
                    r"\b(create\s*virus|write\s*malware|develop\s*malware)\b",
                    r"\b(bypass\s*security|evade\s*detection)\b",
                    r"\b(send\s*phishing\s*emails)\b",
                ],
            ),
            (
                "illegal_goods_services",
                [
                    r"\b(drugs?|cocaine|heroin|meth|LSD|marijuana)\b",
                    r"\b(buy\s*drugs|sell\s*drugs)\b",
                    r"\b(forgery|counterfeit|fake\s*id|passport)\b",
                    r"\b(credit\s*card\s*fraud|carding|identity\s*theft)\b",
                ],
            ),
            (
                "animal_harm",
                [
                    r"\b(hurt\s*an\s*animal|kill\s*an\s*animal|abuse\s*animals)\b",
                    r"\b(animal\s*cruelty)\b",
                ],
            ),
        ]

        self.suspicious_questions: List[re.Pattern[str]] = [
            re.compile(r"\b(how\s*to\s*make\s*\w+\s*weapon)\b", re.I),
            re.compile(r"\b(illegal|unlawful)\b", re.I),
        ]

    def analyze(self, message: str, user_id: str) -> Dict[str, Any]:
        msg = message.lower().strip()
        if not msg:
            return {"blocked": False, "category": "", "reply": ""}

        for category, patterns in self.block_patterns:
            for p in patterns:
                if re.search(p, msg, flags=re.IGNORECASE):
                    return self._blocked_response(category)

        for rp in self.suspicious_questions:
            if rp.search(msg):
                return self._blocked_response("potential_illegal_or_harm")

        return {"blocked": False, "category": "", "reply": ""}

    def _blocked_response(self, category: str) -> Dict[str, Any]:
        if category == "weapons_and_violence":
            reply = (
                "I can’t help with instructions or guidance that could enable violence or weapon-making. "
                "If you’re feeling overwhelmed or angry, step back and consider reaching out for real support. "
                "If you’re in immediate danger, contact local emergency services right now."
            )
        elif category == "cyber_harm":
            reply = (
                "I can’t assist with hacking, phishing, malware creation, or bypassing security. "
                "If your goal is learning, I can help with defensive cybersecurity concepts (secure coding, "
                "threat modeling, and safe lab practice)."
            )
        elif category == "illegal_goods_services":
            reply = (
                "I can’t help with illegal or harmful activities. "
                "If you tell me a legal, ethical goal, I’ll guide you safely."
            )
        elif category == "animal_harm":
            reply = (
                "I can’t help with harming animals. If an animal needs help, contact a local animal welfare "
                "organization or a licensed veterinarian."
            )
        else:
            reply = (
                "I can’t help with content that appears illegal or harmful. "
                "I can still help you with safe, ethical alternatives—tell me your learning goal."
            )

        reply += (
            "\n\nIf you’re in India and this involves safety/legal concerns, consider contacting local authorities or "
            "reputable, official helplines."
        )

        return {"blocked": True, "category": category, "reply": reply}

