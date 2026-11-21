# LifeLink AI — Blood Availability and Emergency Donor Coordination System

A modular starter for a blood availability and emergency donor coordination platform.

## Stack
- Frontend: HTML, CSS, vanilla JavaScript
- Backend: FastAPI, SQLAlchemy
- Database: MySQL 8+
- Authentication: JWT access tokens

## Important safety boundary
This is a development prototype. Inventory shown by the app is operational information, not medical approval.
Only authorized blood-centre personnel may verify screening, compatibility/cross-match, suitability, reservation and release.
Donor matching only identifies people who may be contacted; it does not establish eligibility or guarantee donation.

## 1. Requirements
- Python 3.10+
- MySQL 8+
- VS Code (recommended)
- A modern browser

## 2. Create database
Open MySQL Workbench or MySQL command line and run `database/schema.sql`.

## 3. Configure backend
Windows PowerShell:
```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` and set your MySQL username/password and a long random SECRET_KEY.

Linux/macOS:
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## 4. Run backend
From `backend/`:
```bash
uvicorn app.main:app --reload
```
Open:
- API docs: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/health

## 5. Run frontend
In another terminal, from the project root:
```bash
cd frontend
py -m http.server 5500
```
Open http://127.0.0.1:5500

The frontend calls `http://127.0.0.1:8000`. If you change the backend host/port, edit `frontend/js/config.js`.

## 6. First API checks
Register a user:
```bash
curl -X POST http://127.0.0.1:8000/api/auth/register ^
  -H "Content-Type: application/json" ^
  -d "{\"full_name\":\"Demo Hospital\",\"email\":\"hospital@example.com\",\"password\":\"ChangeMe123!\",\"role\":\"hospital\"}"
```
Login:
```bash
curl -X POST http://127.0.0.1:8000/api/auth/login ^
  -H "Content-Type: application/x-www-form-urlencoded" ^
  -d "username=hospital@example.com&password=ChangeMe123!"
```
Use the returned `access_token` as `Authorization: Bearer <token>` for protected endpoints.

## 7. Initial API endpoints
- `GET /health`
- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `POST /api/donors`
- `GET /api/donors`
- `POST /api/blood-banks`
- `GET /api/blood-banks`
- `POST /api/inventory`
- `GET /api/inventory`
- `POST /api/requests`
- `GET /api/requests`
- `PATCH /api/requests/{request_id}/status`

All protected endpoints require a valid bearer token. The starter uses role checks for sensitive operations.
### Blood Bank Response Endpoints

- `GET /api/blood-bank-responses/available-requests` — View matching hospital requests.
- `POST /api/blood-bank-responses/` — Submit an accepted or declined response.
- `GET /api/blood-bank-responses/my-responses` — View blood bank response history.
- `GET /api/blood-bank-responses/hospital/{request_id}` — View responses received by a hospital.

### Inventory and Request Features

- Blood unit registration and screening status.
- Inventory release controls.
- Automatic blood group and component matching.
- Blood bank response tracking.
- Hospital request management.
## 8. Testing
1. Start MySQL and confirm the database exists.
2. Start FastAPI and check `/health`.
3. Register a `hospital`, `blood_bank`, and `donor` account (use separate emails).
4. Login and copy each token.
5. Use Swagger `/docs` to test donor, inventory and request endpoints.
6. Confirm invalid credentials return 401 and unauthorized roles return 403.

## Next development phases
Phase 2: stronger relational constraints, seed data, migrations (Alembic), blood-component inventory and audit history.
Phase 3: complete registration/verification workflows and role-specific dashboards.
Phase 4+: reservation transactions, donor consent/eligibility workflow, notification providers, AI forecasts, maps and mobile client.

Do not use real patient or donor data in this starter. Use synthetic data until security, privacy, legal and clinical review is complete.
