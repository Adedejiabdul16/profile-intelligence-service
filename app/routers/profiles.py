from datetime import timezone

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Response,
    status,
)
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import Profile, generate_uuid7
from ..profile_service import enrich_profile
from ..query_parser import (
    QueryInterpretationError,
    parse_natural_language,
)
from ..schemas import (
    ProfileCreateRequest,
    ProfileData,
    ProfileListItem,
    ProfileListResponse,
    ProfileResponse,
)


router = APIRouter(
    prefix="/api/profiles",
    tags=["Profiles"],
)


def profile_to_dict(profile: Profile) -> dict:
    created_at = profile.created_at

    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)

    return {
        "id": profile.id,
        "name": profile.name,
        "gender": profile.gender,
        "gender_probability": profile.gender_probability,
        "sample_size": profile.sample_size,
        "age": profile.age,
        "age_group": profile.age_group,
        "country_id": profile.country_id,
        "country_name": profile.country_name,
        "country_probability": profile.country_probability,
        "created_at": created_at,
    }


def error_response(message: str) -> dict:
    return {
        "status": "error",
        "message": message,
    }


def build_filtered_statement(
    *,
    gender: str | None = None,
    age_group: str | None = None,
    country_id: str | None = None,
    min_age: int | None = None,
    max_age: int | None = None,
    min_gender_probability: float | None = None,
    min_country_probability: float | None = None,
):
    """Build a database query from all supplied filters."""

    statement = select(Profile)

    if gender is not None:
        gender = gender.strip().lower()

        if gender not in {"male", "female"}:
            raise HTTPException(
                status_code=400,
                detail="Invalid query parameters",
            )

        statement = statement.where(
            func.lower(Profile.gender) == gender
        )

    if age_group is not None:
        age_group = age_group.strip().lower()

        if age_group not in {
            "child", "teenager", "adult", "senior"
        }:
            raise HTTPException(
                status_code=400,
                detail="Invalid query parameters",
            )

        statement = statement.where(
            func.lower(Profile.age_group) == age_group
        )

    if country_id is not None:
        country_id = country_id.strip().upper()

        if len(country_id) != 2:
            raise HTTPException(
                status_code=400,
                detail="Invalid query parameters",
            )

        statement = statement.where(
            func.upper(Profile.country_id) == country_id
        )

    if min_age is not None:
        statement = statement.where(Profile.age >= min_age)

    if max_age is not None:
        statement = statement.where(Profile.age <= max_age)

    if min_age is not None and max_age is not None:
        if min_age > max_age:
            raise HTTPException(
                status_code=400,
                detail="Invalid query parameters",
            )

    if min_gender_probability is not None:
        statement = statement.where(
            Profile.gender_probability >= min_gender_probability
        )

    if min_country_probability is not None:
        statement = statement.where(
            Profile.country_probability >= min_country_probability
        )

    return statement


async def get_paginated_profiles(
    db: AsyncSession,
    statement,
    page: int,
    limit: int,
    sort_by: str = "created_at",
    order: str = "desc",
) -> dict:
    """Count, sort, and paginate in the database."""

    count_statement = select(func.count()).select_from(
        statement.order_by(None).subquery()
    )

    total = await db.scalar(count_statement)
    total = total or 0

    sort_columns = {
        "age": Profile.age,
        "created_at": Profile.created_at,
        "gender_probability": Profile.gender_probability,
    }

    if sort_by not in sort_columns:
        raise HTTPException(
            status_code=400,
            detail="Invalid query parameters",
        )

    if order not in {"asc", "desc"}:
        raise HTTPException(
            status_code=400,
            detail="Invalid query parameters",
        )

    sort_column = sort_columns[sort_by]

    if order == "asc":
        statement = statement.order_by(sort_column.asc())
    else:
        statement = statement.order_by(sort_column.desc())

    statement = statement.order_by(Profile.id.asc())

    offset = (page - 1) * limit

    statement = statement.offset(offset).limit(limit)

    result = await db.scalars(statement)
    profiles = result.all()

    return {
        "status": "success",
        "page": page,
        "limit": limit,
        "total": total,
        "data": [
            {
                "id": profile.id,
                "name": profile.name,
                "gender": profile.gender,
                "gender_probability": profile.gender_probability,
                "age": profile.age,
                "age_group": profile.age_group,
                "country_id": profile.country_id,
                "country_name": profile.country_name,
                "country_probability": profile.country_probability,
                "created_at": (
                    profile.created_at.replace(tzinfo=timezone.utc)
                    if profile.created_at.tzinfo is None
                    else profile.created_at
                ),
            }
            for profile in profiles
        ],
    }


@router.post("")
async def create_profile(
    payload: ProfileCreateRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    name = payload.name.strip().lower()

    if not name:
        raise HTTPException(
            status_code=400,
            detail="Name is required",
        )

    existing = await db.scalar(
        select(Profile).where(Profile.name == name)
    )

    if existing:
        return {
            "status": "success",
            "message": "Profile already exists",
            "data": profile_to_dict(existing),
        }

    enriched_data = await enrich_profile(name)

    profile = Profile(
        id=generate_uuid7(),
        name=name,
        **enriched_data,
    )

    db.add(profile)

    try:
        await db.commit()
        await db.refresh(profile)

    except IntegrityError:
        await db.rollback()

        existing = await db.scalar(
            select(Profile).where(Profile.name == name)
        )

        if existing:
            return {
                "status": "success",
                "message": "Profile already exists",
                "data": profile_to_dict(existing),
            }

        raise HTTPException(
            status_code=500,
            detail="Unable to save profile",
        )

    response.status_code = status.HTTP_201_CREATED

    return {
        "status": "success",
        "data": profile_to_dict(profile),
    }


@router.get("/search")
async def search_profiles(
    q: str = Query(..., min_length=1),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=50),
    sort_by: str = Query(
        default="created_at",
        pattern="^(age|created_at|gender_probability)$",
    ),
    order: str = Query(
        default="desc",
        pattern="^(asc|desc)$",
    ),
    db: AsyncSession = Depends(get_db),
):
    try:
        filters = parse_natural_language(q)

    except QueryInterpretationError:
        return Response(
            content=(
                '{"status":"error",'
                '"message":"Unable to interpret query"}'
            ),
            status_code=400,
            media_type="application/json",
        )

    statement = build_filtered_statement(**filters)

    return await get_paginated_profiles(
        db=db,
        statement=statement,
        page=page,
        limit=limit,
        sort_by=sort_by,
        order=order,
    )


@router.get("", response_model=ProfileListResponse)
async def list_profiles(
    gender: str | None = None,
    age_group: str | None = None,
    country_id: str | None = None,
    min_age: int | None = Query(default=None, ge=0),
    max_age: int | None = Query(default=None, ge=0),
    min_gender_probability: float | None = Query(
        default=None, ge=0, le=1
    ),
    min_country_probability: float | None = Query(
        default=None, ge=0, le=1
    ),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=50),
    sort_by: str = Query(
        default="created_at",
        pattern="^(age|created_at|gender_probability)$",
    ),
    order: str = Query(
        default="desc",
        pattern="^(asc|desc)$",
    ),
    db: AsyncSession = Depends(get_db),
):
    statement = build_filtered_statement(
        gender=gender,
        age_group=age_group,
        country_id=country_id,
        min_age=min_age,
        max_age=max_age,
        min_gender_probability=min_gender_probability,
        min_country_probability=min_country_probability,
    )

    return await get_paginated_profiles(
        db=db,
        statement=statement,
        page=page,
        limit=limit,
        sort_by=sort_by,
        order=order,
    )


@router.get("/{profile_id}", response_model=ProfileResponse)
async def get_profile(
    profile_id: str,
    db: AsyncSession = Depends(get_db),
):
    profile = await db.get(Profile, profile_id)

    if profile is None:
        raise HTTPException(
            status_code=404,
            detail="Profile not found",
        )

    return {
        "status": "success",
        "data": profile_to_dict(profile),
    }


@router.delete(
    "/{profile_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_profile(
    profile_id: str,
    db: AsyncSession = Depends(get_db),
):
    profile = await db.get(Profile, profile_id)

    if profile is None:
        raise HTTPException(
            status_code=404,
            detail="Profile not found",
        )

    await db.delete(profile)
    await db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)