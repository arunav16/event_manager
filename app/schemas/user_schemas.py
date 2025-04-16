from builtins import any, bool, str
from pydantic import BaseModel, EmailStr, Field, HttpUrl, root_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum
import uuid
from app.schemas.pagination_schema import PaginationLink


from app.utils.nickname_gen import generate_nickname


class UserRole(str, Enum):
    ANONYMOUS = "ANONYMOUS"
    AUTHENTICATED = "AUTHENTICATED"
    MANAGER = "MANAGER"
    ADMIN = "ADMIN"


class UserBase(BaseModel):
    email: EmailStr = Field(..., example="john.doe@example.com")
    nickname: Optional[str] = Field(None, min_length=3, pattern=r'^[\w-]+$', example=generate_nickname())
    first_name: Optional[str] = Field(None, example="John")
    last_name: Optional[str] = Field(None, example="Doe")
    bio: Optional[str] = Field(None, example="Experienced software developer specializing in web applications.")
    profile_picture_url: Optional[HttpUrl] = Field(None, example="https://example.com/profiles/john.jpg")
    linkedin_profile_url: Optional[HttpUrl] = Field(None, example="https://linkedin.com/in/johndoe")
    github_profile_url: Optional[HttpUrl] = Field(None, example="https://github.com/johndoe")

    class Config:
        from_attributes = True

    @root_validator(pre=True)
    def convert_urls_to_str(cls, values):
        if isinstance(values, dict):  
            url_fields = ["profile_picture_url", "linkedin_profile_url", "github_profile_url"]
            for field in url_fields:
                if field in values and values[field] is not None:
                    values[field] = str(values[field])
        return values


class UserCreate(UserBase):
    password: str = Field(..., example="Secure*1234")


from pydantic import HttpUrl, field_serializer

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, example="John")
    last_name: Optional[str] = Field(None, example="Doe")
    nickname: Optional[str] = None
    profile_picture_url: Optional[HttpUrl] = None
    linkedin_profile_url: Optional[HttpUrl] = None
    github_profile_url: Optional[HttpUrl] = None

    @field_serializer("profile_picture_url", "linkedin_profile_url", "github_profile_url", when_used="json")
    def serialize_urls(self, v):
        return str(v) if v else None

    @root_validator(pre=True)
    def check_at_least_one(cls, values):
        if not any(values.values()):
            raise ValueError("At least one field must be provided")
        return values



class UserResponse(UserBase):
    id: uuid.UUID = Field(..., example=uuid.uuid4())
    role: UserRole = Field(default=UserRole.AUTHENTICATED, example="AUTHENTICATED")
    last_login_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    links: Optional[List[dict]] = []


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., example="john.doe@example.com")
    password: str = Field(..., example="Secure*1234")


class ErrorResponse(BaseModel):
    error: str = Field(..., example="Not Found")
    details: Optional[str] = Field(None, example="The requested resource was not found.")


class UserListResponse(BaseModel):
    items: List[UserResponse] = Field(...)
    total: int = Field(..., example=100)
    page: int = Field(..., example=1)
    size: int = Field(..., example=10)
    links: Optional[List[PaginationLink]]
