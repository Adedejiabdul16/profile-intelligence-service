from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ClassifyData(BaseModel):
    name: str
    gender: str
    probability: float
    sample_size: int
    is_confident: bool
    processed_at: datetime


class ClassifyResponse(BaseModel):
    status: str
    data: ClassifyData


class ProfileCreateRequest(BaseModel):
    name: str


class ProfileData(BaseModel):
    id: str
    name: str
    gender: str
    gender_probability: float
    sample_size: int
    age: int
    age_group: str
    country_id: str
    country_name: str
    country_probability: float
    created_at: datetime


class ProfileResponse(BaseModel):
    status: str
    data: ProfileData


class ProfileListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    gender: str
    gender_probability: float
    age: int
    age_group: str
    country_id: str
    country_name: str
    country_probability: float
    created_at: datetime


class ProfileListResponse(BaseModel):
    status: str
    page: int
    limit: int
    total: int
    data: list[ProfileListItem]