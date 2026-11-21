from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models import BloodBank
from app.schemas.dto import BloodBankCreate
from app.routers.deps import require_roles

router = APIRouter(prefix="/api/blood-banks", tags=["Blood banks"])

@router.post("", status_code=201)
def create_blood_bank(payload: BloodBankCreate, user=Depends(require_roles("blood_bank")), db: Session = Depends(get_db)):
    if db.query(BloodBank).filter(BloodBank.user_id == user.id).first():
        raise HTTPException(status_code=409, detail="Blood bank profile already exists")
    bank = BloodBank(user_id=user.id, **payload.model_dump())
    db.add(bank); db.commit(); db.refresh(bank)
    return {"id": bank.id, "message": "Blood bank profile submitted for verification"}

@router.get("")
def list_blood_banks(city: str | None = None, db: Session = Depends(get_db)):
    q = db.query(BloodBank).filter(BloodBank.verified == True)
    if city: q = q.filter(BloodBank.city.ilike(f"%{city}%"))
    return [{"id": b.id, "name": b.name, "city": b.city, "state": b.state,
             "address": b.address, "phone": b.phone} for b in q.limit(100).all()]
@router.get("/me")
def get_my_blood_bank(
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

    return {
        "id": bank.id,
        "name": bank.name,
        "license_number": bank.license_number,
        "address": bank.address,
        "city": bank.city,
        "state": bank.state,
        "phone": bank.phone,
        "verified": bank.verified
    }