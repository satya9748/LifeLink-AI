# LifeLink AI API — Phase 1

Base URL: `http://127.0.0.1:8000`

Interactive OpenAPI documentation: `/docs`

## Authentication
Register:
`POST /api/auth/register`
```json
{"full_name":"Sample Donor","email":"donor@example.com","password":"ChangeMe123!","role":"donor"}
```
Allowed public roles: `hospital`, `blood_bank`, `donor`. Admin creation must be a protected administrative operation, not public registration.

Login:
`POST /api/auth/login` (form fields `username` and `password`)
Returns a bearer token.

Current user:
`GET /api/auth/me`

## Donors
`POST /api/donors` — donor token; creates own donor profile.
`GET /api/donors?city=Bhubaneswar&blood_group=O%2B` — hospital, blood-bank or admin token.
Only donors who consented to alerts and are marked contactable are returned.

## Blood banks
`POST /api/blood-banks` — blood-bank token; submits profile for verification.
`GET /api/blood-banks?city=Bhubaneswar` — lists verified blood banks.

## Inventory
`POST /api/inventory` — blood-bank token; adds a unit in quarantined state.
`GET /api/inventory?city=Bhubaneswar&blood_group=O%2B` — returns units recorded as available and screening-passed at verified banks.

## Hospital requests
`POST /api/requests` — hospital token; creates a request.
`GET /api/requests` — hospital sees own requests; bank/admin can see requests.
`PATCH /api/requests/{request_id}/status` — bank/admin token; updates workflow status.

## Important
This is an initial development API. It does not yet implement hospital profile creation, admin verification UI, atomic unit reservations, clinical compatibility, donor eligibility decisions, SMS/email provider integration, or AI predictions. Those are planned phases, not completed features.
