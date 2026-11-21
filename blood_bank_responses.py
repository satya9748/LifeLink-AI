
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models import (
    Hospital,
    BloodBank,
    BloodRequest,
    BloodUnit,
    BloodBankResponse
)
from app.schemas.dto import BloodBankResponseCreate
from app.routers.deps import require_roles

router = APIRouter(
    prefix="/api/blood-bank-responses",
    tags=["Blood Bank Responses"]
)


@router.get("/available-requests")
def available_requests(
    user=Depends(require_roles("blood_bank")),
    db: Session = Depends(get_db)
):
    bank = db.query(BloodBank).filter(
        BloodBank.user_id == user.id,
        BloodBank.verified == True
    ).first()

    if not bank:
        raise HTTPException(
            status_code=403,
            detail="Verified blood bank profile required"
        )

    requests = db.query(BloodRequest).filter(
        BloodRequest.status == "open",
        BloodRequest.city.ilike(bank.city)
    ).all()

    return [
        {
            "request_id": req.id,
            "blood_group": req.blood_group,
            "component": req.component,
            "units_required": req.units_required,
            "urgency": req.urgency,
            "city": req.city,
            "created_at": req.created_at.isoformat()
        }
        for req in requests
    ]


@router.post("/")
def submit_response(
    data: BloodBankResponseCreate,
    user=Depends(require_roles("blood_bank")),
    db: Session = Depends(get_db)
):
    bank = db.query(BloodBank).filter(
        BloodBank.user_id == user.id,
        BloodBank.verified == True
    ).first()

    if not bank:
        raise HTTPException(
            status_code=403,
            detail="Verified blood bank profile required"
        )

    req = db.query(BloodRequest).filter(
        BloodRequest.id == data.request_id
    ).first()

    if not req or req.status != "open":
        raise HTTPException(
            status_code=404,
            detail="Open blood request not found"
        )

    if data.response_status not in ["accepted", "declined"]:
        raise HTTPException(
            status_code=400,
            detail="Response must be accepted or declined"
        )

    if data.response_status == "declined" and data.units_offered != 0:
        raise HTTPException(
            status_code=400,
            detail="Declined response must offer zero units"
        )

    if data.response_status == "accepted":
        if data.units_offered < 1 or data.units_offered > req.units_required:
            raise HTTPException(
                status_code=400,
                detail="Invalid number of units offered"
            )

        available_units = db.query(BloodUnit).filter(
            BloodUnit.blood_bank_id == bank.id,
            BloodUnit.blood_group == req.blood_group,
            BloodUnit.component == req.component,
            BloodUnit.status == "available",
            BloodUnit.screening_status == "passed",
            BloodUnit.expiry_date > datetime.utcnow()
        ).count()

        if data.units_offered > available_units:
            raise HTTPException(
                status_code=400,
                detail=f"Only {available_units} eligible inventory units found"
            )

    existing = db.query(BloodBankResponse).filter(
        BloodBankResponse.request_id == req.id,
        BloodBankResponse.blood_bank_id == bank.id
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail="This blood bank has already responded"
        )

    response = BloodBankResponse(
        request_id=req.id,
        blood_bank_id=bank.id,
        response_status=data.response_status,
        units_offered=data.units_offered,
        response_message=data.response_message,
        responded_at=datetime.utcnow()
    )

    db.add(response)
    db.commit()
    db.refresh(response)

    return {
        "message": "Blood bank response submitted successfully",
        "response_id": response.id,
        "request_id": response.request_id,
        "response_status": response.response_status,
        "units_offered": response.units_offered,
        "note": "This is an offer only. It does not reserve or issue blood units."
    }


@router.get("/my-responses")
def my_responses(
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

    responses = db.query(BloodBankResponse).filter(
        BloodBankResponse.blood_bank_id == bank.id
    ).order_by(
        BloodBankResponse.created_at.desc()
    ).all()

    return [
        {
            "response_id": item.id,
            "request_id": item.request_id,
            "response_status": item.response_status,
            "units_offered": item.units_offered,
            "response_message": item.response_message,
            "responded_at": (
                item.responded_at.isoformat()
                if item.responded_at else None
            )
        }
        for item in responses
    ]

@router.get("/hospital/{request_id}")
def hospital_responses(
    request_id: int,
    user=Depends(require_roles("hospital", "admin")),
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

    if user.role == "hospital":
        hospital = db.query(Hospital).filter(
            Hospital.user_id == user.id
        ).first()

        if not hospital or req.hospital_id != hospital.id:
            raise HTTPException(
                status_code=403,
                detail="You cannot view another hospital's request"
            )

    responses = db.query(
    BloodBankResponse,
    BloodBank
).join(
    BloodBank,
    BloodBankResponse.blood_bank_id == BloodBank.id
).filter(
    BloodBankResponse.request_id == request_id
).order_by(
    BloodBankResponse.created_at.desc()
).all()

    return {
        "request_id": request_id,
        "total_responses": len(responses),
        "responses": [
            {
                "response_id": item.id,
                "blood_bank_id": item.blood_bank_id,
                "blood_bank_name": bank.name,
                "response_status": item.response_status,
                "units_offered": item.units_offered,
                "response_message": item.response_message,
                "responded_at": (
                    item.responded_at.isoformat()
                    if item.responded_at else None
                )
            }
            for item, bank in responses
        ]
    }

