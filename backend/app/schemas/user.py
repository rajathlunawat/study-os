"""
StudyOS Schemas — User.

Responsibility: Defines the Pydantic models (schemas) for the User entity.
These are used for request validation and response serialization in FastAPI routers.
No database or business logic is present here.
"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ── Shared Properties ─────────────────────────────────────────────────────────

class UserBase(BaseModel):
    """
    Shared properties that are common across user creation, updates, and responses.
    """
    name: str = Field(..., max_length=255, description="The user's full or display name.")
    email: EmailStr | None = Field(None, description="Optional email address for the user.")


# ── Create Model ──────────────────────────────────────────────────────────────

class UserCreate(UserBase):
    """
    Properties required to create a new user via API request.
    Inherits name and email from UserBase.
    """
    pass


# ── Update Model ──────────────────────────────────────────────────────────────

class UserUpdate(BaseModel):
    """
    Properties that can be updated for a user.
    All fields are optional because updates can be partial.
    """
    name: str | None = Field(None, max_length=255)
    email: EmailStr | None = Field(None)


# ── Response Model ────────────────────────────────────────────────────────────

class UserResponse(UserBase):
    """
    Properties returned to the client when a user is fetched.
    Includes database-generated fields like id and created_at.
    """
    id: int = Field(..., description="Unique internal database ID.")
    created_at: datetime = Field(..., description="UTC timestamp of account creation.")

    # Allows Pydantic to read data directly from the SQLAlchemy ORM model
    model_config = ConfigDict(from_attributes=True)
