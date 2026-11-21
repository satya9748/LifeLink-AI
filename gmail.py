import os
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from jose import jwt, JWTError
from cryptography.fernet import Fernet, InvalidToken

from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleRequest

from app.core.config import settings
from app.db.database import get_db
from app.models import GmailConnection
from app.routers.deps import current_user


router = APIRouter(
    prefix="/api/gmail",
    tags=["Gmail Integration"]
)


# Gmail permissions
GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.compose"
]


# Google OAuth configuration
def get_google_config():
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(
            status_code=500,
            detail="Google OAuth credentials are not configured"
        )

    return {
        "web": {
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [settings.google_redirect_uri]
        }
    }


# Encrypt Gmail refresh tokens
def encrypt_token(token: str) -> str:
    if not settings.gmail_token_encryption_key:
        raise HTTPException(
            status_code=500,
            detail="Gmail encryption key is missing"
        )

    cipher = Fernet(
        settings.gmail_token_encryption_key.encode()
    )

    return cipher.encrypt(token.encode()).decode()


# Decrypt Gmail refresh tokens
def decrypt_token(token: str) -> str:
    cipher = Fernet(
        settings.gmail_token_encryption_key.encode()
    )

    return cipher.decrypt(token.encode()).decode()

def get_gmail_service(user_id: int, db: Session):
    connection = db.query(GmailConnection).filter(
        GmailConnection.user_id == user_id
    ).first()

    if not connection:
        raise HTTPException(
            status_code=404,
            detail="Gmail account is not connected"
        )

    refresh_token = decrypt_token(
        connection.encrypted_refresh_token
    )

    credentials = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        scopes=GMAIL_SCOPES
    )

    credentials.refresh(GoogleRequest())

    return build(
        "gmail",
        "v1",
        credentials=credentials
    )

# Create a signed OAuth state for the logged-in user
def create_gmail_state(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "purpose": "gmail_oauth",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=10)
    }

    return jwt.encode(
        payload,
        settings.secret_key,
        algorithm="HS256"
    )

from fastapi import Request
from app.models import User


# Start Google Gmail authorization
@router.get("/connect")
def connect_gmail(user=Depends(current_user)):
    flow = Flow.from_client_config(
        get_google_config(),
        scopes=GMAIL_SCOPES,
        redirect_uri=settings.google_redirect_uri,
autogenerate_code_verifier=False
    )

    state = create_gmail_state(user.id)

    authorization_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
        state=state
    )

    return {"authorization_url": authorization_url}


# Google OAuth callback
@router.get("/callback")
def gmail_callback(
    request: Request,
    state: str,
    db: Session = Depends(get_db)
):
    try:
        payload = jwt.decode(
            state,
            settings.secret_key,
            algorithms=["HS256"]
        )

        if payload.get("purpose") != "gmail_oauth":
            raise HTTPException(status_code=400, detail="Invalid OAuth state")

        user_id = int(payload["sub"])

        user = db.query(User).filter(
            User.id == user_id,
            User.is_active == True
        ).first()

        if not user:
            raise HTTPException(status_code=401, detail="LifeLink account not found")

    except (JWTError, ValueError, KeyError):
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")

    if request.query_params.get("error"):
        raise HTTPException(status_code=400, detail="Google authorization was cancelled")

    try:
        flow = Flow.from_client_config(
            get_google_config(),
            scopes=GMAIL_SCOPES,
            state=state,
            autogenerate_code_verifier=False
        )

        flow.redirect_uri = settings.google_redirect_uri
        flow.fetch_token(authorization_response=str(request.url))

        credentials = flow.credentials

        if not credentials.refresh_token:
            raise HTTPException(
                status_code=400,
                detail="Google did not provide a refresh token. Please reconnect with consent."
            )

        service = build("gmail", "v1", credentials=credentials)
        profile = service.users().getProfile(userId="me").execute()
        gmail_email = profile["emailAddress"]

        connection = db.query(GmailConnection).filter(
            GmailConnection.user_id == user_id
        ).first()

        encrypted_refresh_token = encrypt_token(credentials.refresh_token)

        if connection:
            connection.gmail_email = gmail_email
            connection.encrypted_refresh_token = encrypted_refresh_token
            connection.scopes = " ".join(GMAIL_SCOPES)
            connection.updated_at = datetime.utcnow()
        else:
            connection = GmailConnection(
                user_id=user_id,
                gmail_email=gmail_email,
                encrypted_refresh_token=encrypted_refresh_token,
                scopes=" ".join(GMAIL_SCOPES)
            )
            db.add(connection)

        db.commit()

        return {
            "message": "Gmail connected successfully",
            "gmail_email": gmail_email
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        print("GMAIL CALLBACK ERROR:", type(exc).__name__, str(exc)[:300])
        raise HTTPException(
            status_code=400,
            detail="Gmail connection failed. Check backend terminal."
        )


# Check Gmail connection status
@router.get("/status")
def gmail_status(
    user=Depends(current_user),
    db: Session = Depends(get_db)
):
    connection = db.query(GmailConnection).filter(
        GmailConnection.user_id == user.id
    ).first()

    if not connection:
        return {"connected": False}

    return {
        "connected": True,
        "gmail_email": connection.gmail_email
    }


# Disconnect Gmail from LifeLink
@router.delete("/disconnect")
def disconnect_gmail(
    user=Depends(current_user),
    db: Session = Depends(get_db)
):
    connection = db.query(GmailConnection).filter(
        GmailConnection.user_id == user.id
    ).first()

    if not connection:
        return {"message": "No Gmail account is connected"}

    db.delete(connection)
    db.commit()

    return {"message": "Gmail disconnected from LifeLink"}
# Get Gmail inbox messages
@router.get("/inbox")
def get_gmail_inbox(
    max_results: int = 20,
    user=Depends(current_user),
    db: Session = Depends(get_db)
):
    if max_results < 1 or max_results > 100:
        raise HTTPException(
            status_code=400,
            detail="max_results must be between 1 and 100"
        )

    service = get_gmail_service(user.id, db)

    results = service.users().messages().list(
        userId="me",
        labelIds=["INBOX"],
        maxResults=max_results
    ).execute()

    messages = []

    for item in results.get("messages", []):
        message = service.users().messages().get(
            userId="me",
            id=item["id"],
            format="metadata",
            metadataHeaders=["From", "To", "Subject", "Date"]
        ).execute()

        headers = {
            h["name"].lower(): h["value"]
            for h in message.get("payload", {}).get("headers", [])
        }

        messages.append({
            "id": message["id"],
            "thread_id": message["threadId"],
            "sender": headers.get("from", ""),
            "to": headers.get("to", ""),
            "subject": headers.get("subject", "(No subject)"),
            "date": headers.get("date", ""),
            "snippet": message.get("snippet", ""),
            "unread": "UNREAD" in message.get("labelIds", [])
        })

    return {
        "total_returned": len(messages),
        "messages": messages
    }

