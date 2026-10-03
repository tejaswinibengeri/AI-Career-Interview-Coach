"""
Models package initialization.
"""

from app.models.career import (
    CareerGoal,
    Occupation,
    OccupationSkill,
    Skill,
    SkillGapReport,
    UserSkill,
)
from app.models.coding import CodingChallenge, CodingResult, CodingSubmission
from app.models.company_prep import CompanyPrepPlan
from app.models.interview import (
    InterviewAnswer,
    InterviewEvaluation,
    InterviewQuestion,
    InterviewSession,
)
from app.models.job import Job, SavedJob
from app.models.job_match import JobMatch
from app.models.career_intelligence import ColdEmail, CoverLetter, ResumeJdMatch
from app.models.achievement import Achievement, UserAchievement
from app.models.learning_resource import LearningResource, UserLearningProgress
from app.models.notification import Notification, NotificationPreference
from app.models.project_recommendation import ProjectRecommendation
from app.models.question import Question, SavedQuestion
from app.models.resume import Resume, ResumeVersion
from app.models.resume_analysis import ResumeAnalysis, ResumeSkill
from app.models.roadmap import Roadmap, RoadmapItem, RoadmapProgress
from app.models.personal_trainer import (
    PersonalTrainerSettings,
    TrainingDay,
    TrainingPlan,
    TrainingTask,
)
from app.models.user import Profile, User

__all__ = [
    "User",
    "Profile",
    "TrainingPlan",
    "TrainingDay",
    "TrainingTask",
    "PersonalTrainerSettings",
    "Resume",
    "ResumeVersion",
    "ResumeAnalysis",
    "ResumeSkill",
    "Occupation",
    "Skill",
    "OccupationSkill",
    "UserSkill",
    "CareerGoal",
    "SkillGapReport",
    "Roadmap",
    "RoadmapItem",
    "RoadmapProgress",
    "Job",
    "SavedJob",
    "JobMatch",
    "ResumeJdMatch",
    "CoverLetter",
    "ColdEmail",
    "Question",
    "SavedQuestion",
    "InterviewSession",
    "InterviewQuestion",
    "InterviewAnswer",
    "InterviewEvaluation",
    "CodingChallenge",
    "CodingSubmission",
    "CodingResult",
    "CompanyPrepPlan",
    "LearningResource",
    "UserLearningProgress",
    "ProjectRecommendation",
    "Achievement",
    "UserAchievement",
    "Notification",
    "NotificationPreference",
]






