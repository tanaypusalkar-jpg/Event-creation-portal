import pytest
from pydantic import ValidationError
from app.schemas import RegistrationCreate, EventCreate

def test_registration_validates_email_and_phone():
    with pytest.raises(ValidationError):
        RegistrationCreate(full_name="Test User", email="invalid", contact_number="123")
    value = RegistrationCreate(full_name="Test User", email="test@example.com", contact_number="+91 98765 43210")
    assert value.full_name == "Test User"

def test_event_rejects_negative_capacity():
    with pytest.raises(ValidationError):
        EventCreate(title="Security workshop", category="Technology", starts_at="2027-01-01T10:00:00Z",
            ends_at="2027-01-01T11:00:00Z", venue="Pune", capacity=-1)
