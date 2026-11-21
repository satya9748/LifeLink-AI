from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.database import Base, engine
from app import models

from app.routers import (
    auth,
    donors,
    blood_banks,
    inventory,
    requests,
    hospitals,
    admin,
    blood_bank_responses,
    gmail
)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Blood availability and emergency donor coordination API"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(donors.router)
app.include_router(blood_banks.router)
app.include_router(inventory.router)
app.include_router(requests.router)
app.include_router(hospitals.router)
app.include_router(admin.router)
app.include_router(blood_bank_responses.router)
app.include_router(gmail.router)
@app.get("/health", tags=["System"])
def health():
    return {
        "status": "ok",
        "application": settings.app_name
    }
