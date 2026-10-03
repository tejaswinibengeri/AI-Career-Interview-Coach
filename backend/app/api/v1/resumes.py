"""
Resume API Router — upload, list, retrieve, version history, compare versions, download, and delete resumes.
"""

from typing import List
from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.resume import (
    ResumeResponse,
    ResumeVersionComparisonResponse,
    ResumeVersionHistoryResponse,
    ResumeVersionResponse,
)
from app.schemas.user import APIEnvelope
from app.services.resume_service import (
    compare_resume_versions,
    delete_user_resume,
    delete_resume_version,
    get_current_version,
    get_resume_file_for_download,
    get_resume_version_history,
    get_user_resume_by_id,
    get_user_resumes,
    upload_user_resume,
)

router = APIRouter(prefix="/resumes", tags=["Resumes"])


def format_resume_response(resume) -> ResumeResponse:
    """Format ORM Resume object into ResumeResponse schema with current version."""
    current_ver = get_current_version(resume)
    current_resp = ResumeVersionResponse.model_validate(current_ver) if current_ver else None
    version_resps = [ResumeVersionResponse.model_validate(v) for v in resume.versions]

    return ResumeResponse(
        id=resume.id,
        user_id=resume.user_id,
        title=resume.title,
        current_version=current_resp,
        versions=version_resps,
        created_at=resume.created_at,
        updated_at=resume.updated_at,
    )


@router.post(
    "",
    response_model=APIEnvelope[ResumeResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Upload a new resume or a new version of an existing resume",
)
async def upload_resume(
    file: UploadFile = File(...),
    resume_id: int | None = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[ResumeResponse]:
    """Upload a PDF or DOCX resume. Validates size, MIME type, format, and extracts text."""
    resume = await upload_user_resume(db, user=current_user, file=file, resume_id=resume_id)
    return APIEnvelope(
        status="success",
        message="Resume uploaded and processed successfully.",
        data=format_resume_response(resume),
    )


@router.get(
    "",
    response_model=APIEnvelope[List[ResumeResponse]],
    status_code=status.HTTP_200_OK,
    summary="List all resumes for current user",
)
async def list_resumes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[List[ResumeResponse]]:
    """Retrieve all uploaded resumes for the authenticated user."""
    resumes = await get_user_resumes(db, user_id=current_user.id)
    data = [format_resume_response(r) for r in resumes]
    return APIEnvelope(
        status="success",
        message="Resumes retrieved successfully.",
        data=data,
    )


@router.get(
    "/{id}",
    response_model=APIEnvelope[ResumeResponse],
    status_code=status.HTTP_200_OK,
    summary="Get resume details by ID",
)
async def get_resume(
    id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[ResumeResponse]:
    """Retrieve details, version history, and extracted text for a specific resume."""
    resume = await get_user_resume_by_id(db, user_id=current_user.id, resume_id=id)
    return APIEnvelope(
        status="success",
        message="Resume details retrieved successfully.",
        data=format_resume_response(resume),
    )


@router.get(
    "/{id}/history",
    response_model=APIEnvelope[ResumeVersionHistoryResponse],
    status_code=status.HTTP_200_OK,
    summary="Get detailed version history and score trajectory for a resume",
)
async def get_resume_history(
    id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[ResumeVersionHistoryResponse]:
    """Retrieve full version history, ATS score progression, and extracted metadata per version."""
    history = await get_resume_version_history(db, user_id=current_user.id, resume_id=id)
    return APIEnvelope(
        status="success",
        message="Resume version history retrieved successfully.",
        data=history,
    )


@router.get(
    "/{id}/compare",
    response_model=APIEnvelope[ResumeVersionComparisonResponse],
    status_code=status.HTTP_200_OK,
    summary="Compare two specific versions of a resume",
)
async def compare_versions(
    id: int,
    v1: int = Query(..., description="First version ID"),
    v2: int = Query(..., description="Second version ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[ResumeVersionComparisonResponse]:
    """Compare two versions for ATS score improvement (+/- delta), newly added skills, and resolved missing keywords."""
    comparison = await compare_resume_versions(
        db, user_id=current_user.id, resume_id=id, v1_id=v1, v2_id=v2
    )
    return APIEnvelope(
        status="success",
        message="Resume versions compared successfully.",
        data=comparison,
    )


@router.get(
    "/{id}/download",
    summary="Securely download a resume file version",
)
async def download_resume(
    id: int,
    version_id: int | None = Query(None, description="Optional specific version ID to download"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Download the original uploaded PDF/DOCX file for the specified resume version."""
    file_path, filename, mime_type = await get_resume_file_for_download(
        db, user_id=current_user.id, resume_id=id, version_id=version_id
    )

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=mime_type,
    )


@router.delete(
    "/{id}",
    response_model=APIEnvelope[None],
    status_code=status.HTTP_200_OK,
    summary="Delete a resume and all associated physical file versions",
)
async def delete_resume(
    id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[None]:
    """Delete resume record and remove disk files for all versions."""
    await delete_user_resume(db, user_id=current_user.id, resume_id=id)
    return APIEnvelope(
        status="success",
        message="Resume deleted successfully.",
        data=None,
    )


@router.delete(
    "/{id}/versions/{version_id}",
    response_model=APIEnvelope[None],
    status_code=status.HTTP_200_OK,
    summary="Delete a specific resume version",
)
async def delete_version(
    id: int,
    version_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[None]:
    """Delete a specific version of a resume and clean up physical file from storage disk."""
    await delete_resume_version(db, user_id=current_user.id, resume_id=id, version_id=version_id)
    return APIEnvelope(
        status="success",
        message="Resume version deleted successfully.",
        data=None,
    )
