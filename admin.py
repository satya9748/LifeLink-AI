from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models import User, BloodBank, Hospital, Donor, BloodRequest
from app.routers.deps import require_roles

router = APIRouter(
    prefix="/api/admin",
    tags=["Admin"]
)


@router.get("/blood-banks")
def get_blood_banks(
    admin=Depends(require_roles("admin")),
    db: Session = Depends(get_db)
):
    banks = (
        db.query(BloodBank, User)
        .join(User, BloodBank.user_id == User.id)
        .order_by(BloodBank.id.desc())
        .all()
    )

    return [
        {
            "id": bank.id,
            "user_id": user.id,
            "name": bank.name,
            "license_number": bank.license_number,
            "address": bank.address,
            "city": bank.city,
            "state": bank.state,
            "phone": bank.phone,
            "email": user.email,
            "verified": bank.verified
        }
        for bank, user in banks
    ]


@router.patch("/blood-banks/{bank_id}/verification")
def update_blood_bank_verification(
    bank_id: int,
    verified: bool = Body(..., embed=True),
    admin=Depends(require_roles("admin")),
    db: Session = Depends(get_db)
):
    bank = db.query(BloodBank).filter(
        BloodBank.id == bank_id
    ).first()

    if not bank:
        raise HTTPException(
            status_code=404,
            detail="Blood bank not found"
        )

    bank.verified = verified
    db.commit()
    db.refresh(bank)

    return {
        "message": "Blood bank verified successfully" if verified
        else "Blood bank verification rejected",
        "bank_id": bank.id,
        "verified": bank.verified
    }
# ==============================
# HOSPITAL MANAGEMENT
# ==============================

@router.get("/hospitals")
def get_hospitals(
    admin=Depends(require_roles("admin")),
    db: Session = Depends(get_db)
):
    hospitals = (
        db.query(Hospital, User)
        .join(User, Hospital.user_id == User.id)
        .order_by(Hospital.id.desc())
        .all()
    )

    return [
        {
            "id": hospital.id,
            "user_id": user.id,
            "name": hospital.name,
            "address": hospital.address,
            "city": hospital.city,
            "state": hospital.state,
            "phone": hospital.phone,
            "email": user.email,
            "is_active": user.is_active,
            "is_verified": user.is_verified
        }
        for hospital, user in hospitals
    ]


@router.patch("/hospitals/{hospital_id}/status")
def update_hospital_status(
    hospital_id: int,
    is_active: bool = Body(..., embed=True),
    admin=Depends(require_roles("admin")),
    db: Session = Depends(get_db)
):
    hospital = db.query(Hospital).filter(
        Hospital.id == hospital_id
    ).first()

    if not hospital:
        raise HTTPException(
            status_code=404,
            detail="Hospital not found"
        )

    user = db.query(User).filter(
        User.id == hospital.user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Hospital user not found"
        )

    user.is_active = is_active

    db.commit()
    db.refresh(user)

    return {
        "message": "Hospital account activated successfully"
        if is_active else "Hospital account deactivated successfully",
        "hospital_id": hospital.id,
        "is_active": user.is_active
    }
# ==============================
# DONOR MANAGEMENT
# ==============================

@router.get("/donors")
def get_donors(
    admin=Depends(require_roles("admin")),
    db: Session = Depends(get_db)
):
    donors = (
        db.query(Donor, User)
        .join(User, Donor.user_id == User.id)
        .order_by(Donor.id.desc())
        .all()
    )

    return [
        {
            "id": donor.id,
            "user_id": user.id,
            "name": user.full_name,
            "email": user.email,
            "blood_group": donor.blood_group,
            "city": donor.city,
            "phone": donor.phone,
            "is_active": user.is_active,
            "consent_to_alerts": donor.consent_to_alerts,
            "available_for_contact": donor.available_for_contact
        }
        for donor, user in donors
    ]


@router.patch("/donors/{donor_id}/status")
def update_donor_status(
    donor_id: int,
    is_active: bool = Body(..., embed=True),
    admin=Depends(require_roles("admin")),
    db: Session = Depends(get_db)
):
    donor = db.query(Donor).filter(
        Donor.id == donor_id
    ).first()

    if not donor:
        raise HTTPException(
            status_code=404,
            detail="Donor not found"
        )

    user = db.query(User).filter(
        User.id == donor.user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Donor user not found"
        )

    user.is_active = is_active

    db.commit()
    db.refresh(user)

    return {
        "message": "Donor account status updated successfully",
        "donor_id": donor.id,
        "is_active": user.is_active
    }
# ==============================
# BLOOD REQUEST MONITORING
# ==============================

@router.get("/blood-requests")
def get_all_blood_requests(
    admin=Depends(require_roles("admin")),
    db: Session = Depends(get_db)
):
    requests = (
        db.query(BloodRequest, Hospital)
        .join(Hospital, BloodRequest.hospital_id == Hospital.id)
        .order_by(BloodRequest.id.desc())
        .all()
    )

    return [
        {
            "id": request.id,
            "hospital_name": hospital.name,
            "blood_group": request.blood_group,
            "component": request.component,
            "units_required": request.units_required,
            "urgency": request.urgency,
            "city": request.city,
            "status": request.status,
            "created_at": request.created_at
        }
        for request, hospital in requests
    ]