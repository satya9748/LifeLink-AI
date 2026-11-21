
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models import Hospital
from app.schemas.dto import HospitalCreate
from app.routers.deps import require_roles

router = APIRouter(prefix="/api/hospitals", tags=["Hospitals"])


@router.post("", status_code=201)
def create_hospital(
    payload: HospitalCreate,
    user=Depends(require_roles("hospital")),
    db: Session = Depends(get_db)
):
    existing = db.query(Hospital).filter(
        Hospital.user_id == user.id
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Hospital profile already exists"
        )

    hospital = Hospital(
        user_id=user.id,
        **payload.model_dump()
    )

    db.add(hospital)
    db.commit()
    db.refresh(hospital)

    return {
        "id": hospital.id,
        "message": "Hospital profile created successfully"
    }


@router.get("/me")
def get_my_hospital(
    user=Depends(require_roles("hospital")),
    db: Session = Depends(get_db)
):
    hospital = db.query(Hospital).filter(
        Hospital.user_id == user.id
    ).first()

    if not hospital:
        raise HTTPException(
            status_code=404,
            detail="Hospital profile not found"
        )

    return {
        "id": hospital.id,
        "name": hospital.name,
        "address": hospital.address,
        "city": hospital.city,
        "state": hospital.state,
        "phone": hospital.phone
    }
