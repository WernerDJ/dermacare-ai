# DermaCare AI - Dermocosmetic Product Advisor

An intelligent AI-powered platform that helps users discover personalized skincare recommendations from brand portfolios. Upload brand product catalogs, and DermaCare automatically extracts, analyzes, and recommends products based on user preferences.

**Ask questions like:**
- *"What product is best for oily skin with acne?"*
- *"Which products are suitable for teenagers?"*
- *"Show me the most hydrating moisturizers"*
- *"I'm a man with dry skin, give me a skincare routine"*

Get AI-generated recommendations with detailed reasoning.

---

## ✨ Key Features

### 📚 Brand Portfolio Management
- Upload brand product catalogs (PDF, DOCX, TXT)
- Automatically extract product metadata (ingredients, benefits, usage)
- Store up to 1000+ products per brand
- Track analysis history and status

### 🤖 Intelligent Recommendation Engine
- 4-specialized AI agents working in pipeline:
  - **Agent 1:** Extracts product metadata from documents
  - **Agent 2:** Vectorizes products and enriches ingredient data
  - **Agent 3:** Filters products based on user preferences (free vector search)
  - **Agent 4:** Generates natural language recommendations
- Cost-optimized: Uses cheaper models where possible, free APIs for data enrichment
- Real-time learning: Improves recommendations based on portfolio data

### 🎯 Smart Search & Filtering
- Vector-based semantic search (instant, no API costs)
- Filter by: skin type, gender, life stage, product category
- Multi-brand search across portfolios
- Contextual recommendations based on user input

### 👤 User & Admin Dashboards
- **Admin Panel:** Upload portfolios, manage brands, track analysis tasks
- **User Dashboard:** Browse brands, ask questions, get recommendations
- Real-time task status updates
- Product portfolio viewing with full metadata

### 🔐 Secure Authentication
- User registration and login
- Admin controls for portfolio management
- Session management
- CSRF protection across localhost and production domains

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- OpenAI API key
- PostgreSQL (included)
- Redis (included)

### Installation

1. **Clone repository:**
```bash
git clone https://github.com/WernerDJ/dermacare-ai.git
cd dermacare-ai
```

2. **Setup environment:**
```bash
cp .env.example .env
# Edit .env with your OPENAI_API_KEY
```

3. **Start application:**
```bash
docker compose up -d
```

4. **Access:**
- App: http://localhost
- Admin: http://localhost/admin/ (login required)

### First Time Setup

1. **Create admin account:**
```bash
docker compose exec backend python manage.py createsuperuser
# Username: admin
# Password: (your choice)
```

2. **Upload first portfolio:**
   - Go to Admin Panel
   - Click "Upload Portfolio"
   - Enter brand name (e.g., "Biotherm")
   - List product names (one per line)
   - Upload PDF/DOCX with product information
   - Click "Analyze"

3. **Ask questions:**
   - Go to Dashboard
   - Select brand(s) to search
   - Ask any skincare question
   - Get AI recommendations

---

## 📖 Usage Guide

### For Administrators

**Upload a Brand Portfolio:**
1. Navigate to Admin Panel
2. Fill in brand details:
   - **Brand Name:** Company name (e.g., "Biotherm", "Sensilis")
   - **Product Names:** List of products to extract (one per line)
   - **Product Document:** PDF/DOCX with product information
3. Check "Lookup Ingredients" to enrich with INCIDecoder data
4. Click "Analyze"
5. Monitor extraction progress in task list
6. View extracted products in portfolio

**Manage Portfolios:**
- View all uploaded brands
- See product counts and analysis status
- Delete brands if needed
- Track extraction errors and retry

### For End Users

**Get Personalized Recommendations:**
1. Go to Dashboard
2. Select brands you want to search (or leave blank for all)
3. Ask your skincare question:
   - *"What's best for sensitive skin?"*
   - *"I need a moisturizer for oily skin"*
   - *"Products for menopausal women"*
4. Receive AI-generated answer with:
   - Top product recommendations
   - Reasoning for each product
   - How to use tips
   - Ingredient highlights

---

## 🏗️ Architecture

### Data Pipeline
### Why 4 Agents?

- **Specialization:** Each agent does one thing well
- **Cost Efficiency:** Expensive LLMs only used when needed
- **Speed:** Parallel processing, fast vector searches
- **Accuracy:** Focused prompts lead to better results

---

## 🛠️ Technical Stack

| Component | Technology |
|-----------|-----------|
| Backend | Django 4.2 |
| Database | PostgreSQL |
| Vector DB | ChromaDB |
| Task Queue | Celery + Redis |
| LLM | OpenAI (GPT-4o-mini) |
| Frontend | Django Templates |
| Deployment | Docker Compose |
| Auth | Django Built-in |

### Requirements
- Python 3.11+
- Docker 24+
- 2GB RAM minimum
- 5GB storage (for vector DB)

---

## 📊 Performance

- **Extraction:** 70 products in ~45 seconds
- **Search Latency:** <100ms per query
- **Enrichment Coverage:** 95%+ of products
- **Scalability:** Handles 1000+ products per brand
- **Concurrent Users:** 50+ simultaneous users

---

## 🔧 Configuration

### Environment Variables

```bash
# Required
OPENAI_API_KEY=sk-...
SECRET_KEY=your-secret-key

# Database
DB_ENGINE=django.db.backends.postgresql
DB_NAME=dermacare_db
DB_USER=dermacare_user
DB_PASSWORD=dermacare_pass
DB_HOST=db
DB_PORT=5432

# Redis
CELERY_BROKER_URL=redis://redis:6379/0

# Security
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,ip-xpert.com,www.ip-xpert.com

# CSRF
CSRF_TRUSTED_ORIGINS=https://ip-xpert.com,https://www.ip-xpert.com
```

---

## 🧪 Testing

Run test suite:

```bash
docker compose exec backend python manage.py test api.tests -v 2
```

Current coverage: **28 tests passing**
- Auth flows (login, signup, logout)
- Admin controls and access
- Portfolio upload and deletion
- Dashboard functionality

---

## 📦 API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET/POST | `/login/` | User login |
| GET/POST | `/signup/` | User registration |
| GET | `/logout/` | User logout |
| GET/POST | `/admin/` | Admin panel |
| GET/POST | `/dashboard/` | User Q&A interface |
| GET | `/api/task/<id>/status/` | Check task progress |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Clone and setup
git clone https://github.com/yourusername/dermacare-ai.git
cd dermacare-ai

# Install dependencies
pip install -r backend/requirements_backend.txt

# Run migrations
python backend/manage.py migrate

# Start dev server
python backend/manage.py runserver
```

---

## 🐛 Troubleshooting

### CSRF Token Errors
- Check `CSRF_TRUSTED_ORIGINS` in settings
- Clear browser cookies
- Ensure HTTPS for production

### No Products After Upload
- Check Celery logs: `docker compose logs celery`
- Verify PDF contains product information
- Check product names match document content

### Search Returns No Results
- Verify products were extracted successfully
- Check if brand name matches exactly
- Try simpler search terms

---

## 📝 License
MIT License
