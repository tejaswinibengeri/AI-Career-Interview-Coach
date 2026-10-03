"""
Resume business logic — handles secure file uploads, versioning, retrieval, download, comparison, and version deletion.
"""

import os
import uuid
from pathlib import Path
from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AppException
from app.models.resume import Resume, ResumeVersion
from app.models.resume_analysis import ResumeAnalysis
from app.models.user import User
from app.schemas.resume import (
    ResumeVersionComparisonResponse,
    ResumeVersionHistoryItem,
    ResumeVersionHistoryResponse,
)
from app.services.resume_parser import process_and_extract_resume


def get_current_version(resume: Resume) -> ResumeVersion | None:
    """Helper to return current version of a resume."""
    for ver in resume.versions:
        if ver.is_current:
            return ver
    return resume.versions[0] if resume.versions else None


async def upload_user_resume(
    db: AsyncSession,
    user: User,
    file: UploadFile,
    resume_id: int | None = None,
) -> Resume:
    """Upload a PDF/DOCX file, extract text, store securely, and save metadata versioning."""
    filename = file.filename or "resume.pdf"
    content_type = file.content_type or "application/octet-stream"

    # Read uploaded bytes
    content = await file.read()

    # Validate file integrity, format, size, and extract text
    file_type, extracted_text = process_and_extract_resume(filename, content_type, content)

    # Determine user secure storage directory
    user_upload_dir = Path(settings.UPLOAD_DIR) / "resumes" / f"user_{user.id}"
    user_upload_dir.mkdir(parents=True, exist_ok=True)

    target_resume: Resume | None = None
    version_number = 1

    if resume_id is not None:
        # Uploading new version to existing resume
        query = select(Resume).where(Resume.id == resume_id, Resume.user_id == user.id)
        result = await db.execute(query)
        target_resume = result.scalar_one_or_none()

        if not target_resume:
            raise AppException(
                message="Resume record not found.",
                status_code=404,
            )

        # Mark all existing versions as not current
        for ver in target_resume.versions:
            ver.is_current = False

        version_number = max((ver.version_number for ver in target_resume.versions), default=0) + 1
    else:
        # Creating a brand new resume
        target_resume = Resume(
            user_id=user.id,
            title=filename,
        )
        db.add(target_resume)
        await db.flush()

    # Generate unique secure physical filename
    unique_filename = f"res_{target_resume.id}_v{version_number}_{uuid.uuid4().hex[:8]}.{file_type}"
    file_path = user_upload_dir / unique_filename

    # Write file securely to disk
    with open(file_path, "wb") as f:
        f.write(content)

    # Create new ResumeVersion entry
    new_version = ResumeVersion(
        resume_id=target_resume.id,
        version_number=version_number,
        filename=filename,
        file_path=str(file_path),
        file_size=len(content),
        file_type=file_type,
        mime_type=content_type,
        extracted_text=extracted_text,
        is_current=True,
    )
    db.add(new_version)

    await db.commit()
    await db.refresh(target_resume, attribute_names=["versions"])
    return target_resume


async def get_user_resumes(db: AsyncSession, user_id: int) -> list[Resume]:
    """Retrieve all resume entities for a given user."""
    query = select(Resume).where(Resume.user_id == user_id).order_by(Resume.updated_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_user_resume_by_id(db: AsyncSession, user_id: int, resume_id: int) -> Resume:
    """Retrieve a single resume entity for a user."""
    query = select(Resume).where(Resume.id == resume_id, Resume.user_id == user_id)
    result = await db.execute(query)
    resume = result.scalar_one_or_none()

    if not resume:
        raise AppException(
            message="Resume not found or access denied.",
            status_code=404,
        )
    return resume


async def get_resume_file_for_download(
    db: AsyncSession,
    user_id: int,
    resume_id: int,
    version_id: int | None = None,
) -> tuple[str, str, str]:
    """Get physical file path, original filename, and MIME type for secure download."""
    resume = await get_user_resume_by_id(db, user_id, resume_id)

    target_version: ResumeVersion | None = None
    if version_id is not None:
        for ver in resume.versions:
            if ver.id == version_id:
                target_version = ver
                break
        if not target_version:
            raise AppException(message="Resume version not found.", status_code=404)
    else:
        target_version = get_current_version(resume)

    if not target_version:
        raise AppException(message="No file version found for this resume.", status_code=404)

    if not os.path.exists(target_version.file_path):
        raise AppException(
            message="Resume file could not be found on storage disk.",
            status_code=404,
        )

    return target_version.file_path, target_version.filename, target_version.mime_type


async def delete_user_resume(db: AsyncSession, user_id: int, resume_id: int) -> None:
    """Delete a user's resume record and clean up associated disk files."""
    resume = await get_user_resume_by_id(db, user_id, resume_id)

    for ver in resume.versions:
        if os.path.exists(ver.file_path):
            try:
                os.remove(ver.file_path)
            except OSError:
                pass

    await db.delete(resume)
    await db.commit()


async def get_resume_version_history(
    db: AsyncSession, user_id: int, resume_id: int
) -> ResumeVersionHistoryResponse:
    """Retrieve detailed version history and real ATS score trajectory for a resume."""
    resume = await get_user_resume_by_id(db, user_id, resume_id)

    # Fetch all analyses for this resume
    an_query = select(ResumeAnalysis).where(
        ResumeAnalysis.resume_id == resume_id, ResumeAnalysis.user_id == user_id
    )
    an_res = await db.execute(an_query)
    analyses = an_res.scalars().all()
    analysis_map: dict[int, ResumeAnalysis] = {a.resume_version_id: a for a in analyses}

    # Sort versions by version_number desc
    sorted_versions = sorted(resume.versions, key=lambda v: v.version_number, reverse=True)

    items: list[ResumeVersionHistoryItem] = []
    evaluated_scores: list[tuple[int, float]] = []

    for ver in sorted_versions:
        an = analysis_map.get(ver.id)
        ats_score = round(an.ats_score, 1) if an else None
        extracted_skills = [s.skill_name for s in an.skills] if an and an.skills else []

        if ats_score is not None:
            evaluated_scores.append((ver.version_number, ats_score))

        items.append(
            ResumeVersionHistoryItem(
                id=ver.id,
                version_number=ver.version_number,
                filename=ver.filename,
                file_size=ver.file_size,
                file_type=ver.file_type,
                mime_type=ver.mime_type,
                is_current=ver.is_current,
                ats_score=ats_score,
                skills=extracted_skills,
                strengths=an.strengths if an else [],
                weaknesses=an.weaknesses if an else [],
                missing_keywords=an.missing_keywords if an else [],
                created_at=ver.created_at,
            )
        )

    # Calculate real score improvement (latest vs earliest evaluated version)
    score_improvement = None
    if len(evaluated_scores) >= 2:
        evaluated_scores.sort(key=lambda x: x[0])  # Sort by version_number asc
        earliest_score = evaluated_scores[0][1]
        latest_score = evaluated_scores[-1][1]
        score_improvement = round(latest_score - earliest_score, 1)

    return ResumeVersionHistoryResponse(
        resume_id=resume.id,
        title=resume.title,
        total_versions=len(sorted_versions),
        score_improvement=score_improvement,
        versions=items,
    )


async def compare_resume_versions(
    db: AsyncSession, user_id: int, resume_id: int, v1_id: int, v2_id: int
) -> ResumeVersionComparisonResponse:
    """Compare two specific versions of a resume for ATS score improvement, skills, and keyword fixes."""
    resume = await get_user_resume_by_id(db, user_id, resume_id)

    ver1 = next((v for v in resume.versions if v.id == v1_id), None)
    ver2 = next((v for v in resume.versions if v.id == v2_id), None)

    if not ver1 or not ver2:
        raise AppException(message="Specified resume version(s) not found.", status_code=404)

    # Fetch analyses
    an1_res = await db.execute(
        select(ResumeAnalysis).where(
            ResumeAnalysis.resume_version_id == v1_id, ResumeAnalysis.user_id == user_id
        )
    )
    an1 = an1_res.scalar_one_or_none()

    an2_res = await db.execute(
        select(ResumeAnalysis).where(
            ResumeAnalysis.resume_version_id == v2_id, ResumeAnalysis.user_id == user_id
        )
    )
    an2 = an2_res.scalar_one_or_none()

    v1_score = round(an1.ats_score, 1) if an1 else None
    v2_score = round(an2.ats_score, 1) if an2 else None

    score_delta = None
    if v1_score is not None and v2_score is not None:
        score_delta = round(v2_score - v1_score, 1)

    v1_skills = [s.skill_name for s in an1.skills] if an1 and an1.skills else []
    v2_skills = [s.skill_name for s in an2.skills] if an2 and an2.skills else []

    set1_skills = set(v1_skills)
    set2_skills = set(v2_skills)

    added_skills = list(set2_skills - set1_skills)
    removed_skills = list(set1_skills - set2_skills)

    v1_missing = an1.missing_keywords if an1 else []
    v2_missing = an2.missing_keywords if an2 else []

    set1_missing = set(v1_missing)
    set2_missing = set(v2_missing)

    resolved_missing = list(set1_missing - set2_missing)

    return ResumeVersionComparisonResponse(
        resume_id=resume.id,
        v1_version_id=ver1.id,
        v1_version_number=ver1.version_number,
        v1_filename=ver1.filename,
        v1_ats_score=v1_score,
        v1_skills=v1_skills,
        v2_version_id=ver2.id,
        v2_version_number=ver2.version_number,
        v2_filename=ver2.filename,
        v2_ats_score=v2_score,
        v2_skills=v2_skills,
        ats_score_delta=score_delta,
        added_skills=added_skills,
        removed_skills=removed_skills,
        resolved_missing_keywords=resolved_missing,
    )


async def delete_resume_version(
    db: AsyncSession, user_id: int, resume_id: int, version_id: int
) -> None:
    """Delete a specific version of a resume. Updates is_current if needed."""
    resume = await get_user_resume_by_id(db, user_id, resume_id)

    if len(resume.versions) <= 1:
        # If it's the only version, delete the whole resume entity
        await delete_user_resume(db, user_id, resume_id)
        return

    target_version = next((v for v in resume.versions if v.id == version_id), None)
    if not target_version:
        raise AppException(message="Resume version not found.", status_code=404)

    was_current = target_version.is_current

    # Clean up file from disk
    if os.path.exists(target_version.file_path):
        try:
            os.remove(target_version.file_path)
        except OSError:
            pass

    await db.delete(target_version)
    await db.flush()

    # If deleted version was current, set highest remaining version_number as current
    if was_current:
        rem_res = await db.execute(
            select(ResumeVersion)
            .where(ResumeVersion.resume_id == resume_id)
            .order_by(ResumeVersion.version_number.desc())
        )
        remaining_versions = rem_res.scalars().all()
        if remaining_versions:
            remaining_versions[0].is_current = True

    await db.commit()
    db.expire_all()



