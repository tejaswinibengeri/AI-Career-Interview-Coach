"""
Interview Performance & Placement Readiness Service.
Calculates performance stats and transparent readiness scores strictly from real stored database activity.
"""

from collections import defaultdict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.career import SkillGapReport
from app.models.interview import InterviewAnswer, InterviewEvaluation, InterviewQuestion, InterviewSession
from app.models.resume import Resume
from app.models.resume_analysis import ResumeAnalysis
from app.models.user import User
from app.schemas.performance import (
    PerformanceResponse,
    ReadinessMetricComponent,
    ReadinessResponse,
    ScoreHistoryItem,
    TopicPerformanceItem,
)
from app.services.profile_service import get_or_create_profile


async def get_user_performance_data(db: AsyncSession, user: User) -> PerformanceResponse:
    """Calculate interview performance metrics strictly from completed user mock interviews."""
    query = (
        select(InterviewSession)
        .where(InterviewSession.user_id == user.id, InterviewSession.status == "completed")
        .order_by(InterviewSession.created_at.asc())
    )
    res = await db.execute(query)
    completed_sessions = list(res.scalars().all())

    total_interviews = len(completed_sessions)

    if total_interviews == 0:
        return PerformanceResponse(
            total_interviews=0,
            average_score=None,
            best_score=None,
            latest_score=None,
            improvement=None,
            technical_score=None,
            communication_score=None,
            weak_topics=[],
            strong_topics=[],
            score_history=[],
            has_enough_data=False,
            status_message="Not enough interview data. Complete mock interviews to view performance analytics.",
        )

    scores = [s.overall_score for s in completed_sessions if s.overall_score is not None]

    if not scores:
        return PerformanceResponse(
            total_interviews=total_interviews,
            average_score=None,
            best_score=None,
            latest_score=None,
            improvement=None,
            technical_score=None,
            communication_score=None,
            weak_topics=[],
            strong_topics=[],
            score_history=[],
            has_enough_data=False,
            status_message="Interview sessions completed, but answer evaluations are pending.",
        )

    avg_score = round(sum(scores) / len(scores), 1)
    best_score = round(max(scores), 1)
    latest_score = round(scores[-1], 1)
    first_score = round(scores[0], 1)
    improvement = round(latest_score - first_score, 1)

    score_history: list[ScoreHistoryItem] = []
    for idx, s in enumerate(completed_sessions):
        if s.overall_score is not None:
            score_history.append(
                ScoreHistoryItem(
                    interview_number=idx + 1,
                    session_id=s.id,
                    role=s.role,
                    difficulty=s.difficulty,
                    score=s.overall_score,
                    date=s.created_at,
                )
            )

    eval_query = (
        select(InterviewEvaluation, InterviewQuestion.category)
        .join(InterviewAnswer, InterviewEvaluation.answer_id == InterviewAnswer.id)
        .join(InterviewQuestion, InterviewAnswer.question_id == InterviewQuestion.id)
        .join(InterviewSession, InterviewAnswer.session_id == InterviewSession.id)
        .where(InterviewSession.user_id == user.id, InterviewSession.status == "completed")
    )
    eval_res = await db.execute(eval_query)
    eval_rows = eval_res.all()

    tech_scores: list[float] = []
    comm_scores: list[float] = []
    category_map: dict[str, list[float]] = defaultdict(list)

    for ev, cat in eval_rows:
        tech_scores.append(ev.technical_correctness)
        comm_scores.append(ev.communication)
        cat_name = cat or "General"
        category_map[cat_name].append(ev.overall_score)

    technical_score = round(sum(tech_scores) / len(tech_scores), 1) if tech_scores else None
    communication_score = round(sum(comm_scores) / len(comm_scores), 1) if comm_scores else None

    topic_items: list[TopicPerformanceItem] = []
    for cat_name, cat_scores in category_map.items():
        avg_cat = round(sum(cat_scores) / len(cat_scores), 1)
        topic_items.append(
            TopicPerformanceItem(
                topic=cat_name,
                avg_score=avg_cat,
                questions_count=len(cat_scores),
            )
        )

    topic_items.sort(key=lambda x: x.avg_score, reverse=True)
    strong_topics = [t for t in topic_items if t.avg_score >= 75.0]
    weak_topics = [t for t in topic_items if t.avg_score < 75.0]

    if not weak_topics and len(topic_items) > 1:
        weak_topics = topic_items[-2:]
    if not strong_topics and topic_items:
        strong_topics = topic_items[:2]

    return PerformanceResponse(
        total_interviews=total_interviews,
        average_score=avg_score,
        best_score=best_score,
        latest_score=latest_score,
        improvement=improvement,
        technical_score=technical_score,
        communication_score=communication_score,
        weak_topics=weak_topics,
        strong_topics=strong_topics,
        score_history=score_history,
        has_enough_data=True,
        status_message=f"Calculated from {total_interviews} completed interview session(s).",
    )


async def get_user_readiness_data(db: AsyncSession, user: User) -> ReadinessResponse:
    """Calculate Placement Readiness using transparent formula and available real metrics."""
    # 1. Resume ATS score
    resume_score: float | None = None
    res_query = (
        select(ResumeAnalysis)
        .join(Resume, ResumeAnalysis.resume_id == Resume.id)
        .where(Resume.user_id == user.id)
        .order_by(ResumeAnalysis.created_at.desc())
    )
    res_res = await db.execute(res_query)
    latest_analysis = res_res.scalars().first()
    if latest_analysis:
        resume_score = float(latest_analysis.ats_score)

    # 2. Skills score (from SkillGapReport or Profile)
    skills_score: float | None = None
    sg_query = (
        select(SkillGapReport)
        .where(SkillGapReport.user_id == user.id)
        .order_by(SkillGapReport.created_at.desc())
    )
    sg_res = await db.execute(sg_query)
    latest_sg = sg_res.scalars().first()
    if latest_sg:
        skills_score = float(latest_sg.match_percentage)
    else:
        profile = await get_or_create_profile(db, user.id)
        if profile and profile.skills:
            skills_score = min(100.0, float(len(profile.skills) * 15))

    # 3. Interview performance score
    interview_score: float | None = None
    perf_data = await get_user_performance_data(db, user)
    if perf_data.has_enough_data and perf_data.average_score is not None:
        interview_score = perf_data.average_score

    # 4. Coding practice score
    coding_score: float | None = None
    eval_coding_query = (
        select(InterviewEvaluation)
        .join(InterviewAnswer, InterviewEvaluation.answer_id == InterviewAnswer.id)
        .join(InterviewQuestion, InterviewAnswer.question_id == InterviewQuestion.id)
        .join(InterviewSession, InterviewAnswer.session_id == InterviewSession.id)
        .where(
            InterviewSession.user_id == user.id,
            InterviewQuestion.category.ilike("%Coding%") | InterviewQuestion.category.ilike("%DSA%"),
        )
    )
    eval_coding_res = await db.execute(eval_coding_query)
    coding_evals = list(eval_coding_res.scalars().all())
    if coding_evals:
        coding_score = round(sum(ev.overall_score for ev in coding_evals) / len(coding_evals), 1)

    raw_components = [
        {"key": "resume", "name": "Resume ATS Score", "score": resume_score, "raw_weight": 0.25},
        {"key": "skills", "name": "Skill Match & Gap", "score": skills_score, "raw_weight": 0.25},
        {"key": "interview", "name": "Mock Interview Score", "score": interview_score, "raw_weight": 0.35},
        {"key": "coding", "name": "Coding Practice", "score": coding_score, "raw_weight": 0.15},
    ]

    available_components = [c for c in raw_components if c["score"] is not None]
    total_available_weight = sum(c["raw_weight"] for c in available_components)

    breakdown: list[ReadinessMetricComponent] = []
    weighted_sum = 0.0

    for comp in raw_components:
        is_avail = comp["score"] is not None
        if is_avail and total_available_weight > 0:
            eff_weight = round((comp["raw_weight"] / total_available_weight) * 100, 1)
            weighted_sum += comp["score"] * (comp["raw_weight"] / total_available_weight) # type: ignore
            status_str = f"{comp['score']}% Score"
        else:
            eff_weight = 0.0
            status_str = "Not enough data"

        breakdown.append(
            ReadinessMetricComponent(
                key=comp["key"],
                name=comp["name"],
                available=is_avail,
                score=comp["score"],
                raw_weight=comp["raw_weight"],
                effective_weight_percentage=eff_weight,
                status=status_str,
            )
        )

    recommendations: list[str] = []

    if len(available_components) == 0:
        overall_score = None
        level = "Not Evaluated"
        status_message = "Not enough data to calculate placement readiness. Complete a resume analysis or mock interview to view your score."
        recommendations.append("Upload your resume for AI ATS analysis.")
        recommendations.append("Take your first AI Mock Interview session.")
        recommendations.append("Run a Skill Gap analysis against target career roles.")
    else:
        overall_score = round(weighted_sum, 1)
        if overall_score >= 80.0:
            level = "Job Ready"
            status_message = "Outstanding candidate profile! You are well-positioned for placement."
        elif overall_score >= 65.0:
            level = "Nearly Ready"
            status_message = "Solid foundation! Improve lowest scoring areas to achieve top readiness."
        else:
            level = "Needs Preparation"
            status_message = "Additional practice recommended to reach benchmark placement readiness."

        if resume_score is None:
            recommendations.append("Upload your resume for ATS analysis to include resume score in readiness calculation.")
        elif resume_score < 70.0:
            recommendations.append("Update resume formatting & keywords to boost your ATS score.")

        if interview_score is None:
            recommendations.append("Complete a Mock Interview session to evaluate communication & technical readiness.")
        elif interview_score < 70.0:
            recommendations.append("Practice additional mock interviews in weak topic categories.")

        if skills_score is None:
            recommendations.append("Run a Skill Gap report for your target occupation.")

        if coding_score is None:
            recommendations.append("Answer Coding & DSA interview questions in the Mock Interview room.")

    return ReadinessResponse(
        overall_readiness_score=overall_score,
        level=level,
        status_message=status_message,
        available_metrics_count=len(available_components),
        total_metrics_count=len(raw_components),
        breakdown=breakdown,
        recommendations=recommendations,
    )
