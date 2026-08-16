from __future__ import annotations

"""Universal Education & Subject Intelligence System for Nitro Infinity AI.

COMPREHENSIVE TAXONOMY COVERING ALL EDUCATION LEVELS:
- Pre-Primary (ages 3-5)
- Primary School (grades 1-5)
- Middle School (grades 6-8)
- High School (grades 9-10)
- Senior Secondary (grades 11-12)
- University / Higher Education
- Research Level

ARCHITECTURE:
- 9 stable subject clusters (IDs never change - for persistence)
- Each cluster enriched with: keywords, aliases, subtopics for the FULL RANGE of education
- detect_subject_id() maps ANY educational subject name to one of these 9
- This provides universal coverage with minimal duplication

KEY FEATURES:
- Adaptive learning per subject_id (weak/strong tracking, learning speed, style)
- Multilingual education support
- Step-by-step teaching, practice questions, quizzes, worksheets, study plans
- Visual explanations and emotional teaching support
- Supports weak and advanced students
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class Subject:
    id: str
    name: str
    level: str  # pre_primary|primary|middle|high|senior_secondary|university|research
    aliases: Tuple[str, ...]
    keywords: Tuple[str, ...]
    subtopics: Tuple[str, ...]


LEVELS = {
    "pre_primary": "Pre-Primary (Ages 3-5)",
    "primary": "Primary School (Grades 1-5)",
    "middle": "Middle School (Grades 6-8)",
    "high": "High School (Grades 9-10)",
    "senior_secondary": "Senior Secondary (Grades 11-12)",
    "university": "University / Higher Education",
    "research": "Research Level",
}


# 9-subject taxonomy (stable IDs - DO NOT RENAME)
SUBJECTS: Dict[str, Subject] = {
    # ==================== PRE-PRIMARY CLUSTER ====================
    # Covers: Phonics, Reading, Writing, Storytelling, Recitation, Native Language Literacy
    "phonics": Subject(
        id="phonics",
        name="Phonics, Reading & Literacy (Pre-Primary through Advanced)",
        level="pre_primary",
        aliases=(
            # Pre-Primary
            "phonics", "phoneme", "letter sounds", "letter sound", "native language",
            "native language literacy", "literacy", "recitation", "storytelling",
            "reading", "reading skills", "writing", "writing skills", "phonics sounds",
            "rhymes", "story recitation", "recite", "recitation skills",
            # Primary through Senior Secondary
            "english language", "english grammar", "english composition", "english literature",
            "hindi", "regional language", "foreign languages", "vocabulary",
            "spelling", "reading comprehension", "creative writing", "essays",
            "story writing", "grammar", "composition writing", "sentence structure",
            "pronouns", "verbs", "nouns", "adjectives", "prepositions",
            "classical languages", "sanskrit", "language literacy", "poetry",
            "prose", "drama", "dramatic play", "language arts", "communication skills",
            # University & Research
            "linguistics", "language analysis", "phonology", "syntax", "semantics",
            "discourse analysis", "applied linguistics",
        ),
        keywords=(
            "phonics", "phoneme", "letters", "letter sound", "blending", "segment",
            "recite", "reading", "story", "rhymes", "writing", "vowels", "consonants",
            "sight words", "word reading", "early literacy", "grammar", "composition",
            "vocabulary", "spelling", "literature", "prose", "poetry", "drama",
            "communication", "expression", "language", "hindi", "sanskrit", "regional",
            "linguistics", "syntax", "semantics",
        ),
        subtopics=(
            "vowels & consonants", "blending & segmentation", "sight words",
            "recitation skills", "storytelling", "native language literacy",
            "english grammar", "english composition", "vocabulary building",
            "reading comprehension", "creative writing", "essay writing",
            "poetry & prose", "drama & performance", "language arts",
            "hindi language", "regional languages", "foreign languages",
            "classical languages", "linguistics", "language analysis",
        ),
    ),

    # ==================== PRE-PRIMARY CLUSTER ====================
    # Covers: Numbers, Counting, Comparisons, Pattern Matching, Shapes, Colors
    "number_sense": Subject(
        id="number_sense",
        name="Numbers, Arithmetic & Foundational Math (Pre-Primary through Advanced)",
        level="pre_primary",
        aliases=(
            # Pre-Primary
            "numbers", "number recognition", "counting", "count", "counting numbers",
            "comparison", "more than", "less than", "bigger", "smaller", "equal",
            "pattern matching", "pattern", "shapes", "colors", "colour", "sorting",
            # Primary
            "arithmetic", "addition", "subtraction", "multiplication", "division",
            "fractions", "word problems", "basic mathematics", "basic arithmetic",
            "number sense", "place value", "skip counting", "even odd",
            # Middle School
            "pre-algebra", "algebra", "geometry", "ratios", "proportions",
            "data handling", "statistics", "integers", "linear equations",
            # High School & Senior Secondary
            "algebra", "calculus", "core mathematics", "applied mathematics",
            "trigonometry", "coordinate geometry", "sequences", "series",
            "quadratic equations", "exponential", "logarithms", "matrices",
            "permutations", "combinations", "probability", "vectors",
            # University & Research
            "advanced calculus", "real analysis", "complex analysis", "abstract algebra",
            "number theory", "group theory", "field theory", "topology",
        ),
        keywords=(
            "count", "numbers", "number recognition", "arithmetic", "addition",
            "subtraction", "multiplication", "division", "fractions", "patterns",
            "before", "after", "between", "more", "less", "bigger", "smaller",
            "equal", "algebra", "geometry", "ratios", "proportions", "statistics",
            "data", "probability", "calculus", "equations", "matrices",
        ),
        subtopics=(
            "counting & number recognition", "comparison & ordering",
            "pattern matching & sequences", "basic arithmetic operations",
            "fractions & decimals", "word problems", "pre-algebra",
            "algebra fundamentals", "geometry basics", "data handling",
            "statistics & probability", "trigonometry", "calculus basics",
            "advanced algebra", "coordinate geometry", "linear algebra",
        ),
    ),

    # ==================== PRE-PRIMARY CLUSTER ====================
    # Covers: Shapes, Colors, Drawing, Coloring, Crafts, Good Habits, Awareness
    "shapes_colors": Subject(
        id="shapes_colors",
        name="Shapes, Colors, Arts & Environmental Awareness (Pre-Primary through Secondary)",
        level="pre_primary",
        aliases=(
            # Pre-Primary
            "shapes", "colors", "colour", "sorting", "drawing", "coloring",
            "craft", "paper folding", "clay modeling", "paper craft",
            "art", "painting", "collage", "texture", "spatial awareness",
            # Environmental & General Awareness
            "environment", "environmental studies", "environmental awareness",
            "general awareness", "general knowledge", "world around us",
            "nature", "plants", "animals", "insects", "seasons",
            "weather", "water", "soil", "natural resources",
            # Primary & Beyond
            "fine arts", "visual arts", "drawing", "painting", "sculpture",
            "design", "interior design", "fashion design", "architecture",
            "art appreciation", "art history", "cultural studies",
            # Secondary & Higher
            "performing arts", "music", "dance", "theater", "drama",
            "animation", "graphic design", "digital art",
        ),
        keywords=(
            "shape", "circle", "square", "triangle", "color", "colour", "sorting",
            "awareness", "environment", "drawing", "coloring", "craft", "art",
            "painting", "design", "nature", "plants", "animals", "music", "dance",
            "theater", "drama", "performance", "creative", "visual",
        ),
        subtopics=(
            "basic shapes & colors", "sorting & classification", "spatial awareness",
            "drawing & painting", "craft activities", "paper folding", "clay modeling",
            "environmental studies", "good habits & character", "digital safety basics",
            "general awareness & knowledge", "nature & environment",
            "fine arts", "performing arts", "music & dance", "theater & drama",
            "design & aesthetics", "cultural studies",
        ),
    ),

    # ==================== PRIMARY CLUSTER ====================
    # Covers: Languages, Moral Science, Digital Safety, Keyboard, Social Skills
    "english": Subject(
        id="english",
        name="Languages, Communication & Moral Science (Primary through University)",
        level="primary",
        aliases=(
            # Primary
            "english", "english language", "english grammar", "english literature",
            "composition", "vocabulary", "spelling", "moral science", "moral",
            "hindi", "regional language", "language", "foreign language",
            "keyboard", "keyboard typing", "typing skills", "digital literacy",
            "digital safety", "cyber safety", "online safety", "e-safety",
            # Secondary & Beyond
            "language arts", "communication skills", "public speaking", "presentation",
            "debate", "discussion", "negotiation", "interpersonal skills",
            "professional communication", "business communication", "technical writing",
            "journalism", "content writing", "copywriting", "digital communication",
            "media literacy", "information literacy", "research skills",
        ),
        keywords=(
            "english", "grammar", "composition", "literature", "vocabulary", "spelling",
            "reading", "writing", "hindi", "sanskrit", "regional", "language",
            "moral", "ethics", "civics", "communication", "expression", "typing",
            "keyboard", "digital", "safety", "speaking", "presentation", "debate",
        ),
        subtopics=(
            "english grammar basics", "vocabulary & spelling", "composition & writing",
            "literature & reading", "moral science & ethics", "hindi language",
            "regional languages", "foreign languages", "language literacy",
            "keyboard & typing skills", "digital safety & citizenship",
            "communication skills", "public speaking", "presentation skills",
            "debate & discussion", "professional communication",
        ),
    ),

    # ==================== PRIMARY/MIDDLE CLUSTER ====================
    # Covers: Science, Health, Environmental Studies, General Knowledge
    "science": Subject(
        id="science",
        name="Science, Health & Environmental Studies (Primary through Research)",
        level="middle",
        aliases=(
            # Primary & Middle
            "science", "general science", "environmental studies", "environmental science",
            "environment", "nature", "natural science",
            # Physics
            "physics", "motion", "forces", "energy", "light", "sound", "electricity",
            "magnetism", "waves", "mechanics", "thermodynamics", "optics",
            # Chemistry
            "chemistry", "atoms", "molecules", "elements", "compounds", "reactions",
            "periodic table", "acids", "bases", "salts", "organic chemistry",
            "biochemistry", "physical chemistry", "analytical chemistry",
            # Biology
            "biology", "cells", "organisms", "plants", "animals", "ecosystems",
            "anatomy", "physiology", "genetics", "evolution", "microbiology",
            "botany", "zoology", "ecology", "marine biology", "human biology",
            # Earth Science
            "earth science", "geology", "earth", "rocks", "minerals", "earthquakes",
            "volcanoes", "atmosphere", "weather", "climate", "oceans",
            "geography", "physical geography", "geomorphology",
            # Astronomy
            "astronomy", "astrology", "stars", "planets", "space", "solar system",
            "universe", "astrophysics", "cosmology", "celestial",
            # Health
            "health", "health education", "hygiene", "nutrition", "fitness",
            "physical education", "exercise", "wellness", "sports", "athletics",
            "medicine", "medical science", "public health", "health sciences",
            "dentistry", "nursing", "pharmacology", "veterinary science",
            # IT Basics
            "IT", "information technology", "computer", "computing", "digital technology",
        ),
        keywords=(
            "science", "physics", "chemistry", "biology", "earth", "geology",
            "astronomy", "environmental", "energy", "motion", "force", "atoms",
            "cells", "ecosystem", "biotechnology", "astrophysics", "public health",
            "health", "fitness", "sports", "medicine", "technology", "digital",
        ),
        subtopics=(
            "motion & forces", "energy & work", "light & sound", "electricity",
            "atoms & molecules", "elements & compounds", "chemical reactions",
            "basic biology", "human body", "plants & animals", "ecosystems",
            "earth & geology", "astronomy & space", "weather & climate",
            "health & hygiene", "nutrition & fitness", "sports & physical education",
            "environmental studies", "public health", "medical sciences",
            "biotechnology & genetics", "information technology basics",
        ),
    ),

    # ==================== MIDDLE/SECONDARY CLUSTER ====================
    # Covers: Social Studies, History, Civics, Geography, Humanities
    "social_science": Subject(
        id="social_science",
        name="Social Studies, History & Humanities (Middle through Research)",
        level="middle",
        aliases=(
            # Social Studies & Civics
            "social studies", "civics", "civics studies", "government", "governance",
            "citizenship", "community", "society", "social structure",
            # History
            "history", "world history", "ancient civilizations", "medieval history",
            "modern history", "ancient history", "indian history", "european history",
            "world wars", "cold war", "historical events", "historians",
            # Geography
            "geography", "physical geography", "human geography", "map reading",
            "countries", "cities", "capitals", "regions", "continents",
            "climate zones", "biodiversity", "natural resources",
            # Government & Politics
            "political science", "politics", "government", "democracy", "dictatorship",
            "monarchy", "constitution", "legislation", "parliament",
            "local governance", "administration", "public policy",
            # Economics
            "economics", "economic systems", "trade", "commerce", "business",
            "finance", "banking", "money", "inflation", "unemployment",
            "business studies", "entrepreneurship", "marketing", "management",
            # Humanities & Social Sciences
            "sociology", "social behavior", "culture", "tradition", "customs",
            "psychology", "human behavior", "emotions", "personality", "mental health",
            "philosophy", "ethics", "values", "logic", "reasoning",
            "anthropology", "cultural studies", "linguistics",
            # International
            "international relations", "global affairs", "geopolitics",
            "diplomacy", "treaties", "international law",
            # Legal Studies
            "legal studies", "law", "justice", "rights", "duties",
            "human rights", "constitutional law", "criminal law", "civil law",
        ),
        keywords=(
            "civics", "history", "geography", "government", "community",
            "civilizations", "ancient", "medieval", "political", "economics",
            "sociology", "psychology", "philosophy", "legal", "international",
            "culture", "society", "administration", "business", "trade",
        ),
        subtopics=(
            "ancient & medieval history", "modern & contemporary history",
            "local & world geography", "government & civics",
            "political systems", "economics & trade", "sociology",
            "psychology & human behavior", "philosophy & ethics",
            "cultural studies", "international relations", "legal studies",
            "human geography", "historical events", "democratic processes",
        ),
    ),

    # ==================== HIGH SCHOOL/UNIVERSITY CLUSTER ====================
    # Covers: Computer Science, IT, Programming, AI, Data Science, Engineering
    "computer_science": Subject(
        id="computer_science",
        name="Computer Science, AI & Programming (High School through Research)",
        level="high",
        aliases=(
            # Basic IT & Computers
            "computer science", "cs", "informatics", "information technology", "IT",
            "computing", "computer", "digital technology", "technology",
            # Programming Languages
            "programming", "coding", "code", "python", "java", "javascript",
            "c++", "c#", "php", "ruby", "go", "rust", "swift", "kotlin",
            "sql", "shell", "bash", "assembly", "bytecode",
            # Web & Frontend
            "web development", "web design", "frontend", "html", "css",
            "javascript", "react", "angular", "vue", "bootstrap", "responsive design",
            "user interface", "UX", "user experience", "web apps",
            # Backend & Databases
            "backend", "server", "databases", "sql", "nosql", "data persistence",
            "apis", "rest", "graphql", "backend systems", "scalability",
            # Data Science & AI
            "ai", "artificial intelligence", "machine learning", "deep learning",
            "neural networks", "nlp", "natural language processing", "computer vision",
            "data science", "big data", "analytics", "statistical learning",
            "reinforcement learning", "supervised learning", "unsupervised learning",
            # Algorithms & Theory
            "data structures", "algorithms", "algorithm design", "complexity",
            "graph theory", "sorting", "searching", "dynamic programming",
            "greedy algorithms", "divide and conquer", "big o notation",
            # Software Engineering
            "software engineering", "software development", "agile", "scrum",
            "design patterns", "architecture", "testing", "debugging",
            "version control", "git", "devops", "continuous integration",
            # Cybersecurity
            "cybersecurity", "security", "encryption", "hacking", "penetration testing",
            "network security", "information security", "privacy",
            # Block Coding & Visual Programming
            "block coding", "visual programming", "scratch", "blockly",
            "game development", "game engines", "unity", "unreal",
            # Office & Spreadsheets
            "spreadsheet", "excel", "google sheets", "data analysis",
            "presentation design", "powerpoint", "office tools",
            # Typing & Digital Literacy
            "keyboard typing", "typing", "digital literacy", "e-literacy",
            "computer basics", "operating systems", "file management",
        ),
        keywords=(
            "computer", "programming", "python", "java", "data structures",
            "algorithms", "coding", "ai", "machine learning", "block coding",
            "html", "css", "javascript", "spreadsheet", "presentation",
            "keyboard", "typing", "information technology", "software",
            "web", "database", "network", "security", "development",
        ),
        subtopics=(
            "programming fundamentals", "python programming", "java fundamentals",
            "web development basics", "html & css", "javascript & frontend",
            "database design", "sql basics", "backend systems",
            "data structures", "algorithms", "algorithm analysis",
            "artificial intelligence", "machine learning basics",
            "deep learning", "neural networks", "natural language processing",
            "computer vision", "big data & analytics",
            "software engineering", "design patterns", "agile methodology",
            "cybersecurity", "network security", "encryption",
            "game development", "block coding", "game engines",
            "digital citizenship", "typing & digital literacy",
        ),
    ),

    # ==================== ARTS & PERFORMING ARTS CLUSTER ====================
    # Covers: Music, Drama, Dance, Singing, Instrumental, Vocal, Performing Arts
    "arts": Subject(
        id="arts",
        name="Music, Performing Arts & Creative Expression (Pre-Primary through University)",
        level="primary",
        aliases=(
            # Music Basics
            "music", "singing", "song", "musical", "melody", "rhythm",
            "music theory", "musical notes", "beats", "tempo", "scale",
            # Instrumental Music
            "instrumental music", "instruments", "piano", "guitar", "violin",
            "flute", "drums", "percussion", "strings", "brass",
            "wind instruments", "keyboard instruments", "musical instrument",
            # Vocal Music
            "vocal music", "voice", "singing", "chorus", "choir", "vocal training",
            "vocal performance", "voice control", "breath support",
            # Performing Arts
            "performing arts", "theater", "theatre", "drama", "dramatic play",
            "stage performance", "acting", "acting skills", "performance",
            "speech", "recitation", "monologue", "dialogue",
            # Dance
            "dance", "dancing", "choreography", "movement", "rhythm",
            "cultural dance", "classical dance", "contemporary dance",
            "dance performance", "dance training",
            # Arts & Crafts
            "art", "arts", "craft", "painting", "drawing", "sculpture",
            "visual arts", "art history", "art appreciation", "art techniques",
            "fine arts", "creative arts", "artistic expression",
            # Design & Aesthetics
            "design", "graphic design", "interior design", "fashion design",
            "fashion", "aesthetics", "composition", "color theory",
            "visual design", "user experience design",
            # Animation & Digital Arts
            "animation", "digital art", "graphic animation", "motion graphics",
            "3d modeling", "visual effects", "animation software",
        ),
        keywords=(
            "music", "singing", "instrument", "piano", "guitar", "violin",
            "rhythm", "melody", "beat", "performance", "theater", "drama",
            "dance", "art", "painting", "drawing", "design", "creative",
            "vocal", "instrumental", "choreography", "animation", "visual",
        ),
        subtopics=(
            "music fundamentals", "music theory", "rhythm & beat",
            "melody & harmony", "musical notes & scales",
            "instrumental music training", "vocal music training",
            "piano basics", "guitar basics", "violin basics",
            "wind instruments", "percussion instruments",
            "drama & theater", "acting & performance", "stage production",
            "dance basics", "choreography", "movement & rhythm",
            "drawing & painting", "sculpture & 3d arts", "art history",
            "graphic design", "interior design", "fashion design",
            "animation & motion graphics", "digital arts",
        ),
    ),

    # ==================== COMMERCE & PROFESSIONAL STUDIES CLUSTER ====================
    # Covers: Accounting, Finance, Business Management, Professional Skills
    "commerce": Subject(
        id="commerce",
        name="Commerce, Business & Professional Studies (High School through University)",
        level="high",
        aliases=(
            # Accounting
            "accountancy", "accounting", "accounts", "bookkeeping",
            "financial accounting", "management accounting", "cost accounting",
            "auditing", "taxation", "tax planning", "financial statements",
            # Business Studies
            "business studies", "business", "commerce", "business management",
            "entrepreneurship", "entrepreneurship skills", "business planning",
            "venture capital", "startup", "business model",
            # Finance
            "finance", "financial planning", "personal finance", "corporate finance",
            "investment", "banking", "stock market", "shares", "bonds",
            "mutual funds", "financial markets", "insurance", "portfolio management",
            # Marketing
            "marketing", "market research", "advertising", "brand management",
            "customer service", "sales", "digital marketing", "social media marketing",
            "content marketing", "e-commerce", "customer relationship",
            # Management & Administration
            "management", "business management", "operations management",
            "human resources", "hr", "team management", "project management",
            "organizational behavior", "leadership", "decision making",
            "administration", "public administration",
            # Economics
            "economics", "microeconomics", "macroeconomics", "political economy",
            "behavioral economics", "development economics", "business economics",
            # Office Skills
            "office skills", "office management", "secretarial skills",
            "administrative assistant", "communication skills", "time management",
        ),
        keywords=(
            "accounting", "finance", "business", "commerce", "entrepreneurship",
            "marketing", "management", "investment", "banking", "management",
            "economics", "professional", "administration", "office", "sales",
        ),
        subtopics=(
            "accounting fundamentals", "financial accounting", "taxation",
            "business management", "entrepreneurship", "business planning",
            "financial planning", "investment basics", "stock market",
            "marketing fundamentals", "market research", "advertising",
            "management skills", "human resources", "operations management",
            "economics basics", "microeconomics", "macroeconomics",
            "office management", "professional communication",
        ),
    ),

    # ==================== SPORTS, HEALTH & WELLNESS CLUSTER ====================
    # Covers: Physical Education, Sports, Gymnastics, Team Sports, Health
    "sports_health": Subject(
        id="sports_health",
        name="Physical Education, Sports & Wellness (Pre-Primary through University)",
        level="primary",
        aliases=(
            # Physical Education
            "physical education", "pe", "sports", "athletics", "exercise",
            "fitness", "workout", "training", "conditioning",
            # Team Sports
            "team sports", "basketball", "football", "soccer", "cricket",
            "volleyball", "badminton", "tennis", "hockey", "rugby",
            "american football", "baseball", "softball", "lacrosse",
            # Individual Sports
            "individual sports", "swimming", "gymnastics", "wrestling",
            "track and field", "athletics", "martial arts", "boxing",
            "table tennis", "squash", "racquetball", "skateboarding",
            # Games & Recreation
            "games", "outdoor games", "recreational sports", "adventure sports",
            "extreme sports", "water sports", "winter sports", "parkour",
            # Gymnastics & Movement
            "gymnastics", "rhythmic gymnastics", "artistic gymnastics",
            "acrobatics", "balance", "flexibility", "stretching",
            # Health & Wellness
            "health", "health education", "wellness", "nutrition", "diet",
            "mental health", "stress management", "relaxation", "yoga",
            "meditation", "mindfulness", "sleep health", "hygiene",
            # Sports Science
            "sports medicine", "sports science", "biomechanics", "physiology",
            "performance training", "coaching", "sports psychology",
            "athletic performance", "sports nutrition",
        ),
        keywords=(
            "physical education", "sports", "fitness", "exercise", "athletic",
            "team sports", "basketball", "soccer", "football", "cricket",
            "health", "wellness", "nutrition", "gymnastics", "swimming",
            "training", "coaching", "performance", "meditation", "yoga",
        ),
        subtopics=(
            "physical fitness basics", "exercise fundamentals",
            "team sports skills", "individual sports training",
            "gymnastics & flexibility", "swimming & water sports",
            "martial arts basics", "yoga & relaxation",
            "nutrition & diet", "health habits", "mental wellness",
            "sports psychology", "performance training",
            "outdoor recreation", "sports safety",
        ),
    ),
}


def list_subjects() -> List[Dict[str, str]]:
    """Return all available subjects with metadata."""
    return [{"id": s.id, "name": s.name, "level": s.level} for s in SUBJECTS.values()]


def list_levels() -> Dict[str, str]:
    """Return all available education levels."""
    return LEVELS.copy()


def normalize(s: str) -> str:
    """Normalize string for matching."""
    return (s or "").strip().lower()


def subject_match_candidates(message: str, limit: int = 6) -> List[Tuple[str, int]]:
    """Find subject candidates that match the message.
    
    Args:
        message: User input message
        limit: Maximum number of candidates to return
        
    Returns:
        List of (subject_id, score) tuples sorted by score descending
    """
    msg = normalize(message)
    if not msg:
        return []

    scores: Dict[str, int] = {}
    for sid, subj in SUBJECTS.items():
        score = 0
        # Keyword matches get higher weight
        for kw in subj.keywords:
            if kw and kw in msg:
                score += 3
        # Alias matches get medium weight
        for al in subj.aliases:
            if al and al in msg:
                score += 2
        # Subtopic matches get lower weight
        for st in subj.subtopics:
            if st and st in msg:
                score += 1
        if score:
            scores[sid] = score

    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    return ranked[:limit]


def detect_subject_id(message: str, fallback: str = "mathematics") -> str:
    """Detect which subject the message refers to.
    
    Uses priority overrides for ambiguous cases, then falls back to
    keyword/alias matching to map user input to one of the 9 stable
    subject clusters.
    
    Args:
        message: User input message
        fallback: Subject ID to use if no match found
        
    Returns:
        One of the 9 stable subject IDs
    """
    msg = normalize(message)

    # Priority overrides to handle ambiguous/high-risk terms
    priority_map = {
        # Commerce/Vocational → commerce/mathematics
        "accountancy": "commerce",
        "accounting": "commerce",
        "business studies": "commerce",
        "business management": "commerce",
        "commerce": "commerce",
        "finance": "commerce",
        "banking": "commerce",
        "stock market": "commerce",
        "investment": "commerce",
        "entrepreneurship": "commerce",
        "marketing": "commerce",

        # Health/Medicine → science
        "medicine": "science",
        "dentistry": "science",
        "nursing": "science",
        "pharmacology": "science",
        "public health": "science",
        "veterinary": "science",
        "health": "science",

        # Law/Legal → social_science
        "law": "social_science",
        "legal studies": "social_science",
        "criminal law": "social_science",
        "constitution": "social_science",

        # Philosophy/Humanities → social_science
        "philosophy": "social_science",
        "ethics": "social_science",
        "psychology": "social_science",
        "sociology": "social_science",
        "anthropology": "social_science",
        "linguistics": "social_science",

        # Music/Drama/Arts → arts
        "music": "arts",
        "singing": "arts",
        "vocal": "arts",
        "instrumental": "arts",
        "drama": "arts",
        "theater": "arts",
        "theatre": "arts",
        "dance": "arts",
        "painting": "arts",
        "drawing": "arts",
        "sculpture": "arts",
        "animation": "arts",

        # Sports/PE → sports_health
        "sports": "sports_health",
        "physical education": "sports_health",
        "fitness": "sports_health",
        "athletics": "sports_health",
        "gymnastics": "sports_health",
        "swimming": "sports_health",
        "yoga": "sports_health",

        # Programming/CS terms → computer_science
        "programming": "computer_science",
        "coding": "computer_science",
        "python": "computer_science",
        "java": "computer_science",
        "javascript": "computer_science",
        "ai": "computer_science",
        "machine learning": "computer_science",
        "data science": "computer_science",
    }

    # Check priority overrides
    for key, subject in priority_map.items():
        if key in msg:
            return subject

    # Fall back to keyword/alias matching
    ranked = subject_match_candidates(message, limit=3)
    if not ranked:
        return fallback
    return ranked[0][0]


