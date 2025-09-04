# INSA-Project (backend API)

This repository is a Django project for prescription and medicine management. I added a small REST API scaffold to support a patient mobile app.

Quick setup (Windows / PowerShell):

1. Create virtual environment and install dependencies

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Run migrations and start server

```powershell
python manage.py migrate
python manage.py runserver
```

3. API endpoints (JWT auth)

- POST /api/token/  -> obtain access and refresh tokens (username/password)
- POST /api/token/refresh/  -> refresh access token
- GET /api/patient/me/  -> patient profile (requires Authorization: Bearer <token>)
- GET /api/patient/me/medical-record/  -> medical record
- GET /api/patient/prescriptions/  -> prescriptions list
- GET /api/prescriptions/{id}/  -> prescription detail
- GET /api/medicine/{id}/  -> medicine detail + batches

Notes:
- This scaffold uses DRF and Simple JWT. Adjust `medi_flow/settings.py` to use environment variables for production secrets.
- If you want, I can now scaffold the Flutter app and wire it to these endpoints.
