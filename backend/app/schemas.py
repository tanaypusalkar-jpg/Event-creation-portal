from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

Category = Literal["Technology", "Business", "Design", "Workshop"]
EventStatus = Literal["upcoming", "ongoing", "completed"]

class EventBase(BaseModel):
    title: str = Field(min_length=3, max_length=160)
    description: str = Field(default="", max_length=5000)
    category: Category
    image_url: str = Field(default="", max_length=1000)
    starts_at: datetime
    ends_at: datetime
    venue: str = Field(min_length=2, max_length=200)
    capacity: int = Field(ge=0, le=100000)
    status: EventStatus = "upcoming"

    @field_validator("title", "venue")
    @classmethod
    def trim_required(cls, value):
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be blank")
        return value

class EventCreate(EventBase):
    pass

class EventUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=160)
    description: str | None = Field(default=None, max_length=5000)
    category: Category | None = None
    image_url: str | None = Field(default=None, max_length=1000)
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    venue: str | None = Field(default=None, min_length=2, max_length=200)
    capacity: int | None = Field(default=None, ge=0, le=100000)
    status: EventStatus | None = None

class EventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    description: str
    category: str
    image_url: str
    starts_at: datetime
    ends_at: datetime
    venue: str
    capacity: int
    status: str
    registration_count: int = 0
    available_seats: int = 0

class RegistrationCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    contact_number: str = Field(min_length=7, max_length=24)

    @field_validator("full_name")
    @classmethod
    def valid_name(cls, value):
        value = " ".join(value.split())
        if not all(ch.isalpha() or ch in " -'." for ch in value):
            raise ValueError("Name contains unsupported characters")
        return value

    @field_validator("contact_number")
    @classmethod
    def valid_phone(cls, value):
        digits = "".join(ch for ch in value if ch.isdigit())
        if not 7 <= len(digits) <= 15 or any(ch not in "+- ()0123456789" for ch in value):
            raise ValueError("Enter a valid contact number")
        return value.strip()

class RegistrationOut(BaseModel):
    id: int
    event_id: int
    full_name: str
    email: EmailStr
    contact_number: str
    created_at: datetime

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=256)

class DashboardOut(BaseModel):
    total_events: int
    upcoming_events: int
    total_registrations: int
    completed_events: int
