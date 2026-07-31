# DermaCare AI - Personalized Skincare Recommendation System

**An AI-powered dermocosmetic advisor that analyzes user skincare needs and recommends products from trusted brands using a sophisticated multi-agent system.**

🔗 **Repository**: https://github.com/WernerDJ/dermacare-ai

---

## 🎯 Project Overview

DermaCare uses a **4-agent AI pipeline** to understand user skincare questions and recommend the most relevant products from your brand portfolio. The system combines:
- **Semantic search** (ChromaDB vector embeddings)
- **Intelligent metadata filtering** (life stage hierarchies, skin types, treatment kinds)
- **Natural language understanding** (OpenAI GPT models)
- **Structured product database** (PostgreSQL)

### Key Features
✅ Multi-agent recommendation pipeline
✅ Intelligent skincare routine detection
✅ Life stage hierarchy filtering (Babies → Post-menopausal)
✅ Product database editor with CRUD operations
✅ Search logging & audit trail
✅ Automatic ChromaDB synchronization
✅ Support for multiple brands with independent product catalogs

---

## 🏗️ Technology Stack

| Component | Technology |
|-----------|------------|
| **Backend** | Django 4.2 |
| **Database** | PostgreSQL |
| **Cache/Queue** | Redis |
| **Task Queue** | Celery |
| **Vector Search** | ChromaDB |
| **LLM Provider** | OpenAI API |
| **Containerization** | Docker Compose |
| **Frontend** | Django Templates |

---

## 🤖 The Multi-Agent System

### Agent 1: Product Extractor
**Model**: `gpt-4o-mini`
- Extracts structured product information from PDFs/documents
- Generates: product names, benefits, ingredients, usage instructions
- Outputs: List of products with full metadata

### Agent 2: Vectorizer  
**Technology**: ChromaDB + OpenAI embeddings
- Converts product descriptions to semantic vectors
- Enriches ingredients with INCI standards
- Stores embeddings in ChromaDB collections (one per brand)
- Zero-cost semantic search

### Agent 3: Intelligent Filter
**Model**: `gpt-4.1` (GPT-4 Turbo - smartest non-reasoning model)
- **AI-powered filter extraction**: Understands user queries in natural language
- **Extracts metadata**: Gender, skin type, life stage, treatment kind
- **Hierarchical filtering**: 
  - Teenagers can use products for older age groups
  - Adults can use menopausal/post-menopausal products
  - All ages can use "all ages" products
- **Routine detection**: When user asks for "skincare routine", returns diverse product types (cleanser + serum + moisturizer + SPF)
- **Combines**: Semantic similarity + metadata constraints

### Agent 4: Answer Generator
**Model**: `gpt-4o-mini`
- Takes filtered products and user query
- Generates personalized skincare recommendations
- Provides usage instructions and benefits
- Cites specific products from the filtered results

---

## 📋 Product Database Editor

**URL**: `/product-editor/`

Allows admins to:
- 🏷️ **Browse** products by brand (sidebar)
- ➕ **Create** new products with unique names
- ✏️ **Edit** all product fields (name, category, skin type, life stage, gender, benefits, ingredients, etc.)
- 🗑️ **Delete** products
- ⬅️ **Navigate** between products (First/Previous/Next/Last)
- 💾 **Save** changes instantly
- 🔄 **Sync to ChromaDB** - Updates product count and re-vectorizes all products

### Product Fields
- **Name** (unique per portfolio)
- **Category** (Cleanser, Serum, Moisturizer, etc.)
- **Skin Type** (All, Oily, Dry, Sensitive, Combination)
- **Life Stage** (All ages, Babies, Children, Teenagers, Adults, Menopausal, Post-menopausal)
- **Gender** (Unisex, Male, Female)
- **Treatment Kind** (Acne, Anti-aging, Rosacea, Hydration, Brightening, Firming, Sun protection, etc.)
- **Benefits** (Rich text field)
- **How to Use** (Rich text field)
- **Ingredients** (PDF-extracted or manual)

---

## 📊 Search Logs

**URL**: `/search-logs/`

Comprehensive audit trail of all user searches:
- User who asked
- Question asked
- **Agent 3 Extracted Filters** (what metadata was detected)
- **Agent 3 Products Found** (which products matched)
- **Agent 4 Response** (the final recommendation)
- Brands searched
- Timestamp

Helps debug and understand how the system is interpreting queries.

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- OpenAI API key
- INCI API key (optional, for ingredient enrichment)

### Setup

```bash
# Clone repository
git clone https://github.com/WernerDJ/dermacare-ai
cd dermacare-ai

# Create .env file
cat > .env << EOF
DEBUG=False
SECRET_KEY=your-secret-key-here
OPENAI_API_KEY=sk-...
INCI_API=your-inci-api-key
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com
EOF

# Start services
docker compose up -d

# Run migrations
docker compose exec backend python manage.py migrate

# Create admin user
docker compose exec backend python manage.py createsuperuser

# Access the app
# Admin: http://localhost/admin/
# Dashboard: http://localhost/dashboard/
# Editor: http://localhost/product-editor/
# Logs: http://localhost/search-logs/
```

---

## 📝 Portfolio Management

### Uploading a Portfolio

1. Go to Django admin: `/admin/`
2. Click "Brand Portfolios" → "Add Portfolio"
3. Fill in brand name and upload PDF/document
4. System will:
   - ✅ Extract products via Agent 1
   - ✅ Vectorize to ChromaDB via Agent 2
   - ✅ Save to PostgreSQL
   - ✅ Auto re-vectorize to ensure sync
   - ✅ Update product count

### Current Portfolios

| Brand | Products | Status |
|-------|----------|--------|
| Biotherm | 55 | ✅ Ready |
| Rilastil | 60 | ✅ Ready |
| Eucerin | 70 | ✅ Ready |
| La Roche Posay | 24 | ✅ Ready |
| The Ordinary | 30+ | ✅ Ready |

### Syncing Products

If products exist in PostgreSQL but not in ChromaDB:

**Via UI**: Go to Product Editor → Select brand → Click **🔄 Sync to ChromaDB**

**Via CLI**:
```bash
# Check all portfolios
docker compose exec backend python manage.py sync_chroma

# Fix all mismatches
docker compose exec backend python manage.py sync_chroma --fix-all

# Fix specific brand
docker compose exec backend python manage.py sync_chroma --brand "La Roche Posay"
```

---

## 🔍 Example Queries

### Skincare Routine (Detects diverse product types)
**Query**: "I'm a 40-year-old woman with dry skin, I need a complete morning and evening routine"

**Response**: Cleanser + Serum + Moisturizer + SPF in morning, Cleanser + Serum + Night cream in evening

### Specific Treatment
**Query**: "Best sunscreen for my 5-year-old with atopic dermatitis"

**Response**: Products filtered for: Life stage=Children, Skin type=Sensitive, Treatment=Sun protection

### Advanced Search
**Query**: "I'm menopausal with acne-prone skin, looking for a serum with Niacinamide"

**Response**: Products filtered for: Gender=Female, Life stage=Menopausal, Treatment=Acne, Ingredients match Niacinamide

---

## 🛠️ Configuration

### Environment Variables (.env)

```bash
DEBUG=False
SECRET_KEY=your-secret-key
OPENAI_API_KEY=sk-...
INCI_API=optional-inci-key
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com
DB_NAME=dermacare_db
DB_USER=dermacare_user
DB_PASSWORD=secure-password
DB_HOST=db
DB_PORT=5432
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

### Django Settings (backend/dermacare/settings.py)

Key configurations:
- CSRF_TRUSTED_ORIGINS: Add your domain
- LOGGING: File logging (optional)
- REST_FRAMEWORK: Token auth for API endpoints

---

## 📂 Project Structure
dermacare-ai/
├── .env
├── docker-compose.yml
├── README.md
├── .gitignore
├── chroma_db/ # Vector database storage
├── backend/
│ ├── dermacare/ # Django project settings
│ │ ├── settings.py
│ │ ├── urls.py
│ │ └── wsgi.py
│ ├── api/
│ │ ├── models.py # Product, BrandPortfolio, AnalysisTask, SearchLog
│ │ ├── views.py # Dashboard, editor, API endpoints
│ │ ├── urls.py
│ │ ├── tasks.py # Celery tasks with auto-vectorization
│ │ ├── admin.py # Django admin customization
│ │ ├── agents/
│ │ │ ├── agent1_extractor.py # PDF → Product extraction
│ │ │ ├── agent2_vectorizer.py # Products → ChromaDB
│ │ │ ├── agent3_filter.py # Query → Metadata + Semantic filtering
│ │ │ └── agent4_answerer.py # Recommendations generation
│ │ ├── management/
│ │ │ └── commands/
│ │ │ └── sync_chroma.py # Manual ChromaDB sync
│ │ └── templates/
│ │ ├── base.html
│ │ ├── login.html # Modern Cetaphil-style login
│ │ ├── signup.html
│ │ ├── user_dashboard.html # Q&A interface
│ │ ├── admin_panel.html # Admin controls
│ │ ├── product_editor.html # CRUD products
│ │ └── search_logs.html # Audit trail
│ └── Dockerfile_backend
└── Dockerfile (docker-compose orchestration)
---

## 🧪 Testing the System

### 1. Ask a Question
### 2. View Search Log
- Go to `/search-logs/`
- Click "View" on your search
- See extracted filters, products found, and full recommendation

### 3. Edit & Sync
- Go to `/product-editor/`
- Add/edit products
- Click "🔄 Sync to ChromaDB"
- System syncs to vector database automatically

---

## 🐛 Known Issues & Solutions

### Products in DB but not in ChromaDB
**Symptom**: Product appears in admin but not in search results

**Solution**:
```bash
# Use the Sync command
docker compose exec backend python manage.py sync_chroma --fix-all
```
### Celery Task Failures
**Check logs**:
```bash
docker compose logs celery | tail -50
```

**Common cause**: Model cache in Celery container. Solution:
```bash
docker compose down
docker compose up -d --build
```

---

## 🔐 Security

- ✅ CSRF protection enabled
- ✅ Login required for dashboard
- ✅ Admin-only product editor
- ✅ Secure session cookies
- ✅ API endpoints authenticated
- ✅ No API keys in repository

---

## 📜 License

Proprietary - All rights reserved

---

## 📞 Support

For issues:
1. Check `/search-logs/` for debugging info
2. Review backend logs: `docker compose logs backend`
3. Verify ChromaDB sync: `docker compose exec backend python manage.py sync_chroma`

---

**Last Updated**: July 2026  