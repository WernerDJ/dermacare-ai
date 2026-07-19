# DermaCare AI - Dermocosmetic Product Advisor

An intelligent AI-powered platform that helps users discover personalized skincare recommendations from brand portfolios. Upload brand product catalogs, and DermaCare automatically extracts, analyzes, and recommends products based on user preferences.

**Ask questions like:**
- *"What Biotherm product is best for oily skin with acne?"*
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
- https://ip-xpert.com/login/

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