from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models import BloodBank, BloodUnit
from app.schemas.dto import BloodUnitCreate, BloodScreeningUpdate
from app.routers.deps import require_roles

router = APIRouter(prefix="/api/inventory", tags=["Blood inventory"])

@router.post("", status_code=201)
def add_unit(payload: BloodUnitCreate, user=Depends(require_roles("blood_bank")), db: Session = Depends(get_db)):
    bank = db.query(BloodBank).filter(BloodBank.user_id == user.id).first()
    if not bank:
        raise HTTPException(status_code=400, detail="Create a blood bank profile first")
    if db.query(BloodUnit).filter(BloodUnit.unit_code == payload.unit_code).first():
        raise HTTPException(status_code=409, detail="Unit code already exists")
    if payload.expiry_date <= payload.collection_date:
        raise HTTPException(status_code=400, detail="Expiry date must be after collection date")
    unit = BloodUnit(blood_bank_id=bank.id, **payload.model_dump(), status="quarantined")
    db.add(unit); db.commit(); db.refresh(unit)
    return {"id": unit.id, "status": unit.status,
            "message": "Unit recorded; authorized blood-bank staff must verify screening and release status"}

@router.get("")
def get_inventory(city: str | None = None, blood_group: str | None = None, db: Session = Depends(get_db)):
    q = db.query(BloodUnit, BloodBank).join(BloodBank, BloodUnit.blood_bank_id == BloodBank.id)
    q = q.filter(BloodBank.verified == True, BloodUnit.status == "available",
                 BloodUnit.screening_status == "passed")
    if city: q = q.filter(BloodBank.city.ilike(f"%{city}%"))
    if blood_group: q = q.filter(BloodUnit.blood_group == blood_group)
    return [{"blood_bank": bank.name, "city": bank.city, "blood_group": unit.blood_group,
             "component": unit.component, "quantity_ml": unit.quantity_ml, "expiry_date": unit.expiry_date.isoformat(),
             "unit_code": unit.unit_code} for unit, bank in q.limit(200).all()]
@router.get("/my")
def get_my_inventory(
    user=Depends(require_roles("blood_bank")),
    db: Session = Depends(get_db)
):
    bank = db.query(BloodBank).filter(
        BloodBank.user_id == user.id
    ).first()

    if not bank:
        raise HTTPException(
            status_code=404,
            detail="Blood bank profile not found"
        )

    units = db.query(BloodUnit).filter(
        BloodUnit.blood_bank_id == bank.id
    ).order_by(BloodUnit.expiry_date.asc()).all()

    return [
        {
            "id": unit.id,
            "unit_code": unit.unit_code,
            "blood_group": unit.blood_group,
            "component": unit.component,

            "collection_date": unit.collection_date.isoformat(),
            "expiry_date": unit.expiry_date.isoformat(),
            "screening_status": unit.screening_status,
            "status": unit.status
        }
        for unit in units
    ]
@router.patch("/{unit_id}/screening")
def update_screening(
    unit_id: int,
    payload: BloodScreeningUpdate,
    user=Depends(require_roles("blood_bank")),
    db: Session = Depends(get_db)
):
    bank = db.query(BloodBank).filter(
        BloodBank.user_id == user.id
    ).first()

    if not bank:
        raise HTTPException(status_code=404, detail="Blood bank profile not found")

    unit = db.query(BloodUnit).filter(
        BloodUnit.id == unit_id,
        BloodUnit.blood_bank_id == bank.id
    ).first()

    if not unit:
        raise HTTPException(status_code=404, detail="Blood unit not found")

    if payload.screening_status not in ["passed", "failed"]:
        raise HTTPException(
            status_code=400,
            detail="Screening status must be passed or failed"
        )

    unit.screening_status = payload.screening_status

    if payload.screening_status == "failed":
        unit.status = "quarantined"
    else:
        unit.status = "quarantined"

    db.commit()
    db.refresh(unit)

    return {
        "id": unit.id,
        "screening_status": unit.screening_status,
        "status": unit.status,
        "message": "Screening result recorded. Unit remains quarantined until separately released."
    }
@router.patch("/{unit_id}/release")
def release_blood_unit(
    unit_id: int,
    user=Depends(require_roles("blood_bank")),
    db: Session = Depends(get_db)
):
    bank = db.query(BloodBank).filter(
        BloodBank.user_id == user.id
    ).first()

    if not bank:
        raise HTTPException(status_code=404, detail="Blood bank profile not found")

    unit = db.query(BloodUnit).filter(
        BloodUnit.id == unit_id,
        BloodUnit.blood_bank_id == bank.id
    ).first()

    if not unit:
        raise HTTPException(status_code=404, detail="Blood unit not found")

    if unit.screening_status != "passed":
        raise HTTPException(
            status_code=400,
            detail="Only blood units with passed screening can be released"
        )

    unit.status = "available"

    db.commit()
    db.refresh(unit)

    return {
        "id": unit.id,
        "screening_status": unit.screening_status,
        "status": unit.status,
        "message": "Blood unit successfully released for availability search"
    }
@router.get("/summary")
def get_inventory_summary(
    user=Depends(require_roles("blood_bank")),
    db: Session = Depends(get_db)
):
    bank = db.query(BloodBank).filter(
        BloodBank.user_id == user.id
    ).first()

    if not bank:
        raise HTTPException(status_code=404, detail="Blood bank profile not found")

    units = db.query(BloodUnit).filter(
        BloodUnit.blood_bank_id == bank.id
    )

    total = units.count()

    available = units.filter(
        BloodUnit.status == "available"
    ).count()

    quarantined = units.filter(
        BloodUnit.status == "quarantined"
    ).count()

    failed = units.filter(
        BloodUnit.screening_status == "failed"
    ).count()

    return {
        "total_units": total,
        "available_units": available,
        "quarantined_units": quarantined,
        "failed_screening_units": failed
    }