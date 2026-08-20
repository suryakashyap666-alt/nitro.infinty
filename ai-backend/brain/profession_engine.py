from __future__ import annotations

import re
from typing import Callable, Dict, List, Optional

PROFESSION_NAMES: List[str] = [
    "Accountant", "Actor", "Aerospace Engineer", "Agricultural Engineer", "Agronomist",
    "Air Traffic Controller", "Aircraft Mechanic", "Animator", "Anthropologist", "Architect",
    "Astronomer", "Auditor", "Automotive Mechanic", "Biochemist", "Biomedical Engineer",
    "Biologist", "Botanist", "Chemical Engineer", "Chemist", "CEO", "CTO", "Civil Engineer",
    "Clinical Psychologist", "Composer", "Computer Programmer", "Cybersecurity Analyst",
    "Data Analyst", "Data Scientist", "Database Administrator", "Dentist", "Dietitian",
    "Digital Marketer", "Doctor", "Economist", "Editor", "Electrician", "Environmental Engineer",
    "Epidemiologist", "Financial Analyst", "Firefighter", "Graphic Designer", "HR Specialist",
    "HVAC Technician", "Illustrator", "Industrial Designer", "Information Security Analyst",
    "Investment Banker", "Journalist", "Lawyer", "Librarian", "Machinist", "Marine Biologist",
    "Marketing Manager", "Materials Scientist", "Mathematician", "Mechanical Engineer",
    "Microbiologist", "Musician", "Network Administrator", "Neurologist", "Nurse",
    "Nutritionist", "Operations Manager", "Paramedic", "Pathologist", "Pharmacist",
    "Photographer", "Physical Therapist", "Physician", "Physicist", "Pilot", "Plumber",
    "Police Officer", "Product Manager", "Professor", "Project Manager", "Psychologist",
    "QA Engineer", "Radiologist", "Registered Nurse", "Research Scientist", "Sales Manager",
    "Software Developer", "Software Engineer", "Statistician", "Structural Engineer",
    "Supply Chain Manager", "Surgeon", "Teacher", "Technical Writer", "UI/UX Designer",
    "Urban Planner", "Veterinarian", "Web Developer", "Zoologist",
]

PROFESSION_MAP: Dict[str, str] = {name.lower(): name for name in PROFESSION_NAMES}


class ProfessionEngine:
    """Profession intelligence engine for career guidance, workflows, tools, and skills."""

    def detect_profession(self, message: str) -> Optional[str]:
        low = (message or "").lower()
        for phrase, canonical in PROFESSION_MAP.items():
            if phrase in low:
                return canonical
        return None

    def handle_profession_message(self, message: str, user_state: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        detected = self.detect_profession(message)
        if not detected:
            if any(k in message.lower() for k in ["career", "workflow", "job", "profession", "interview", "resume"]):
                return {
                    "reply": (
                        "### 💼 Nitro Career & Workflow Intelligence\n\n"
                        "Tell me your target profession or role, and I will tailor a complete daily workflow checklist, "
                        "recommended software stack, interview preparation guide, and skill roadmaps."
                    ),
                    "profession_name": None,
                }
            return None

        reply = (
            f"### 💼 Nitro Career Guide: {detected}\n\n"
            f"**1. Core Workflow:** Define objectives, utilize standard validation pipelines, document progress, and iterate.\n"
            f"**2. Industry Tools:** Version control, domain-specific CAD/modeling/analytical platforms, and collaborative tracking.\n"
            f"**3. Key Skills:** Analytical problem solving, precision documentation, and clear stakeholder communication.\n\n"
            "Would you like an interview checklist, day-in-the-life schedule, or a tool stack recommendation?"
        )

        return {
            "reply": reply,
            "profession_name": detected,
        }