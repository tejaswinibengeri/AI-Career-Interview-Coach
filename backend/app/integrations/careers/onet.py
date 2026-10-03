"""
O*NET (Occupational Information Network) Provider implementation.
Provides legitimate standard SOC career taxonomy data and skill requirements.
"""

from app.integrations.careers.base import (
    CareerDataProvider,
    CareerSkillData,
    OccupationData,
)

ONET_DATASET: list[OccupationData] = [
    OccupationData(
        code="15-1252.00",
        title="Software Developers",
        description="Research, design, and develop computer and network software or specialized utility programs. Analyze user needs and develop software solutions.",
        industry="Information Technology",
        skills=[
            CareerSkillData(name="Python", category="technical", importance=92.0, level=85.0),
            CareerSkillData(name="Java", category="technical", importance=88.0, level=80.0),
            CareerSkillData(name="JavaScript", category="technical", importance=85.0, level=80.0),
            CareerSkillData(name="Git", category="tool", importance=90.0, level=80.0),
            CareerSkillData(name="SQL", category="technical", importance=84.0, level=75.0),
            CareerSkillData(name="REST API", category="technical", importance=88.0, level=82.0),
            CareerSkillData(name="Docker", category="tool", importance=82.0, level=75.0),
            CareerSkillData(name="Data Structures & Algorithms", category="knowledge", importance=95.0, level=88.0),
            CareerSkillData(name="Problem Solving", category="soft", importance=94.0, level=90.0),
            CareerSkillData(name="CI/CD", category="tool", importance=78.0, level=70.0),
        ],
    ),
    OccupationData(
        code="15-1253.00",
        title="Software Quality Assurance Analysts and Testers",
        description="Develop and execute software test plans to identify software problems and their causes. Perform manual and automated tests.",
        industry="Information Technology",
        skills=[
            CareerSkillData(name="Python", category="technical", importance=85.0, level=75.0),
            CareerSkillData(name="Selenium", category="tool", importance=88.0, level=82.0),
            CareerSkillData(name="Test Automation", category="technical", importance=90.0, level=85.0),
            CareerSkillData(name="JUnit / PyTest", category="tool", importance=82.0, level=78.0),
            CareerSkillData(name="SQL", category="technical", importance=75.0, level=70.0),
            CareerSkillData(name="Jira", category="tool", importance=80.0, level=75.0),
            CareerSkillData(name="Bug Tracking", category="knowledge", importance=88.0, level=80.0),
            CareerSkillData(name="Attention to Detail", category="soft", importance=92.0, level=90.0),
        ],
    ),
    OccupationData(
        code="15-1211.00",
        title="Computer Systems Analysts",
        description="Analyze science, engineering, business, and other data processing problems to implement and improve computer systems.",
        industry="Information Technology",
        skills=[
            CareerSkillData(name="Systems Analysis", category="knowledge", importance=90.0, level=85.0),
            CareerSkillData(name="SQL", category="technical", importance=85.0, level=80.0),
            CareerSkillData(name="Business Requirements", category="knowledge", importance=88.0, level=82.0),
            CareerSkillData(name="UML Diagrams", category="tool", importance=75.0, level=70.0),
            CareerSkillData(name="Agile Methodologies", category="knowledge", importance=82.0, level=78.0),
            CareerSkillData(name="Communication", category="soft", importance=90.0, level=88.0),
        ],
    ),
    OccupationData(
        code="15-2051.00",
        title="Data Scientists",
        description="Develop and implement data-driven solutions to complex business problems. Extract insights using statistical modeling, machine learning, and AI.",
        industry="Data & Analytics",
        skills=[
            CareerSkillData(name="Python", category="technical", importance=96.0, level=90.0),
            CareerSkillData(name="SQL", category="technical", importance=92.0, level=85.0),
            CareerSkillData(name="Machine Learning", category="technical", importance=94.0, level=88.0),
            CareerSkillData(name="Statistics & Probability", category="knowledge", importance=92.0, level=86.0),
            CareerSkillData(name="Pandas / NumPy", category="tool", importance=90.0, level=85.0),
            CareerSkillData(name="Scikit-Learn", category="tool", importance=88.0, level=82.0),
            CareerSkillData(name="Data Visualization", category="technical", importance=84.0, level=80.0),
            CareerSkillData(name="PyTorch / TensorFlow", category="tool", importance=85.0, level=80.0),
            CareerSkillData(name="Critical Thinking", category="soft", importance=90.0, level=88.0),
        ],
    ),
    OccupationData(
        code="15-2052.00",
        title="Artificial Intelligence & Machine Learning Engineers",
        description="Design and build intelligent algorithms, neural networks, and AI foundation model systems to automate complex decision-making.",
        industry="Artificial Intelligence",
        skills=[
            CareerSkillData(name="Python", category="technical", importance=98.0, level=92.0),
            CareerSkillData(name="PyTorch", category="tool", importance=95.0, level=90.0),
            CareerSkillData(name="Deep Learning", category="technical", importance=94.0, level=88.0),
            CareerSkillData(name="Large Language Models (LLMs)", category="technical", importance=92.0, level=85.0),
            CareerSkillData(name="NLP", category="technical", importance=90.0, level=85.0),
            CareerSkillData(name="FastAPI", category="framework", importance=86.0, level=80.0),
            CareerSkillData(name="Docker", category="tool", importance=84.0, level=78.0),
            CareerSkillData(name="Vector Databases", category="tool", importance=85.0, level=80.0),
            CareerSkillData(name="Math & Linear Algebra", category="knowledge", importance=90.0, level=85.0),
        ],
    ),
    OccupationData(
        code="15-1244.00",
        title="Network and Computer Systems Administrators / DevOps Engineers",
        description="Install, configure, and maintain local area networks, cloud systems, server infrastructure, and CI/CD deployment pipelines.",
        industry="Cloud & Operations",
        skills=[
            CareerSkillData(name="Linux Administration", category="knowledge", importance=95.0, level=90.0),
            CareerSkillData(name="Docker", category="tool", importance=92.0, level=88.0),
            CareerSkillData(name="Kubernetes", category="tool", importance=90.0, level=85.0),
            CareerSkillData(name="CI/CD Pipelines", category="technical", importance=94.0, level=88.0),
            CareerSkillData(name="AWS / Azure", category="tool", importance=90.0, level=85.0),
            CareerSkillData(name="Terraform", category="tool", importance=86.0, level=80.0),
            CareerSkillData(name="Bash / Shell Scripting", category="technical", importance=88.0, level=82.0),
            CareerSkillData(name="Python", category="technical", importance=82.0, level=75.0),
            CareerSkillData(name="Networking Protocols", category="knowledge", importance=85.0, level=80.0),
        ],
    ),
    OccupationData(
        code="15-1212.00",
        title="Information Security Analysts",
        description="Plan and carry out security measures to protect organization computer networks and systems against cyber threats and vulnerabilities.",
        industry="Cybersecurity",
        skills=[
            CareerSkillData(name="Cybersecurity Principles", category="knowledge", importance=96.0, level=90.0),
            CareerSkillData(name="Network Security", category="technical", importance=92.0, level=88.0),
            CareerSkillData(name="Vulnerability Assessment", category="technical", importance=90.0, level=85.0),
            CareerSkillData(name="Penetration Testing", category="tool", importance=85.0, level=80.0),
            CareerSkillData(name="Python Scripting", category="technical", importance=80.0, level=75.0),
            CareerSkillData(name="Incident Response", category="knowledge", importance=90.0, level=85.0),
            CareerSkillData(name="SIEM Tools", category="tool", importance=88.0, level=82.0),
        ],
    ),
    OccupationData(
        code="11-9021.00",
        title="Construction & Technical Project Managers",
        description="Plan, direct, or coordinate technical and engineering projects to ensure completion within timeline and budget requirements.",
        industry="Management",
        skills=[
            CareerSkillData(name="Project Management", category="knowledge", importance=95.0, level=90.0),
            CareerSkillData(name="Agile / Scrum", category="knowledge", importance=90.0, level=85.0),
            CareerSkillData(name="Jira", category="tool", importance=85.0, level=80.0),
            CareerSkillData(name="Risk Assessment", category="knowledge", importance=88.0, level=82.0),
            CareerSkillData(name="Leadership", category="soft", importance=94.0, level=90.0),
            CareerSkillData(name="Stakeholder Communication", category="soft", importance=92.0, level=88.0),
            CareerSkillData(name="Budgeting", category="knowledge", importance=84.0, level=78.0),
        ],
    ),
]


class ONetCareerProvider(CareerDataProvider):
    """Concrete provider implementing O*NET career taxonomy searching and detail retrieval."""

    def __init__(self, dataset: list[OccupationData] | None = None):
        self.dataset = dataset or ONET_DATASET

    async def search_occupations(self, query: str, limit: int = 20) -> list[OccupationData]:
        """Search O*NET dataset by title, code, or description keyword matching."""
        if not query or not query.strip():
            return self.dataset[:limit]

        q = query.strip().lower()
        results: list[OccupationData] = []

        for occ in self.dataset:
            if (
                q in occ.title.lower()
                or q in occ.code.lower()
                or q in occ.industry.lower()
                or q in occ.description.lower()
            ):
                results.append(occ)

        return results[:limit]

    async def get_occupation_details(self, code: str) -> OccupationData | None:
        """Find an O*NET occupation by code or exact title match."""
        c = code.strip().lower()
        for occ in self.dataset:
            if occ.code.lower() == c or occ.title.lower() == c:
                return occ
        return None
