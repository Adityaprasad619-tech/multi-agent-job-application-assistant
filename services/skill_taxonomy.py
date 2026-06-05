"""
Skill Taxonomy & Normalization Layer
======================================
Centralized, deterministic skill-to-synonym mapping for the ATS engine.

Design Decisions:
- Bidirectional: maps high-level skill categories to concrete technologies,
  AND individual technologies back to the categories they satisfy.
- Fully deterministic: no LLM, no embeddings, no fuzzy matching.
- Extensible: add new mappings by editing SKILL_TAXONOMY below.
- Separated from ATS logic for maintainability and testability.

Matching Strategy:
- DIRECT match: "Python" in resume matches "Python" in job requirements.
- SYNONYM match: "Pandas" in resume matches "Statistical Analysis" requirement
  because SKILL_TAXONOMY maps "statistical analysis" → ["pandas", ...].
- REVERSE match: "Python" in resume matches "Programming" requirement
  because SKILL_TAXONOMY maps "programming" → ["python", ...].
"""

from __future__ import annotations


# ==================================================================
# CANONICAL SKILL TAXONOMY
# ==================================================================
# Keys are normalized skill categories (lowercase).
# Values are lists of concrete technologies, synonyms, and related terms
# that satisfy the category.
#
# The mapping is intentionally broad to cover common federal job postings
# and technology industry requirements.
# ==================================================================

SKILL_TAXONOMY: dict[str, list[str]] = {
    # --- Data & Analytics ---
    "statistical analysis": [
        "pandas", "numpy", "scipy", "statistics", "data analytics",
        "data analysis", "statistical modeling", "hypothesis testing",
        "regression analysis", "descriptive statistics", "inferential statistics",
        "r programming", "stata", "spss", "sas", "biostatistics",
    ],
    "data analysis": [
        "pandas", "numpy", "data analytics", "excel", "tableau",
        "power bi", "data visualization", "reporting", "dashboards",
        "data mining", "etl", "data wrangling", "data cleaning",
        "statistical analysis", "statistics", "scipy",
    ],
    "data science": [
        "pandas", "numpy", "scipy", "scikit-learn", "tensorflow",
        "pytorch", "machine learning", "data analysis", "data analytics",
        "statistics", "jupyter", "data visualization", "feature engineering",
        "model training", "ml", "deep learning",
    ],
    "data engineering": [
        "etl", "data pipelines", "apache spark", "kafka", "airflow",
        "sql", "python", "data warehousing", "data modeling",
        "snowflake", "redshift", "bigquery", "dbt",
    ],
    "data visualization": [
        "tableau", "power bi", "matplotlib", "seaborn", "plotly",
        "d3.js", "grafana", "dashboards", "charts", "reporting",
    ],

    # --- Machine Learning & AI ---
    "machine learning": [
        "scikit-learn", "tensorflow", "pytorch", "keras", "ml",
        "classification", "prediction", "regression", "clustering",
        "neural networks", "deep learning", "model training",
        "feature engineering", "xgboost", "random forest",
        "natural language processing", "nlp", "computer vision",
        "reinforcement learning", "supervised learning", "unsupervised learning",
    ],
    "deep learning": [
        "tensorflow", "pytorch", "keras", "neural networks",
        "cnn", "rnn", "lstm", "transformer", "gpt",
        "computer vision", "nlp", "machine learning",
    ],
    "artificial intelligence": [
        "machine learning", "deep learning", "nlp",
        "natural language processing", "computer vision",
        "tensorflow", "pytorch", "scikit-learn", "ai",
        "neural networks", "reinforcement learning",
    ],
    "natural language processing": [
        "nlp", "spacy", "nltk", "huggingface", "transformers",
        "text mining", "sentiment analysis", "named entity recognition",
        "text classification", "language models",
    ],

    # --- Scientific & Research ---
    "scientific analysis": [
        "numpy", "scipy", "matlab", "data analysis", "statistics",
        "research methodology", "experimental design", "lab analysis",
        "scientific computing", "pandas", "r programming",
    ],
    "research": [
        "data analysis", "statistics", "literature review",
        "experimental design", "research methodology",
        "scientific computing", "publications", "peer review",
    ],

    # --- Programming & Development ---
    "programming": [
        "python", "java", "c++", "c#", "javascript", "typescript",
        "ruby", "go", "golang", "rust", "scala", "kotlin",
        "swift", "php", "perl", "coding", "software development",
        "software engineering", "scripting", "bash", "shell",
    ],
    "coding": [
        "python", "java", "c++", "javascript", "typescript",
        "programming", "software development", "scripting",
    ],
    "software development": [
        "python", "java", "c++", "javascript", "typescript",
        "git", "agile", "scrum", "ci/cd", "software engineering",
        "programming", "coding", "design patterns", "oop",
        "test-driven development", "tdd", "code review",
    ],
    "software engineering": [
        "programming", "software development", "system design",
        "design patterns", "oop", "algorithms", "data structures",
        "git", "ci/cd", "agile", "testing",
    ],
    "scripting": [
        "python", "bash", "shell", "powershell", "perl",
        "automation", "scripting languages",
    ],

    # --- Web Development ---
    "web development": [
        "html", "css", "javascript", "typescript", "react",
        "angular", "vue", "node.js", "django", "flask",
        "fastapi", "express", "next.js", "html/css",
        "frontend", "backend", "full stack",
    ],
    "frontend development": [
        "html", "css", "javascript", "typescript", "react",
        "angular", "vue", "sass", "tailwind", "responsive design",
        "html/css", "frontend",
    ],
    "backend development": [
        "python", "java", "node.js", "django", "flask",
        "fastapi", "express", "spring", "rest apis", "graphql",
        "microservices", "backend",
    ],

    # --- Database & Storage ---
    "database management": [
        "sql", "mysql", "postgresql", "oracle", "sqlite",
        "mongodb", "redis", "cassandra", "dynamodb",
        "database", "database administration", "dba",
        "database design", "schema design", "data modeling",
        "nosql", "database optimization", "indexing",
    ],
    "database": [
        "sql", "mysql", "postgresql", "oracle", "sqlite",
        "mongodb", "redis", "database management", "nosql",
    ],
    "sql": [
        "mysql", "postgresql", "oracle", "sqlite", "t-sql",
        "pl/sql", "database", "queries", "stored procedures",
    ],

    # --- Cloud & Infrastructure ---
    "cloud computing": [
        "aws", "azure", "gcp", "google cloud", "cloud",
        "ec2", "s3", "lambda", "cloud formation",
        "terraform", "cloud architecture", "iaas", "paas", "saas",
    ],
    "aws": [
        "amazon web services", "ec2", "s3", "lambda", "rds",
        "dynamodb", "cloudformation", "cloud computing",
        "sagemaker", "ecs", "eks",
    ],
    "devops": [
        "ci/cd", "docker", "kubernetes", "jenkins", "github actions",
        "gitlab ci", "terraform", "ansible", "infrastructure as code",
        "monitoring", "deployment", "automation",
    ],
    "containerization": [
        "docker", "kubernetes", "container", "k8s",
        "docker compose", "container orchestration", "ecs", "eks",
    ],

    # --- Networking & Security ---
    "cybersecurity": [
        "security", "penetration testing", "vulnerability assessment",
        "encryption", "firewall", "siem", "incident response",
        "information security", "network security", "infosec",
        "compliance", "risk assessment",
    ],
    "network engineering": [
        "networking", "tcp/ip", "dns", "vpn", "firewall",
        "routing", "switching", "network administration",
        "cisco", "load balancing",
    ],

    # --- Project & Process Management ---
    "project management": [
        "agile", "scrum", "kanban", "jira", "project planning",
        "stakeholder management", "risk management", "pmp",
        "waterfall", "sprint planning", "project lifecycle",
    ],
    "agile": [
        "scrum", "kanban", "sprint", "jira", "agile methodology",
        "sprint planning", "retrospective", "user stories",
        "continuous improvement",
    ],

    # --- APIs & Integration ---
    "rest apis": [
        "api development", "restful", "api design", "swagger",
        "openapi", "postman", "api integration", "web services",
        "json", "http",
    ],
    "api development": [
        "rest apis", "restful", "graphql", "swagger", "openapi",
        "api design", "web services", "microservices",
    ],

    # --- Version Control ---
    "version control": [
        "git", "github", "gitlab", "bitbucket", "svn",
        "branching", "merging", "pull requests",
    ],
    "git": [
        "github", "gitlab", "bitbucket", "version control",
        "branching", "merging",
    ],

    # --- Testing & QA ---
    "testing": [
        "unit testing", "integration testing", "pytest", "jest",
        "selenium", "test automation", "qa", "quality assurance",
        "tdd", "test-driven development", "ci/cd",
    ],

    # --- Systems & Architecture ---
    "system administration": [
        "linux", "windows server", "sysadmin", "system admin",
        "active directory", "dns", "dhcp", "monitoring",
        "troubleshooting", "infrastructure",
    ],
    "linux": [
        "ubuntu", "centos", "redhat", "rhel", "debian",
        "bash", "shell", "system administration", "unix",
    ],

    # --- Communication & Soft Skills ---
    "technical writing": [
        "documentation", "technical documentation", "user guides",
        "api documentation", "writing", "content creation",
    ],
    "technical documentation": [
        "documentation", "technical writing", "user guides",
        "api documentation", "readme", "wiki",
    ],
    "communication": [
        "written communication", "verbal communication",
        "presentation", "public speaking", "reporting",
        "stakeholder communication", "technical writing",
    ],
    "problem solving": [
        "analytical thinking", "critical thinking", "debugging",
        "troubleshooting", "root cause analysis", "analysis",
    ],
    "leadership": [
        "team management", "mentoring", "coaching",
        "team lead", "management", "supervision",
    ],
    "teamwork": [
        "collaboration", "cross-functional", "team player",
        "interpersonal skills", "cooperative",
    ],
}


# ==================================================================
# PRECOMPUTED REVERSE INDEX
# ==================================================================
# Maps each individual technology/synonym back to the categories it satisfies.
# Built once at import time for O(1) lookups during scoring.
# ==================================================================

def _build_reverse_index() -> dict[str, set[str]]:
    """Build a reverse mapping: technology → set of parent categories."""
    reverse: dict[str, set[str]] = {}
    for category, synonyms in SKILL_TAXONOMY.items():
        # The category itself maps to itself
        reverse.setdefault(category, set()).add(category)
        for synonym in synonyms:
            syn_lower = synonym.lower()
            reverse.setdefault(syn_lower, set()).add(category)
    return reverse


REVERSE_SKILL_INDEX: dict[str, set[str]] = _build_reverse_index()


def get_categories_for_skill(skill: str) -> set[str]:
    """
    Return all parent categories that a given skill/technology satisfies.

    Parameters
    ----------
    skill : str
        A concrete technology or skill name (e.g., "pandas", "python").

    Returns
    -------
    set[str]
        Set of category names this skill maps to, or empty set if unknown.
    """
    return REVERSE_SKILL_INDEX.get(skill.lower().strip(), set())


def get_synonyms_for_category(category: str) -> list[str]:
    """
    Return all synonyms/technologies for a given skill category.

    Parameters
    ----------
    category : str
        A skill category name (e.g., "statistical analysis").

    Returns
    -------
    list[str]
        List of synonyms, or empty list if category is unknown.
    """
    return SKILL_TAXONOMY.get(category.lower().strip(), [])
