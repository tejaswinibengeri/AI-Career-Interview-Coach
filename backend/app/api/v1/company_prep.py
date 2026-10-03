"""
Company-Specific Preparation API Router (Module 13).
"""

from typing import List
from fastapi import APIRouter, Body, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.company_prep import CompanyPrepResponse, GenerateCompanyPrepRequest
from app.schemas.user import APIEnvelope
from app.services.company_prep_service import (
    generate_company_prep_plan,
    get_company_prep_plan_by_id,
    list_user_company_plans,
)

router = APIRouter(prefix="/company-prep", tags=["Company-Specific Interview Preparation"])


@router.post(
    "",
    response_model=APIEnvelope[CompanyPrepResponse],
    status_code=status.HTTP_200_OK,
    summary="Generate company-specific preparation plan",
)
async def create_company_prep(
    body: GenerateCompanyPrepRequest = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[CompanyPrepResponse]:
    """Generate interview preparation plan for a specific company and target role."""
    plan = await generate_company_prep_plan(db, user=current_user, request=body)
    return APIEnvelope(
        status="success",
        message="Company-specific preparation plan generated successfully.",
        data=plan,
    )


@router.get(
    "",
    response_model=APIEnvelope[List[CompanyPrepResponse]],
    status_code=status.HTTP_200_OK,
    summary="List saved company prep plans",
)
async def get_company_prep_plans(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[List[CompanyPrepResponse]]:
    """Retrieve saved company interview preparation plans for the user."""
    plans = await list_user_company_plans(db, user=current_user)
    return APIEnvelope(
        status="success",
        message="Saved company preparation plans retrieved.",
        data=plans,
    )


@router.get(
    "/{id}",
    response_model=APIEnvelope[CompanyPrepResponse],
    status_code=status.HTTP_200_OK,
    summary="Get company prep plan detail",
)
async def get_company_prep_detail(
    id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[CompanyPrepResponse]:
    """Retrieve details for a specific company prep plan by ID."""
    plan = await get_company_prep_plan_by_id(db, user=current_user, plan_id=id)
    return APIEnvelope(
        status="success",
        message="Company preparation plan detail retrieved.",
        data=plan,
    )
