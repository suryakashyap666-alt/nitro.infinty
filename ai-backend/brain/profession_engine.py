from __future__ import annotations

import re
from typing import Callable, Dict, List, Optional, Tuple


def _normalize_text(text: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", " ", (text or "").lower()).strip()


PROFESSION_NAMES: List[str] = [
    "Accountant",
    "Actor",
    "Aerospace Engineer",
    "Agricultural Engineer",
    "Agronomist",
    "Air Traffic Controller",
    "Aircraft Mechanic",
    "Ambulance Driver",
    "Animator",
    "Anthropologist",
    "Archaeologist",
    "Architect",
    "Archivist",
    "Assembler",
    "Astronomer",
    "Attorney",
    "Auditor",
    "Automotive Mechanic",
    "Baker",
    "Bank Teller",
    "Barber",
    "Bartender",
    "Biochemist",
    "Biomedical Engineer",
    "Biologist",
    "Boat Captain",
    "Bookkeeper",
    "Botanist",
    "Broadcaster",
    "Budget Analyst",
    "Bus Driver",
    "Butcher",
    "Cabinetmaker",
    "Call Center Agent",
    "Camera Operator",
    "Cardiologist",
    "Carpenter",
    "Cartographer",
    "Cashier",
    "Catering Manager",
    "Chef",
    "Chemical Engineer",
    "Chemist",
    "CEO",
    "CFO",
    "CTO",
    "Childcare Worker",
    "Chiropractor",
    "Choreographer",
    "Civil Engineer",
    "Clinical Psychologist",
    "CNC Programmer",
    "Commercial Pilot",
    "Community Health Worker",
    "Composer",
    "Computer Programmer",
    "Conservationist",
    "Construction Manager",
    "Content Creator",
    "Copywriter",
    "Criminologist",
    "Cryptographer",
    "Curator",
    "Customer Service Representative",
    "Cybersecurity Analyst",
    "Data Analyst",
    "Data Scientist",
    "Database Administrator",
    "Dental Assistant",
    "Dentist",
    "Dermatologist",
    "Detective",
    "Dietitian",
    "Digital Marketer",
    "Diplomat",
    "Doctor",
    "Driver",
    "Ecologist",
    "Economist",
    "Editor",
    "Electrician",
    "EMT",
    "Energy Auditor",
    "Environmental Engineer",
    "Epidemiologist",
    "Esthetician",
    "Event Planner",
    "Exercise Physiologist",
    "Fabricator",
    "Facilities Manager",
    "Fashion Designer",
    "Financial Advisor",
    "Financial Analyst",
    "Firefighter",
    "Fisherman",
    "Fitness Instructor",
    "Flight Attendant",
    "Floral Designer",
    "Food Scientist",
    "Forensic Scientist",
    "Forester",
    "Fundraiser",
    "Furniture Finisher",
    "Game Designer",
    "Gastroenterologist",
    "Geographer",
    "Geologist",
    "Graphic Designer",
    "Guidance Counselor",
    "Gynecologist",
    "Hairdresser",
    "Handyman",
    "Health Educator",
    "Heavy Equipment Operator",
    "Historian",
    "Home Health Aide",
    "Horticulturist",
    "Hospital Administrator",
    "Hotel Manager",
    "HR Specialist",
    "HVAC Technician",
    "Hydrologist",
    "Illustrator",
    "Industrial Designer",
    "Industrial Engineer",
    "Information Security Analyst",
    "Insurance Agent",
    "Interior Designer",
    "Interpreter",
    "Investment Banker",
    "Journalist",
    "Judge",
    "Kindergarten Teacher",
    "Lab Technician",
    "Landscape Architect",
    "Lawyer",
    "Librarian",
    "Linguist",
    "Logistics Analyst",
    "Machinist",
    "Makeup Artist",
    "Management Consultant",
    "Marine Biologist",
    "Marine Engineer",
    "Marketing Manager",
    "Mason",
    "Massage Therapist",
    "Materials Scientist",
    "Mathematician",
    "Mechanical Engineer",
    "Medical Assistant",
    "Meteorologist",
    "Microbiologist",
    "Midwife",
    "Military Officer",
    "Mining Engineer",
    "Mixologist",
    "Model",
    "Music Director",
    "Musician",
    "Network Administrator",
    "Neurologist",
    "Neurosurgeon",
    "Nurse",
    "Nutritionist",
    "Oceanographer",
    "Office Administrator",
    "Oncologist",
    "Operations Manager",
    "Ophthalmologist",
    "Optometrist",
    "Oral Surgeon",
    "Orthodontist",
    "Orthopedic Surgeon",
    "Painter",
    "Paleontologist",
    "Paralegal",
    "Paramedic",
    "Park Ranger",
    "Pathologist",
    "Pediatrician",
    "Personal Trainer",
    "Petroleum Engineer",
    "Pharmacist",
    "Pharmacy Technician",
    "Photographer",
    "Physical Therapist",
    "Physician",
    "Physicist",
    "Pilot",
    "Pipefitter",
    "Plumber",
    "Podiatrist",
    "Poet",
    "Police Officer",
    "Political Scientist",
    "Power Plant Operator",
    "Preschool Teacher",
    "Principal",
    "Producer",
    "Product Designer",
    "Product Manager",
    "Professor",
    "Project Manager",
    "Proofreader",
    "Property Manager",
    "Prosthetist",
    "Psychiatrist",
    "Psychologist",
    "Public Relations Specialist",
    "Purchasing Agent",
    "QA Engineer",
    "Quantity Surveyor",
    "Radiation Therapist",
    "Radiologist",
    "Rancher",
    "Real Estate Agent",
    "Receptionist",
    "Recruiter",
    "Registered Nurse",
    "Regulatory Affairs Specialist",
    "Research Scientist",
    "Respiratory Therapist",
    "Retail Salesperson",
    "Risk Manager",
    "Roofer",
    "Safety Inspector",
    "Sales Manager",
    "School Counselor",
    "School Principal",
    "Screenwriter",
    "Sculptor",
    "Secretary",
    "Security Guard",
    "SEO Specialist",
    "Ship Captain",
    "Sign Language Interpreter",
    "Singer",
    "Social Media Manager",
    "Social Worker",
    "Sociologist",
    "Software Developer",
    "Software Engineer",
    "Soil Scientist",
    "Solar Energy Technician",
    "Sound Engineer",
    "Special Education Teacher",
    "Speech-Language Pathologist",
    "Sports Coach",
    "Statistician",
    "Stockbroker",
    "Strategic Planner",
    "Structural Engineer",
    "Substance Abuse Counselor",
    "Supply Chain Manager",
    "Surgeon",
    "Surveyor",
    "Systems Administrator",
    "Tailor",
    "Talent Acquisition Specialist",
    "Tax Accountant",
    "Tax Consultant",
    "Taxi Driver",
    "Teacher",
    "Technical Writer",
    "Telecommunications Specialist",
    "Textile Designer",
    "Tour Guide",
    "Toxicologist",
    "Translator",
    "Travel Agent",
    "Truck Driver",
    "Tutor",
    "UI/UX Designer",
    "Urban Planner",
    "Urologist",
    "Valuer",
    "Veterinarian",
    "Veterinary Technician",
    "Videographer",
    "Video Game Developer",
    "Vocational Teacher",
    "Waiter",
    "Warehouse Worker",
    "Watchmaker",
    "Water Treatment Plant Operator",
    "Web Designer",
    "Web Developer",
    "Welder",
    "Wildlife Biologist",
    "Wind Turbine Technician",
    "Woodworker",
    "Writer",
    "X-ray Technician",
    "Youth Worker",
    "Zoologist",
]

PROFESSION_MAP: Dict[str, str] = {_normalize_text(name): name for name in PROFESSION_NAMES}

CATEGORY_HINTS: Dict[str, Dict[str, str]] = {
    "engineering": {
        "workflow": "Define requirements, design systems, validate with tests, and iterate on deployment",
        "tools": "CAD, simulation, version control, technical documentation, and collaboration platforms",
        "skills": "structured problem solving, quality checks, safety, and communication with stakeholders",
        "career": "Build a strong portfolio, seek certifications, and keep current with industry standards",
    },
    "healthcare": {
        "workflow": "Assess, diagnose, document, communicate with the care team, and follow safety protocols",
        "tools": "Electronic health records, scheduling systems, clinical guidelines, and patient education resources",
        "skills": "clinical reasoning, empathy, time management, and accurate documentation",
        "career": "Gain experience with supervised practice, certifications, and patient-centered communication",
    },
    "business": {
        "workflow": "Collect requirements, analyze data, prepare recommendations, and present outcomes to decision makers",
        "tools": "Spreadsheets, reporting dashboards, project planning tools, and communication platforms",
        "skills": "analysis, stakeholder management, prioritization, and persuasive writing",
        "career": "Focus on impact, build cross-functional knowledge, and track measurable results",
    },
    "creative": {
        "workflow": "Research the brief, sketch ideas, create drafts, gather feedback, and refine the final product",
        "tools": "Design software, content management, collaboration boards, and portfolio platforms",
        "skills": "concept clarity, storytelling, attention to detail, and client communication",
        "career": "Showcase your work, network in communities, and keep refining your craft with real projects",
    },
    "education": {
        "workflow": "Plan learning objectives, prepare resources, deliver the lesson, assess understanding, and reflect",
        "tools": "Lesson planning software, assessment rubrics, communication platforms, and classroom management systems",
        "skills": "instructional design, feedback, empathy, and classroom organization",
        "career": "Build teaching experience, gather student feedback, and continue learning new methods",
    },
    "science": {
        "workflow": "Formulate hypotheses, design experiments, collect data, analyze results, and document findings",
        "tools": "Laboratory systems, data analysis tools, journals, and knowledge databases",
        "skills": "curiosity, attention to detail, critical thinking, and reproducible reporting",
        "career": "Focus on rigorous experiments, publish clear summaries, and collaborate with peers",
    },
    "trades": {
        "workflow": "Inspect the site, prepare tools, follow safety procedures, complete hands-on work, and verify quality",
        "tools": "Hand tools, safety gear, maintenance checklists, and scheduling software",
        "skills": "precision, practical troubleshooting, safety awareness, and client communication",
        "career": "Develop practical experience, maintain certifications, and build a reputation for reliability",
    },
    "technology": {
        "workflow": "Understand requirements, design solutions, build or configure systems, test carefully, and review performance",
        "tools": "Code editors, infrastructure platforms, monitoring systems, and teamwork software",
        "skills": "logical design, debugging, security awareness, and clear documentation",
        "career": "Contribute to real projects, stay curious about new tools, and focus on quality and delivery",
    },
    "service": {
        "workflow": "Listen to customer needs, respond clearly, resolve requests efficiently, and follow up when needed",
        "tools": "CRM systems, communication tools, scheduling software, and feedback channels",
        "skills": "active listening, empathy, time management, and problem solving",
        "career": "Build trust, learn from every interaction, and keep customer outcomes top of mind",
    },
}

LEVEL_TEMPLATES: Dict[str, str] = {
    "beginner": "If you are starting out, I’ll explain the essentials clearly, build step-by-step routines, and focus on what matters most first.",
    "intermediate": "At this stage, we can deepen your practical skills, improve efficiency, and connect your daily tasks to long-term goals.",
    "expert": "As an expert, I can help you refine advanced workflows, optimize productivity, mentor others, and support strategic decisions.",
}

REQUEST_TYPE_KEYWORDS: Dict[str, List[str]] = {
    "workflow": ["workflow", "process", "routine", "procedure", "steps", "sequence", "daily plan", "checklist"],
    "tools": ["tool", "software", "app", "platform", "system", "excel", "jira", "slack", "autocad", "figma", "photoshop", "powerpoint"],
    "career": ["career", "interview", "resume", "cv", "job", "promotion", "salary", "certification", "license", "prepare", "hire", "growth"],
    "learning": ["learn", "training", "practice", "improve", "study", "course", "resource", "tutorial", "skill", "mentor", "coaching"],
}

PROFESSION_CATEGORY_KEYWORDS: Dict[str, List[str]] = {
    "engineering": ["engineer", "technician", "mechanic", "aerospace", "chemical", "civil", "electrical", "mechanical", "industrial", "marine", "structural", "petroleum", "mining", "solar", "hvac"],
    "healthcare": ["doctor", "nurse", "therapist", "paramedic", "physician", "surgeon", "dentist", "cardiologist", "pharmacist", "midwife", "dietitian", "veterinarian", "chiropractor", "audiologist", "radiologist", "oncologist"],
    "business": ["accountant", "auditor", "analyst", "consultant", "finance", "bank", "cfo", "ceo", "cto", "manager", "advisor", "real estate", "purchasing", "logistics", "recruiter", "sales", "marketing", "public relations", "budget", "risk", "strategic"],
    "creative": ["designer", "artist", "writer", "composer", "musician", "photographer", "illustrator", "animator", "choreographer", "director", "producer", "screenwriter", "fashion", "graphic", "video", "content"],
    "education": ["teacher", "professor", "counselor", "tutor", "principal", "guidance", "special education", "vocational"],
    "science": ["scientist", "biologist", "chemist", "physicist", "geologist", "ecologist", "epidemiologist", "microbiologist", "researcher", "anthropologist", "archaeologist"],
    "trades": ["carpenter", "plumber", "electrician", "roofer", "welder", "mason", "handyman", "fabricator", "pipefitter", "cabinetmaker", "assembler", "mechanic", "technician", "operator", "truck driver", "bus driver", "taxi driver"],
    "technology": ["software", "developer", "programmer", "coder", "database", "network", "systems", "security", "cybersecurity", "it", "information", "web", "ui/ux", "qa"],
    "service": ["customer", "service", "hotel", "hospitality", "food", "chef", "bartender", "barber", "hairstylist", "nurse", "care", "driver", "salesperson", "retail", "tour", "flight attendant", "call center"],
}


class ProfessionEngine:
    """Profession intelligence engine for career guidance, workflows, tools, and skills."""

    def detect_profession(self, message: str) -> Optional[str]:
        normalized = _normalize_text(message)
        for phrase, canonical in PROFESSION_MAP.items():
            if phrase and re.search(rf"\b{re.escape(phrase)}\b", normalized):
                return canonical

        # fallback by keyword presence for common job titles and broad terms
        for phrase, canonical in PROFESSION_MAP.items():
            if phrase and phrase in normalized:
                return canonical

        return None

    def detect_level(self, message: str) -> Optional[str]:
        lower = (message or "").lower()
        if any(k in lower for k in ["beginner", "new to", "starting", "entry level", "student"]):
            return "beginner"
        if any(k in lower for k in ["intermediate", "mid level", "experienced", "seasoned", "working in"]):
            return "intermediate"
        if any(k in lower for k in ["expert", "advanced", "senior", "master", "lead"]):
            return "expert"
        return None

    def detect_request_type(self, message: str) -> str:
        text = (message or "").lower()
        for request_type, keywords in REQUEST_TYPE_KEYWORDS.items():
            if any(k in text for k in keywords):
                return request_type
        return "general"

    def profession_category(self, profession: Optional[str]) -> str:
        if not profession:
            return "general"
        normalized = _normalize_text(profession)
        for category, keywords in PROFESSION_CATEGORY_KEYWORDS.items():
            if any(k in normalized for k in keywords):
                return category
        return "general"

    def _category_hint(self, profession: str) -> Dict[str, str]:
        category = self.profession_category(profession)
        return CATEGORY_HINTS.get(category, {
            "workflow": "Understand typical tasks, use reliable tools, and follow standards for your role.",
            "tools": "Common tools include job-specific software, collaboration platforms, and workflow checklists.",
            "skills": "Focus on strong fundamentals, efficient communication, and consistent process execution.",
            "career": "Build experience, track progress, and ask for feedback to grow your career.",
        })

    def is_profession_query(self, message: str) -> bool:
        normalized = _normalize_text(message)
        if self.detect_profession(message):
            return True
        if any(k in normalized for k in ["profession", "career", "workflow", "tool", "tools", "software", "interview", "resume", "certification"]):
            return True
        return False

    def _summary(self, profession: str, level: str, request_type: str, user_state: Dict[str, Any]) -> str:
        hint = self._category_hint(profession)
        base = [
            f"Profession: {profession}",
            f"Level: {level.title()}",
            f"Core workflow: {hint['workflow']}.",
            f"Useful tools: {hint['tools']}.",
            f"Productivity tip: organize your day around the highest-impact tasks, keep notes, and review outcomes regularly.",
        ]
        if request_type == "workflow":
            return (
                f"As a {profession}, your main workflow often includes: {hint['workflow']}. "
                "I can help you create step-by-step procedures, checklists, and realistic daily plans for your role. "
                f"{LEVEL_TEMPLATES.get(level, LEVEL_TEMPLATES['beginner'])}"
            )
        if request_type == "tools":
            return (
                f"For {profession}, key tools and software include: {hint['tools']}. "
                "I can explain how to use them, compare alternatives, and help you choose the right stack for your daily tasks. "
                f"{LEVEL_TEMPLATES.get(level, LEVEL_TEMPLATES['beginner'])}"
            )
        if request_type == "career":
            return (
                f"Career growth for {profession} is best supported by practical experience, strong communication, and demonstrable results. "
                f"{hint['career']}. "
                "Ask me for interview prep, certification planning, or resume examples tailored to your role."
            )
        if request_type == "learning":
            return (
                f"To build your {profession} skills, focus on real tasks, on-the-job practice, and trusted resources. "
                f"{hint['skills']}. "
                "I can suggest learning resources, training plans, and goal-based routines for your current skill level."
            )
        return (
            f"As a {profession}, I can help with profession-specific workflows, tools, career preparation, and learning paths. "
            f"{hint['workflow']}. {hint['tools']}. {LEVEL_TEMPLATES.get(level, LEVEL_TEMPLATES['beginner'])} "
            "Tell me if you want a workflow checklist, interview preparation, or a profession-specific template."
        )

    def handle_profession_message(self, message: str, user_state: Dict[str, Any], progress_callback: Callable[[int], None] | None = None) -> Optional[Dict[str, Any]]:
        if not self.is_profession_query(message):
            return None

        profession = user_state.get("profession", {}).get("name")
        detected = self.detect_profession(message)
        if detected:
            profession = detected

        level = self.detect_level(message) or user_state.get("profession", {}).get("level") or "beginner"
        request_type = self.detect_request_type(message)
        def _progress(value: int) -> None:
            if progress_callback is None:
                return
            try:
                progress_callback(max(0, min(100, int(value))))
            except Exception:
                pass

        _progress(20)

        if not profession:
            if request_type in {"workflow", "tools", "career", "learning"}:
                return {
                    "reply": (
                        "I can help with profession workflows, tools, learning plans, and career growth. "
                        "Please tell me which profession or industry you want help with."
                    ),
                    "profession_name": None,
                    "profession_level": level,
                    "request_type": request_type,
                }
            return None

        reply = self._summary(profession, level, request_type, user_state)
        _progress(100)
        return {
            "reply": reply,
            "profession_name": profession,
            "profession_level": level,
            "request_type": request_type,
        }

    def extract_interests(self, message: str) -> List[str]:
        lower = (message or "").lower()
        interests: List[str] = []
        if "interest" in lower or "like" in lower or "love" in lower or "want" in lower:
            profession = self.detect_profession(message)
            if profession:
                interests.append(profession)
        return interests

    def extract_tools(self, message: str) -> List[str]:
        lower = (message or "").lower()
        tools: List[str] = []
        for keyword in ["excel", "autocad", "figma", "jira", "slack", "python", "git", "azure", "aws", "google", "office", "zoom"]:
            if keyword in lower:
                tools.append(keyword)
        return tools
