
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models import Hospital, BloodRequest, BloodBank, BloodUnit
from app.schemas.dto import BloodRequestCreate, StatusUpdate
from app.routers.deps import require_roles


router = APIRouter(
    prefix="/api/requests",
    tags=["Hospital blood requests"]
)

VALID_STATUSES = {
    "open",
    "under_review",
    "partially_fulfilled",
    "fulfilled",
    "cancelled"
}

VALID_BLOOD_GROUPS = {
    "A+", "A-", "B+", "B-",
    "AB+", "AB-", "O+", "O-"
}


@router.post("", status_code=201)
def create_request(
    payload: BloodRequestCreate,
    user=Depends(require_roles("hospital")),
    db: Session = Depends(get_db)
):
    hospital = db.query(Hospital).filter(
        Hospital.user_id == user.id
    ).first()

    if not hospital:
        raise HTTPException(
            status_code=400,
            detail="Create a hospital profile first"
        )

    if payload.blood_group not in VALID_BLOOD_GROUPS:
        raise HTTPException(
            status_code=400,
            detail="Invalid blood group"
        )

    if payload.urgency not in {"normal", "urgent", "emergency"}:
        raise HTTPException(
            status_code=400,
            detail="Invalid urgency"
        )

    req = BloodRequest(
        hospital_id=hospital.id,
        **payload.model_dump()
    )

    db.add(req)
    db.commit()
    db.refresh(req)

    return {
        "id": req.id,
        "status": req.status,
        "message": "Blood request submitted"
    }


@router.get("")
def list_requests(
    user=Depends(require_roles("admin", "hospital", "blood_bank")),
    db: Session = Depends(get_db)
):
    q = db.query(BloodRequest)

    if user.role == "hospital":
        hospital = db.query(Hospital).filter(
            Hospital.user_id == user.id
        ).first()

        if not hospital:
            return []

        q = q.filter(BloodRequest.hospital_id == hospital.id)

    return [
        {
            "id": r.id,
            "hospital_id": r.hospital_id,
            "blood_group": r.blood_group,
            "component": r.component,
            "units_required": r.units_required,
            "urgency": r.urgency,
            "city": r.city,
            "status": r.status,
            "created_at": r.created_at.isoformat()
        }
        for r in q.order_by(
            BloodRequest.created_at.desc()
        ).limit(200).all()
    ]


@router.get("/{request_id}/matches")
def match_inventory(
    request_id: int,
    user=Depends(require_roles("admin", "hospital", "blood_bank")),
    db: Session = Depends(get_db)
):
    req = db.query(BloodRequest).filter(
        BloodRequest.id == request_id
    ).first()

    if not req:
        raise HTTPException(
            status_code=404,
            detail="Blood request not found"
        )

    # A hospital can only inspect its own request.
    if user.role == "hospital":
        hospital = db.query(Hospital).filter(
            Hospital.user_id == user.id
        ).first()

        if not hospital or req.hospital_id != hospital.id:
            raise HTTPException(
                status_code=403,
                detail="You cannot access this request"
            )

    # A blood bank must have a profile.
    if user.role == "blood_bank":
        bank = db.query(BloodBank).filter(
            BloodBank.user_id == user.id
        ).first()

        if not bank or not bank.verified:
            raise HTTPException(
                status_code=403,
                detail="Verified blood bank access required"
            )

    now = datetime.now(timezone.utc)

    query = (
        db.query(BloodUnit, BloodBank)
        .join(
            BloodBank,
            BloodUnit.blood_bank_id == BloodBank.id
        )
        .filter(
            BloodBank.verified.is_(True),
            BloodUnit.blood_group == req.blood_group,
            BloodUnit.component == req.component,
            BloodUnit.status == "available",
            BloodUnit.screening_status == "passed",
            BloodUnit.expiry_date > now
        )
    )

    # A blood bank can only view its own matching units.
    if user.role == "blood_bank":
        query = query.filter(
            BloodBank.user_id == user.id
        )

    # Prefer the requested city, but show other matching cities too.
    results = query.order_by(
    (BloodBank.city.ilike(req.city)).desc(),
    BloodUnit.expiry_date.asc()
).limit(500).all()

    matches = [
        {
            "unit_code": unit.unit_code,
            "blood_group": unit.blood_group,
            "component": unit.component,
            "quantity_ml": unit.quantity_ml,
            "blood_bank": bank.name,
            "city": bank.city,
            "expiry_date": unit.expiry_date.isoformat(),
            "location_match": (
                bank.city.casefold() == req.city.casefold()
            )
        }
        for unit, bank in results
    ]

    matching_units = len(matches)

    total_quantity_ml = sum(
        match["quantity_ml"] for match in matches
    )
    inventory_status = calculate_inventory_status(
    matching_units,
    req.units_required
)
    return {
        "request_id": req.id,
        "requested_blood_group": req.blood_group,
        "requested_component": req.component,
        "units_required": req.units_required,
        "matching_units": matching_units,
        "total_quantity_ml": total_quantity_ml,
        "inventory_status": inventory_status,
        "quantity_satisfied": matching_units >= req.units_required,
        "matches": matches,
        "message": (
            "Matching released inventory found."
            if matches
            else "No matching released inventory found."
        ),
        "clinical_notice": (
            "This is an inventory match only. "
            "Authorized professionals must confirm clinical suitability, "
            "compatibility, cross-match and release."
        )
    }
def calculate_inventory_status(matching_units: int, units_required: int):
    if matching_units == 0:
        return "unavailable"
    elif matching_units < units_required:
        return "partially_available"
    else:
        return "sufficient_inventory"
@router.patch("/{request_id}/status")
def update_status(
    request_id: int,
    payload: StatusUpdate,
    user=Depends(require_roles("admin", "blood_bank")),
    db: Session = Depends(get_db)
):
    if payload.status not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail="Invalid request status"
        )

    req = db.query(BloodRequest).filter(
        BloodRequest.id == request_id
    ).first()

    if not req:
        raise HTTPException(
            status_code=404,
            detail="Request not found"
        )

    if user.role == "blood_bank":
        bank = db.query(BloodBank).filter(
            BloodBank.user_id == user.id
        ).first()

        if not bank or not bank.verified:
            raise HTTPException(
                status_code=403,
                detail="Verified blood bank access required"
            )

    req.status = payload.status
    db.commit()

    return {
        "id": req.id,
        "status": req.status
    }
