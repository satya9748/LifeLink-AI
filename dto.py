
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class RegisterIn(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    role: str


class UserOut(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: str
    is_verified: bool

    model_config = ConfigDict(from_attributes=True)


class DonorCreate(BaseModel):
    blood_group: str
    city: str
    state: str
    phone: str
    consent_to_alerts: bool = False
    available_for_contact: bool = False
class DonorPreferencesUpdate(BaseModel):
    consent_to_alerts: bool
    available_for_contact: bool


class BloodBankCreate(BaseModel):
    name: str
    license_number: str
    address: str
    city: str
    state: str
    phone: str


class BloodUnitCreate(BaseModel):
    unit_code: str
    blood_group: str
    component: str
    quantity_ml: int = Field(default=450, gt=0)
    collection_date: datetime
    expiry_date: datetime
    screening_status: str = "pending"

class BloodRequestCreate(BaseModel):
    blood_group: str
    component: str
    units_required: int = Field(gt=0, le=20)
    urgency: str = "normal"
    city: str
    clinical_reference: str | None = None


class StatusUpdate(BaseModel):
    status: str


class HospitalCreate(BaseModel):
    name: str
    address: str
    city: str
    state: str
    phone: str
class BloodScreeningUpdate(BaseModel):
    screening_status: str
class BloodBankResponseCreate(BaseModel):
    request_id: int = Field(gt=0)
    response_status: str
    units_offered: int = Field(default=0, ge=0)
    response_message: str | None = None