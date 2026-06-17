# DermaCare AI — Dermocosmetic Advisor
 
An AI-powered web application that analyzes cosmetic product catalogues (PDFs) and answers questions about ingredients, formulations, and product suitability using Google's Gemini AI.
 
---
 
## 📋 Table of Contents
 
- [How to Use the App](#how-to-use-the-app)
- [Deploying Your Own Instance](#deploying-your-own-instance)
- [Environment Variables](#environment-variables)
- [Architecture](#architecture)
---
 
## How to Use the App
 
### Signing Up & Logging In
 
1. Open the app in your browser
2. Click **Sign Up** to create a new account
3. Log in with your credentials
4. You will be automatically routed to the correct dashboard based on your role
### Admin Users — Uploading Product Catalogues
 
Admins can upload brand PDF catalogues for AI analysis:
 
1. Log in as an admin user
2. In the **Admin Dashboard**, click **Upload PDF**
3. Select a brand catalogue PDF from your computer (up to 100MB)
4. Give the portfolio a name (e.g. "Biotherm 2024")
5. Click **Analyse** — the AI will extract all products and ingredients in the background
6. Wait 30–60 seconds for processing to complete (you can track progress in real time)
7. Once done, the portfolio becomes available to all users
### Regular Users — Asking Questions
 
1. Log in to your account
2. In the **User Dashboard**, select a product portfolio
3. Type your question in the chat box, for example:
   - *"Which products are suitable for sensitive skin?"*
   - *"What are the active ingredients in the moisturising cream?"*
   - *"Is there a product without parabens?"*
4. The AI will answer based on the actual product data from the catalogue
### User Accounts
 
| Role | Capabilities |
|------|-------------|
| Admin | Upload PDFs, manage portfolios, view all analyses |
| Regular User | Ask questions, view shared portfolios |
 
---
 
## Deploying Your Own Instance
 
### Prerequisites
 
- A server running Ubuntu 22.04 or 24.04 (AWS EC2 t3.small or larger recommended, ~$20/month)
- Docker and Docker Compose installed
- A Google Gemini API key ([get one here](https://makersuite.google.com/app/apikey))
- Optionally: a domain name and SSL certificate
### Step 1 — Prepare the Server
 
```bash
# Update the system
sudo apt update && sudo apt upgrade -y
 
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
 
# Add your user to the Docker group
sudo usermod -aG docker $USER
newgrp docker
 
# Install Docker Compose plugin
sudo apt install docker-compose-plugin -y
```
 
### Step 2 — Clone the Repository
 
```bash
git clone https://github.com/WernerDJ/dermacare-ai.git
cd dermacare-ai
```
 
### Step 3 — Configure Environment Variables
 
The repository includes a file called `env` which is a template for your environment configuration.
 
```bash
# View the template
cat env
```
 
Fill in all the values marked with `******` (see [Environment Variables](#environment-variables) below for details).
 
Once you have filled in all values, rename the file:
 
```bash
# Add the dot prefix and remove the .txt extension
mv env .env
```
 
> ⚠️ The file **must** be named `.env` (with a leading dot and no extension) for Docker Compose to pick it up automatically.
 
### Step 4 — Launch the App
 
```bash
docker compose up -d --build
```
 
This will pull and build all Docker images. The first run takes 5–10 minutes.
 
### Step 5 — Run Database Migrations
 
```bash
docker compose exec backend python manage.py migrate
```
 
### Step 6 — Create an Admin User
 
```bash
docker compose exec backend python manage.py createsuperuser
```
 
Follow the prompts to set a username and password for your admin account.
 
### Step 7 — Access the App
 
Open your browser and go to:
 
```
http://YOUR_SERVER_IP
```
 
Or if you have a domain configured:
 
```
https://yourdomain.com
```
 
### Enabling Auto-Start on Reboot
 
To make the app start automatically when the server reboots:
 
```bash
sudo systemctl enable docker
```
 
The `restart: always` directive in `docker-compose.yml` ensures all containers restart automatically with Docker.
 
### Useful Commands
 
```bash
# Check all running services
docker compose ps
 
# View backend logs
docker compose logs backend -f
 
# View all logs
docker compose logs -f
 
# Restart everything
docker compose restart
 
# Stop everything
docker compose down
 
# Stop and wipe all data (careful!)
docker compose down -v
```
 
---
 
## Environment Variables
 
The `env` file in the repository root is a template. Copy it to `.env` and fill in the values below.
 
| Variable | Description | Example |
|----------|-------------|---------|
| `DEBUG` | Django debug mode. Always `False` in production | `False` |
| `SECRET_KEY` | Django secret key — generate a long random string | `your-long-random-secret-key` |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hostnames/IPs | `localhost,127.0.0.1,yourdomain.com` |
| `DB_NAME` | PostgreSQL database name | `dermacare_db` |
| `DB_USER` | PostgreSQL username | `dermacare_user` |
| `DB_PASSWORD` | PostgreSQL password — choose something strong | `your-db-password` |
| `DB_HOST` | Database host — keep as `db` for Docker | `db` |
| `DB_PORT` | Database port — keep as `5432` | `5432` |
| `CELERY_BROKER_URL` | Redis URL for Celery task queue | `redis://redis:6379/0` |
| `CELERY_RESULT_BACKEND` | Redis URL for Celery results | `redis://redis:6379/0` |
| `GEMINI_API_KEY` | Your Google Gemini API key | `AIza...` |
| `INCI_API` | INCI ingredient database API key | `your-inci-api-key` |
| `CORS_ALLOWED_ORIGINS` | Allowed frontend origins for CORS | `http://localhost:3000` |
 
### Generating a Django Secret Key
 
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(50))"
```
 
### Important Notes
 
- Never commit your `.env` file to version control — it is already in `.gitignore`
- The `env` template file in the repo contains placeholder values (`******`) — these must all be replaced before the app will work
- After filling in the values, the file must be renamed from `env` to `.env` (add a dot prefix and remove any `.txt` extension)
---
 
## Architecture
 
The app runs as 6 Docker services orchestrated by Docker Compose:
 
| Service | Technology | Role |
|---------|-----------|------|
| `nginx` | Nginx | Reverse proxy, serves frontend, routes API calls |
| `frontend` | React | User interface |
| `backend` | Django + Gunicorn | REST API, business logic |
| `celery` | Celery | Async PDF processing tasks |
| `db` | PostgreSQL 15 | Data persistence |
| `redis` | Redis 7 | Task queue and cache |
 
### How PDF Analysis Works
 
1. Admin uploads a PDF through the UI
2. Django saves the file and queues an async Celery task
3. Celery uploads the PDF to Google's Gemini File API
4. Gemini analyses the document and extracts product and ingredient data
5. Results are saved to PostgreSQL
6. Users can then query the extracted data via natural language Q&A
---
 
## Tech Stack
 
- **Backend:** Python 3.11, Django 4.x, Django REST Framework, Celery
- **Frontend:** React, JavaScript
- **AI:** Google Gemini API (via `google-generativeai`)
- **Database:** PostgreSQL 15
- **Cache/Queue:** Redis 7
- **Infrastructure:** Docker, Docker Compose, Nginx
- **Deployment:** AWS EC2 (Ubuntu 24.04)
---
 
## License
 
MIT License — feel free to fork and adapt for your own use.
