from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from .memory import MemoryEngine


class CreativeEngine:
    """Lightweight creative-writing engine.

    Responsibilities:
    - Produce poems, stories, dialogues, letters, speeches, jokes, riddles, and short analyses
    - Respect guest-mode by avoiding long-term personalization unless allowed
    - Use simple, safe heuristics to avoid producing unsafe content
    This is intentionally small and template-driven to stay fast and auditable.
    """

    def __init__(self, storage_path: str) -> None:
        self.memory = MemoryEngine(storage_path=storage_path)

    def _is_guest(self, user_id: str) -> bool:
        return isinstance(user_id, str) and user_id.startswith("guest_")

    def _sanitize_request(self, message: str) -> str:
        # Strip excessive whitespace and limit length
        if not message:
            return ""
        txt = re.sub(r"\s+", " ", message).strip()
        return txt[:2000]

    def _extract_topic(self, prompt: str) -> str:
        if not prompt:
            return "the moment"
        match = re.search(r"(?:about|on|for|of|regarding)\s+([A-Za-z0-9 \-]+)", prompt, flags=re.I)
        if match:
            return match.group(1).strip().rstrip(' .,!')
        return prompt.strip().rstrip(' .,!')

    def _make_poem(self, prompt: str, tone: Optional[str] = None) -> str:
        subject = self._extract_topic(prompt)
        tone = (tone or "gentle").lower()
        if tone in ("sad", "melancholy"):
            return (
                f"Beneath the hush of {subject}, a quiet ache remains,\n"
                "The heart remembers every broken line,\n"
                "Soft words fall through long gray windowpanes,\n"
                "And hope is held in shadows over time."
            )
        if tone in ("joyful", "bright"):
            return (
                f"I write of {subject} in the light of day,\n"
                "Where colors swell like laughter in the air,\n"
                "Each simple breeze invites the soul to play,\n"
                "And every small delight becomes a prayer."
            )
        return (
            f"For {subject} I choose gentle, even words,\n"
            "A measured quiet written just for this,\n"
            "A tender scene where ordinary birds\n"
            "Find rhythm in the ordinary kiss."
        )

    def _make_haiku(self, prompt: str) -> str:
        subject = self._extract_topic(prompt)
        if not subject:
            subject = "a morning"
        return (
            f"{subject} stirs softly,\n"
            "petals open in cool, still light,\n"
            "whispers trace the day."
        )

    def _make_limerick(self, prompt: str) -> str:
        subj = self._extract_topic(prompt).split()[0] if prompt else "a poet"
        return (
            f"There once was a {subj} from the shore,\n"
            "Who polished each line more and more;\n"
            "When the final verse came,\n"
            "It still sounded the same,\n"
            "And the audience begged for encore."
        )

    def _make_sonnet(self, prompt: str, theme: Optional[str] = None) -> str:
        target = self._extract_topic(prompt or theme or "love")
        return (
            f"When twilight folds the day in velvet mist,\n"
            f"I speak of {target} in a softer voice,\n"
            "The world becomes a careful, humming tryst,\n"
            "Where every breath is more than simple choice.\n"
            "The first two lines return in gentle rhyme,\n"
            "A promise held in patterns of the heart,\n"
            "And time moves forward, shaped by measured time,\n"
            "While quiet meanings play their quiet part.\n"
            "The middle section wanders through desire,\n"
            "It opens hidden doors and leaves them wide,\n"
            "A warmth that kindles softly like a fire,\n"
            "A mirror for the truth we try to hide.\n"
            "In final couplet, let the answer stay:\n"
            f"That {target} is what keeps the dark at bay."
        )

    def _rhyme_suffix(self, word: str) -> str:
        # Very naive rhyme suffix: last 3 letters if available
        w = re.sub(r"[^a-zA-Z]", "", (word or "").lower())
        return w[-3:]

    def _end_with_rhyme(self, base: str, rhyme_with: str) -> str:
        # Append a short phrase ending with a word that rhymes (naive suffix match)
        suf = self._rhyme_suffix(rhyme_with)
        if not suf:
            return base
        candidates = [
            f"like {rhyme_with}",
            f"near the {rhyme_with}",
            f"beneath {rhyme_with}",
        ]
        # choose candidate that ends with rhyme_with (best-effort)
        return base + " " + candidates[0]

    def _make_short_story(self, prompt: str, mood: Optional[str] = None) -> str:
        subject = self._extract_topic(prompt)
        protagonist = "they"
        if subject and subject.split():
            protagonist = subject.split()[0]
        mood = (mood or "contemplative").lower()
        opening = (
            f"{protagonist.capitalize()} found the city lit in a strange new way, "
            f"as if {subject} had rewritten the morning. "
        )
        middle = (
            "A small choice carried through the day, "
            "a letter passed, a conversation started. "
        )
        closing = (
            "By dusk the scene had settled into something softer, "
            "a simple proof that even ordinary moments can become a story."
        )
        return opening + middle + closing

    def _make_dialogue(self, prompt: str) -> str:
        subject = self._extract_topic(prompt)
        return (
            f"A: 'When you said {subject}, did you mean it in the old way?'\n"
            "B: 'I meant it in the way that makes us pause and listen.'\n"
            "A: 'That's the kind of question that changes how a day begins.'"
        )

    def _make_letter(self, prompt: str) -> str:
        subject = self._extract_topic(prompt)
        return (
            f"Dear Friend,\n\n"
            f"I wanted to write because {subject} has been on my mind. There is a gentle strength in the ordinary things we share, and I find comfort in the way small moments build into meaning.\n\n"
            "Yours sincerely,\nThe Writer"
        )

    def _make_speech(self, prompt: str) -> str:
        subject = self._extract_topic(prompt)
        return (
            f"Today I want to speak about {subject} — not as an idea, but as something lived and felt.\n"
            "It matters because it shapes the way we show up for one another, and it gives us a language for what we care about.\n"
            "If we can hold that clearly, the rest becomes possible.\n"
        )

    def _make_joke(self, prompt: str) -> str:
        return "Why did the AI cross the road? To get to the other dataset."

    def _analysis_template(self, text: str, kind: str) -> str:
        if kind == "character":
            return (
                f"Character Analysis:\nA close reading of the character reveals motivations rooted in contradictions: "
                "their longing often masks fear, and their bravado hides a careful curiosity. Pay attention to how their choices reflect inner conflict."
            )
        if kind == "film":
            return (
                f"Film Analysis:\nThe film uses recurring visual motifs to reinforce its themes — light and shadow, closed doors, and mirrors. "
                "These elements support a narrative about identity and the cost of secrecy."
            )
        return "Analysis: This text explores themes and structure; consider tone, pacing and recurring symbols."

    def generate(self, user_id: str, message: str, style: Optional[str] = None, topic: Optional[str] = None) -> Dict[str, Any]:
        """Main entry: generate creative output.

        Returns { 'reply': str, 'meta': {...} }
        """
        msg = self._sanitize_request(message)
        # Very small safety heuristic: refuse sexual/explicit prompts
        lowered = msg.lower()
        if any(x in lowered for x in ["porn", "explicit", "sexual", "nsfw"]):
            return {"reply": "I can help with creative writing, but I can't produce explicit adult content. Please provide a safe, non-explicit prompt.", "meta": {"blocked": True}}

        # Detect type heuristically
        style = (style or "").strip().lower()
        kind = None
        if style in ("sonnet", "haiku", "limerick", "poem", "story", "dialogue", "letter", "speech", "joke", "character", "film"):
            kind = style
        elif re.search(r"\b(sonnet)\b", lowered):
            kind = "sonnet"
        elif re.search(r"\b(haiku)\b", lowered):
            kind = "haiku"
        elif re.search(r"\b(limerick)\b", lowered):
            kind = "limerick"
        elif re.search(r"\b(poem|poetry)\b", lowered):
            kind = "poem"
        elif re.search(r"\b(story|short story|novel|narrative)\b", lowered):
            kind = "story"
        elif re.search(r"\b(dialogue|dialog)\b", lowered):
            kind = "dialogue"
        elif re.search(r"\b(letter|dear)\b", lowered):
            kind = "letter"
        elif re.search(r"\b(speech)\b", lowered):
            kind = "speech"
        elif re.search(r"\b(joke|riddle)\b", lowered):
            kind = "joke"
        elif re.search(r"\b(character analysis|character)\b", lowered):
            kind = "character"
        elif re.search(r"\b(film|movie|analysis)\b", lowered):
            kind = "film"
        else:
            # fallback to short story/creative paragraph
            kind = style or "story"

        try:
            if kind == "sonnet":
                reply = self._make_sonnet(prompt=topic or msg, theme=None)
            elif kind == "haiku":
                reply = self._make_haiku(prompt=topic or msg)
            elif kind == "limerick":
                reply = self._make_limerick(prompt=topic or msg)
            elif kind == "poem":
                reply = self._make_poem(prompt=topic or msg, tone=None)
            elif kind == "story":
                reply = self._make_short_story(prompt=topic or msg, mood=None)
            elif kind == "dialogue":
                reply = self._make_dialogue(prompt=topic or msg)
            elif kind == "joke":
                reply = self._make_joke(prompt=topic or msg)
            elif kind in ("character", "film"):
                reply = self._analysis_template(msg, kind)
            else:
                reply = self._make_short_story(prompt=topic or msg, mood=None)
        except Exception:
            reply = "I can help craft creative writing — tell me what genre or tone you'd like."

        return {"reply": reply, "meta": {"kind": kind}}
