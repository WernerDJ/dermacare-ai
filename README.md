# DermaCare Product Portfolio Manager

A Django + React web application for managing dermocosmetic product portfolios with AI-powered analysis and ingredient lookups.

## Quick Start with Docker

### 1. Build and Start Containers
```bash
docker-compose up -d
```

### 2. Initialize Database
```bash
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py createsuperuser
```

### 3. Access the Application
- **Frontend:** http://localhost:3000
- **Admin Panel:** http://localhost:8000/admin
- **API:** http://localhost:8000/api

## Project Structure

```
dermacare-project/
├── backend/
│   ├── dermacare/          (Django project settings)
│   ├── api/                (REST API app)
│   ├── manage.py
│   ├── requirements_backend.txt
│   └── Dockerfile_backend
├── frontend/
│   ├── src/components/     (React components)
│   ├── package.json
│   └── Dockerfile_frontend
├── docker-compose.yml
├── nginx.conf
├── .env.example
└── README.md
```

## Environment Setup

1. Create `.env` file from template
2. Add your credentials (GEMINI_API_KEY, INCI_API, DB_PASSWORD)
3. Run `docker-compose up -d`

See the full README.md in Google Drive for complete setup instructions.
