"""
Achievement and Badges Evaluation Service (Module 18).
Evaluates real user database activity and awards achievements automatically.
"""

from datetime import datetime, timezone
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.achievement import Achievement, UserAchievement
from app.models.coding import CodingSubmission
from app.models.interview import InterviewEvaluation, InterviewQuestion, InterviewSession
from app.models.learning_resource import UserLearningProgress
from app.models.resume import ResumeVersion
from app.models.resume_analysis import ResumeAnalysis
from app.models.roadmap import Roadmap, RoadmapItem, RoadmapProgress
from app.models.user import User

from app.schemas.achievement import AchievementResponse, AchievementSummaryResponse

# Standard system achievement catalog definitions
SYSTEM_ACHIEVEMENTS = [
    {
        "slug": "first_resume",
        "title": "First Resume Uploaded",
        "description": "Uploaded your first resume document to the career platform.",
        "icon": "📄",
        "category": "Resume",
        "threshold": 1,
    },
    {
        "slug": "first_resume_analysis",
        "title": "First Resume Analysis",
        "description": "Completed your first AI ATS resume evaluation.",
        "icon": "🔍",
        "category": "Resume",
        "threshold": 1,
    },
    {
        "slug": "ats_score_high",
        "title": "ATS Score Master (75+)",
        "description": "Achieved an ATS score of 75 or higher on a resume version.",
        "icon": "🎯",
        "category": "Resume",
        "threshold": 75,
    },
    {
        "slug": "first_interview",
        "title": "First Mock Interview",
        "description": "Completed your first interactive AI mock interview session.",
        "icon": "🎙️",
        "category": "Interview",
        "threshold": 1,
    },
    {
        "slug": "interview_score_high",
        "title": "Interview Specialist (75%+)",
        "description": "Achieved an overall interview evaluation score of 75% or higher.",
        "icon": "🌟",
        "category": "Interview",
        "threshold": 75,
    },
    {
        "slug": "first_coding_challenge",
        "title": "First Code Solution",
        "description": "Submitted a coding challenge that passed all test cases in the sandbox.",
        "icon": "💻",
        "category": "Coding",
        "threshold": 1,
    },
    {
        "slug": "learning_milestone",
        "title": "Skill Scholar",
        "description": "Completed a verified skill-gap learning resource or course.",
        "icon": "📚",
        "category": "Learning",
        "threshold": 1,
    },
    {
        "slug": "roadmap_milestone",
        "title": "Roadmap Pathfinder",
        "description": "Marked a career milestone as completed in your learning roadmap.",
        "icon": "🗺️",
        "category": "Roadmap",
        "threshold": 1,
    },
    {
        "slug": "improvement_milestone",
        "title": "Continuous Growth",
        "description": "Demonstrated measurable score improvement across interview sessions.",
        "icon": "📈",
        "category": "Growth",
        "threshold": 1,
    },
]


async def ensure_system_achievements_seeded(db: AsyncSession) -> None:
    """Ensure catalog of system achievements exists in database."""
    res = await db.execute(select(Achievement))
    existing = {a.slug for a in res.scalars().all()}

    for item in SYSTEM_ACHIEVEMENTS:
        if item["slug"] not in existing:
            ach = Achievement(
                slug=item["slug"],
                title=item["title"],
                description=item["description"],
                icon=item["icon"],
                category=item["category"],
                threshold=item["threshold"],
            )
            db.add(ach)
    await db.commit()


async def evaluate_and_get_user_achievements(
    db: AsyncSession, user: User
) -> AchievementSummaryResponse:
    """Evaluate candidate's REAL database activity and update/award achievement status."""
    await ensure_system_achievements_seeded(db)

    # 1. Gather real user activity metrics from DB
    # Resume uploads count
    res_count = await db.execute(
        select(func.count(ResumeVersion.id))
        .join(ResumeVersion.resume)
        .where(ResumeVersion.resume.has(user_id=user.id))
    )
    resume_uploads_count = res_count.scalar() or 0

    # Resume analyses count & max ATS score
    an_count = await db.execute(
        select(func.count(ResumeAnalysis.id), func.max(ResumeAnalysis.ats_score)).where(
            ResumeAnalysis.user_id == user.id
        )
    )
    an_row = an_count.first()
    resume_analysis_count = (an_row[0] if an_row else 0) or 0
    max_ats_score = int(an_row[1] or 0) if an_row else 0

    # Mock Interviews count & max overall score & improvement
    int_res = await db.execute(
        select(InterviewSession)
        .where(InterviewSession.user_id == user.id, InterviewSession.status == "completed")
        .order_by(InterviewSession.created_at.asc())
    )
    completed_interviews = int_res.scalars().all()
    interviews_count = len(completed_interviews)

    max_interview_score = 0
    score_improved = False
    if completed_interviews:
        # Calculate average score per session
        session_scores = []
        for sess in completed_interviews:
            q_res = await db.execute(
                select(func.avg(InterviewEvaluation.overall_score))
                .join(InterviewEvaluation.question)
                .where(InterviewQuestion.session_id == sess.id)
            )
            avg_s = q_res.scalar()
            if avg_s is not None:
                session_scores.append(round(avg_s, 1))

        if session_scores:
            max_interview_score = int(max(session_scores))
            if len(session_scores) >= 2 and session_scores[-1] > session_scores[0]:
                score_improved = True

    # Coding submissions passed count
    code_res = await db.execute(
        select(func.count(CodingSubmission.id)).where(
            CodingSubmission.user_id == user.id, CodingSubmission.status == "Passed"
        )
    )
    passed_coding_count = code_res.scalar() or 0

    # Learning resources completed count
    learn_res = await db.execute(
        select(func.count(UserLearningProgress.id)).where(
            UserLearningProgress.user_id == user.id, UserLearningProgress.is_completed == True
        )
    )
    completed_learning_count = learn_res.scalar() or 0

    # Roadmap items completed count
    road_res = await db.execute(
        select(func.count(RoadmapItem.id))
        .join(RoadmapItem.roadmap)
        .where(Roadmap.user_id == user.id, RoadmapItem.is_completed == True)
    )
    completed_roadmap_count = road_res.scalar() or 0


    # Map slugs to evaluated real progress metrics
    progress_map = {
        "first_resume": resume_uploads_count,
        "first_resume_analysis": resume_analysis_count,
        "ats_score_high": max_ats_score,
        "first_interview": interviews_count,
        "interview_score_high": max_interview_score,
        "first_coding_challenge": passed_coding_count,
        "learning_milestone": completed_learning_count,
        "roadmap_milestone": completed_roadmap_count,
        "improvement_milestone": 1 if score_improved else 0,
    }

    # Fetch all catalog achievements
    ach_res = await db.execute(select(Achievement))
    all_achievements = ach_res.scalars().all()

    # Fetch existing user achievements
    ua_res = await db.execute(
        select(UserAchievement).where(UserAchievement.user_id == user.id)
    )
    user_ach_map = {ua.achievement_id: ua for ua in ua_res.scalars().all()}

    response_items: list[AchievementResponse] = []
    earned_count = 0

    for ach in all_achievements:
        prog = progress_map.get(ach.slug, 0)
        ua = user_ach_map.get(ach.id)

        is_earned = False
        earned_at = None

        if ua:
            ua.current_progress = prog
            if prog >= ach.threshold:
                if not ua.is_earned:
                    ua.is_earned = True
                    ua.earned_at = datetime.now(timezone.utc)
                is_earned = True
                earned_at = ua.earned_at
            else:
                is_earned = ua.is_earned
                earned_at = ua.earned_at
        else:
            is_earned = prog >= ach.threshold
            if is_earned:
                earned_at = datetime.now(timezone.utc)

            ua = UserAchievement(
                user_id=user.id,
                achievement_id=ach.id,
                current_progress=prog,
                is_earned=is_earned,
                earned_at=earned_at,
            )
            db.add(ua)

        if is_earned:
            earned_count += 1

        response_items.append(
            AchievementResponse(
                id=ach.id,
                slug=ach.slug,
                title=ach.title,
                description=ach.description,
                icon=ach.icon,
                category=ach.category,
                threshold=ach.threshold,
                current_progress=min(prog, ach.threshold) if ach.slug not in ["ats_score_high", "interview_score_high"] else prog,
                is_earned=is_earned,
                earned_at=earned_at,
            )
        )

    await db.commit()

    total_count = len(all_achievements)
    completion_pct = round((earned_count / total_count * 100), 1) if total_count > 0 else 0.0

    return AchievementSummaryResponse(
        total_achievements=total_count,
        earned_count=earned_count,
        completion_percentage=completion_pct,
        achievements=response_items,
    )
