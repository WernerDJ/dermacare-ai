# DermaCare AI - Personalized Skincare Recommendation System

**An AI-powered dermocosmetic advisor that analyzes user skincare needs and recommends products from trusted brands using a sophisticated multi-agent system.**

🔗 **Repository**: https://github.com/WernerDJ/dermacare-ai

---

## 🎯 Project Overview

DermaCare uses a **4-agent AI pipeline** to understand user skincare questions and recommend the most relevant products from your brand portfolio. The system combines:
- **Semantic search** (ChromaDB vector embeddings)
- **Intelligent metadata filtering** (life stage hierarchies, skin types, treatment kinds)
- **Chemical compound enrichment** (PubChem synonym lookup)
- **Natural language understanding** (OpenAI GPT models)
- **Structured product database** (PostgreSQL)

### Key Features
✅ Multi-agent recommendation pipeline
✅ Intelligent ingredient synonym detection via PubChem
✅ Exclusion filtering (e.g., "without avobenzone")
✅ Skincare routine detection with diverse product selection
✅ Life stage hierarchy filtering (Babies → Post-menopausal)
✅ Product database editor with full CRUD operations
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
- Extracts structured product information from documents
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
  - All ages products available to everyone
- **Routine detection**: When user asks for "skincare routine", returns diverse product types (cleanser + serum + moisturizer + SPF)
- **Combines**: Semantic similarity + metadata constraints

### Agent 3.5: Ingredient Enricher 
**Technology**: PubChem API + Chemical Synonym Lookup
- **Detects chemical compounds** in user queries (e.g., "avobenzone", "salicylic acid")
- **Looks up synonyms** via PubChem API (free, no auth required)
- **Expands exclusion filters** - "without avobenzone" automatically checks:
  - Butyl methoxydibenzoylmethane
  - Avobenzonum
  - Parsol 1789
  - Eusolex 9020
  - And 7+ other known synonyms
- **Filters products intelligently** - Removes any product containing the ingredient OR its synonyms

Example: If a customer asks for "sunscreen **without avobenzone**":
1. Agent 3.5 detects "avobenzone" as excluded ingredient
2. Queries PubChem → gets 11 known synonyms
3. Filters out products containing ANY synonym
4. Returns only truly safe alternatives ✅

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
- ✏️ **Edit** all product fields
- 🗑️ **Delete** products
- ⬅️ **Navigate** between products (First/Previous/Next/Last)
- 💾 **Save** changes instantly
- 🔄 **Sync to ChromaDB** - Updates product count and re-vectorizes all products

### Product Fields
- **Name** (unique per portfolio)
- **Category** (Cleanser, Serum, Cream, Lotion, Foundation, Thermal Water, Sunscreen, Stick, Bar, Gel, Balsam, Spray, Shampoo, Ointment)
- **Skin Type** (All, Dry, Sensitive, Combination, Normal to Oily, Normal to Dry, Atopic, Hyperkeratosis, Itchy)
- **Life Stage** (All ages, Babies, Children, Teenagers, Adults, Menopausal, Post-menopausal)
- **Gender** (Unisex, Male, Female)
- **Treatment Kind** (Acne, Anti-aging, Anti-wrinkles, Rosacea, Hyperpigmentation, Moisturizer, SPF, Chemical lifting, Eyebags, Exfoliation, Eyes, Haircare, Aftersun, Allergies, Adhesive Patch, Post-surgery, Scars, Tattoos)
- **Benefits** (Rich text field)
- **How to Use** (Rich text field)
- **Ingredients** (Manual entry or extracted)

---

## 📊 Search Logs

**URL**: `/search-logs/`

Comprehensive audit trail of all user searches:
- User who asked
- Question asked
- **Agent 3 Extracted Filters** (what metadata was detected)
- **Agent 3.5 Excluded Ingredients** (chemical compounds to avoid)
- **Agent 3 Products Found** (which products matched after filtering)
- **Agent 4 Response** (the final recommendation)
- Brands searched
- Timestamp

Helps debug and understand how the system is interpreting queries.

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- OpenAI API key

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

## 📝 Managing Products

### Adding Products

1. Go to `/product-editor/`
2. Click on a brand from the sidebar
3. Click **+ New** button
4. Fill in all product details
5. Click **💾 Save**

### Editing Products

1. Navigate through products using First/Previous/Next/Last buttons
2. Update any fields
3. Click **💾 Save**

### Syncing Products to Search Database

After adding/editing products:
1. Click **🔄 Sync to ChromaDB** button
2. System will:
   - ✅ Update product count
   - ✅ Vectorize all products
   - ✅ Make them searchable

---

## 🧪 Example Queries

### Skincare Routine (Detects diverse product types)
**Query**: "I'm a 40-year-old woman with dry skin, I need a complete morning and evening routine"

**Response**: Cleanser + Serum + Moisturizer + SPF in morning, Cleanser + Serum + Night cream in evening

### Specific Treatment with Exclusion
**Query**: "Best sunscreen for my 5-year-old with atopic dermatitis that doesn't contain avobenzone"

**Response**: 
- Filters for: Life stage=Children, Skin type=Atopic, Treatment=SPF
- Checks ingredients: Excludes "avobenzone" AND all 11 known synonyms
- Returns only safe products ✅

### Advanced Search
**Query**: "I'm menopausal with acne-prone skin, looking for a serum with niacinamide but no salicylic acid"

**Response**: 
- Extracts: Gender=Female, Life stage=Menopausal, Treatment=Acne
- Ingredient search: Includes niacinamide + all variants
- Excludes: Salicylic acid + all variants (BHA, hydroxyacetic acid, etc.)
- Returns personalized matches

---

## 🔐 Security

- ✅ CSRF protection enabled
- ✅ Login required for dashboard
- ✅ Admin-only product editor
- ✅ Secure session cookies
- ✅ API endpoints authenticated
- ✅ No API keys in repository

---

## 📈 Performance

- **ChromaDB Caching**: Fast semantic search (< 500ms)
- **PubChem API**: Ingredient synonym lookups cached per session
- **Redis**: Query result caching
- **Celery**: Async product vectorization
- **PostgreSQL**: Optimized indexes on common queries

---

## 🛠️ Configuration

### Environment Variables (.env)

```bash
DEBUG=False
SECRET_KEY=your-secret-key
OPENAI_API_KEY=sk-...
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com
DB_NAME=dermacare_db
DB_USER=dermacare_user
DB_PASSWORD=secure-password
DB_HOST=db
DB_PORT=5432
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

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
│ │ ├── tasks.py # Celery tasks
│ │ ├── admin.py # Django admin customization
│ │ ├── agents/
│ │ │ ├── agent1_extractor.py
│ │ │ ├── agent2_vectorizer.py
│ │ │ ├── agent3_filter.py
│ │ │ ├── agent3_5_enricher.py # NEW: Ingredient enricher with PubChem
│ │ │ └── agent4_answerer.py
│ │ ├── management/
│ │ │ └── commands/
│ │ │ ├── sync_chroma.py
│ │ │ └── translate_products.py
│ │ └── templates/
│ │ ├── base.html
│ │ ├── login.html
│ │ ├── signup.html
│ │ ├── user_dashboard.html
│ │ ├── admin_panel.html
│ │ ├── product_editor.html
│ │ └── search_logs.html
│ └── Dockerfile_backend
└── docker-compose.yml

---

## 📜 License

Proprietary - All rights reserved

---

## 📞 Support

For issues, check `/search-logs/` for debugging information or review backend logs:

```bash
docker compose logs backend | tail -50
```

---

**Last Updated**: August 2026  
**Version**: 1.1.0 - Agent 3.5 Ingredient Enricher Enabled
