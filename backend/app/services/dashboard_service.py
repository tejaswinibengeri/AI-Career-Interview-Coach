"""
Dashboard service — aggregates real user database records into a single payload.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.dashboard import (
    ActivityItem,
    CodingStatsSummary,
    DashboardResponse,
    InterviewStatsSummary,
    PlacementReadinessSummary,
    ProfileSummary,
    ResumeSummary,
    SkillProgressSummary,
)
from app.services.profile_service import get_or_create_profile
from app.services.resume_service import get_current_version, get_user_resumes


def calculate_profile_completion(profile) -> int:
    """Calculate profile completion percentage based on filled profile attributes."""
    tracked_fields = [
        profile.education,
        profile.degree,
        profile.graduation_year,
        profile.experience,
        profile.current_role,
        profile.target_role,
        profile.skills if profile.skills else None,
        profile.preferred_location,
        profile.work_preference,
        profile.career_goal,
    ]
    filled = sum(1 for val in tracked_fields if val is not None and val != "")
    return int((filled / len(tracked_fields)) * 100)


async def get_user_dashboard_data(db: AsyncSession, user: User) -> DashboardResponse:
    """Aggregate actual user information from database into DashboardResponse schema."""
    profile = await get_or_create_profile(db, user.id)
    completion_pct = calculate_profile_completion(profile)

    profile_summary = ProfileSummary(
        name=user.name,
        email=user.email,
        current_role=profile.current_role,
        target_role=profile.target_role,
        education=profile.education,
        degree=profile.degree,
        graduation_year=profile.graduation_year,
        experience=profile.experience,
        preferred_location=profile.preferred_location,
        work_preference=profile.work_preference,
        completion_percentage=completion_pct,
    )

    activities: list[ActivityItem] = []

    # Real timestamped activity 1: Account Created
    activities.append(
        ActivityItem(
            id=f"act-user-{user.id}-created",
            activity_type="account_created",
            title="Account Created",
            description="Joined CareerCoach AI platform",
            timestamp=user.created_at,
        )
    )

    # Real timestamped activity 2: Profile Updated (if modified after creation)
    if profile.updated_at and (profile.updated_at - user.created_at).total_seconds() > 1:
        activities.append(
            ActivityItem(
                id=f"act-profile-{profile.id}-updated",
                activity_type="profile_updated",
                title="Profile Updated",
                description="Updated career profile details and preferences",
                timestamp=profile.updated_at,
            )
        )

    # Real resume status & activity
    resumes = await get_user_resumes(db, user.id)
    if resumes:
        latest_resume = resumes[0]
        cur_ver = get_current_version(latest_resume)
        if cur_ver:
            latest_score: float | None = None
            resume_status = "uploaded"
            if latest_resume.analyses:
                latest_score = latest_resume.analyses[0].ats_score
                resume_status = "analyzed"
                activities.append(
                    ActivityItem(
                        id=f"act-analysis-{latest_resume.analyses[0].id}",
                        activity_type="resume_analyzed",
                        title="Resume Analyzed by AI",
                        description=f"ATS Score computed: {latest_score}% for '{cur_ver.filename}'",
                        timestamp=latest_resume.analyses[0].created_at,
                    )
                )

            resume_summary = ResumeSummary(
                has_resume=True,
                filename=cur_ver.filename,
                uploaded_at=cur_ver.created_at,
                latest_ats_score=latest_score,
                status=resume_status,
            )
            activities.append(
                ActivityItem(
                    id=f"act-resume-{cur_ver.id}-uploaded",
                    activity_type="resume_uploaded",
                    title="Resume Uploaded",
                    description=f"Uploaded '{cur_ver.filename}' (v{cur_ver.version_number})",
                    timestamp=cur_ver.created_at,
                )
            )
        else:
            resume_summary = ResumeSummary(
                has_resume=False,
                filename=None,
                uploaded_at=None,
                latest_ats_score=None,
                status="no_resume",
            )
    else:
        resume_summary = ResumeSummary(
            has_resume=False,
            filename=None,
            uploaded_at=None,
            latest_ats_score=None,
            status="no_resume",
        )

    skills_list = profile.skills if profile.skills else []
    skills_summary = SkillProgressSummary(
        total_skills=len(skills_list),
        skills=skills_list,
    )

    # Check for recent Skill Gap Report
    try:
        from sqlalchemy import select
        from app.models.career import SkillGapReport
        sg_query = select(SkillGapReport).where(SkillGapReport.user_id == user.id).order_by(SkillGapReport.created_at.desc())
        sg_res = await db.execute(sg_query)
        latest_sg = sg_res.scalars().first()

        if latest_sg:
            occ_title = latest_sg.occupation.title if latest_sg.occupation else "Target Occupation"
            activities.append(
                ActivityItem(
                    id=f"act-skillgap-{latest_sg.id}",
                    activity_type="skill_gap_analyzed",
                    title="Skill Gap Analyzed",
                    description=f"Match Score: {latest_sg.match_percentage}% for target role '{occ_title}'",
                    timestamp=latest_sg.created_at,
                )
            )
    except Exception:
        pass

    # Fetch real interview stats & placement readiness from database
    from app.services.performance_service import get_user_performance_data, get_user_readiness_data

    perf_data = await get_user_performance_data(db, user)
    readiness_data = await get_user_readiness_data(db, user)

    last_int_date = perf_data.score_history[-1].date if perf_data.score_history else None

    interview_summary = InterviewStatsSummary(
        total_mock_interviews=perf_data.total_interviews,
        average_score=perf_data.average_score,
        last_interview_date=last_int_date,
    )

    coding_summary = CodingStatsSummary(
        total_problems_solved=len(perf_data.score_history),
        streak_days=1 if perf_data.total_interviews > 0 else 0,
        last_practiced_date=last_int_date,
    )

    placement_summary = PlacementReadinessSummary(
        readiness_score=readiness_data.overall_readiness_score,
        level=readiness_data.level,
        status_message=readiness_data.status_message,
    )


    # Sort recent activity descending by timestamp
    activities.sort(key=lambda x: x.timestamp, reverse=True)

    return DashboardResponse(
        welcome_message=f"Welcome back, {user.name}!",
        profile=profile_summary,
        career_goal=profile.career_goal,
        resume=resume_summary,
        skills=skills_summary,
        interviews=interview_summary,
        coding=coding_summary,
        placement_readiness=placement_summary,
        recent_activity=activities,
    )
