
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models import Donor
from app.schemas.dto import DonorCreate,  DonorPreferencesUpdate
from app.routers.deps import require_roles

router = APIRouter(prefix="/api/donors", tags=["Donors"])

GROUPS = {"A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"}


@router.post("", status_code=201)
def create_donor(
    payload: DonorCreate,
    user=Depends(require_roles("donor")),
    db: Session = Depends(get_db)
):
    if payload.blood_group not in GROUPS:
        raise HTTPException(status_code=400, detail="Invalid blood group")

    if db.query(Donor).filter(Donor.user_id == user.id).first():
        raise HTTPException(status_code=409, detail="Donor profile already exists")

    donor = Donor(user_id=user.id, **payload.model_dump())
    db.add(donor)
    db.commit()
    db.refresh(donor)

    return {"id": donor.id, "message": "Donor profile created"}


@router.get("")
def list_donors(
    city: str | None = None,
    blood_group: str | None = None,
    user=Depends(require_roles("admin", "hospital", "blood_bank")),
    db: Session = Depends(get_db)
):
    q = db.query(Donor).filter(
        Donor.consent_to_alerts == True,
        Donor.available_for_contact == True
    )

    if city:
        q = q.filter(Donor.city.ilike(f"%{city}%"))

    if blood_group:
        q = q.filter(Donor.blood_group == blood_group)

    return [
        {
            "id": d.id,
            "blood_group": d.blood_group,
            "city": d.city,
            "state": d.state,
            "available_for_contact": d.available_for_contact
        }
        for d in q.limit(100).all()
    ]


@router.get("/me")
def get_my_donor_profile(
    user=Depends(require_roles("donor")),
    db: Session = Depends(get_db)
):
    donor = db.query(Donor).filter(
        Donor.user_id == user.id
    ).first()

    if not donor:
        raise HTTPException(
            status_code=404,
            detail="Donor profile not found"
        )

    return {
        "id": donor.id,
        "blood_group": donor.blood_group,
        "city": donor.city,
        "state": donor.state,
        "phone": donor.phone,
        "consent_to_alerts": donor.consent_to_alerts,
        "available_for_contact": donor.available_for_contact
    }
@router.patch("/me/preferences")
def update_my_donor_preferences(
    payload: DonorPreferencesUpdate,
    user=Depends(require_roles("donor")),
    db: Session = Depends(get_db)
):
    donor = db.query(Donor).filter(
        Donor.user_id == user.id
    ).first()

    if not donor:
        raise HTTPException(
            status_code=404,
            detail="Donor profile not found"
        )

    donor.consent_to_alerts = payload.consent_to_alerts
    donor.available_for_contact = payload.available_for_contact

    db.commit()
    db.refresh(donor)

    return {
        "message": "Donor preferences updated successfully",
        "consent_to_alerts": donor.consent_to_alerts,
        "available_for_contact": donor.available_for_contact
    }