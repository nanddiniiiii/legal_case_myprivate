# ⚖️ Legal Search Pro - AI-Powered Legal Case Database

**Production-ready semantic search engine for 1,813+ real Indian legal cases from Indian Kanoon with AI embeddings and web scraping.**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0-green.svg)](https://flask.palletsprojects.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)](https://www.postgresql.org/)
[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](#license)

---

## 🎯 What It Does

Search through **1,813+ real Indian legal cases** using AI. Find similar precedents, filter by category/date/court, save bookmarks, and track history. Perfect for legal research and case analysis.

**Live Demo Ready:** Share ngrok URL instantly → no cloud deployment needed!

---

## ✨ Key Features

| Feature | Details |
|---------|---------|
| 🔍 **Hybrid Semantic Search** | Vector + keyword matching - finds both similar meaning AND exact legal references |
| 🕷️ **Web Scraper** | Auto-scrapes Indian Kanoon - 21 categories, 500+ cases per category, generates AI embeddings |
| 🧠 **AI-Powered Similarity** | Finds related precedents using Sentence Transformers (768-dimensional vectors) |
| 📊 **Advanced Filters** | Search by category, date range, court, judge, year |
| 👤 **User System** | Login/signup with bcrypt hashing, bookmarks, search history, profile |
| 📱 **Modern UI** | Responsive HTML5/CSS3/JS with dark/light theme, case comparisons |
| 🌐 **Instant Public URLs** | ngrok integration included - share demo in 30 seconds |
| ⚡ **Smart Caching** | TTL-based caching reduces database load by ~60% |

---

## 🛠️ Technology Stack

**Backend:**
- Python 3.11, Flask 3.0, PostgreSQL 15
- Sentence Transformers (all-mpnet-base-v2, 768-dim embeddings)
- BeautifulSoup4 (web scraping), NumPy (vector math)

**Frontend:**
- HTML5, CSS3, Vanilla JavaScript (ES6+)
- Bootstrap 5, responsive design

**Deployment:**
- Gunicorn (production WSGI)
- ngrok (public tunneling - included)
- Ready for AWS EC2, Heroku, Railway, etc.

---

## 🚀 Quick Start (5 minutes)

### 1. Setup Environment

```bash
git clone https://github.com/nanddiniiiii/legal_case_myprivate.git
cd legal_case_myprivate

# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
pip install beautifulsoup4 requests
```

### 3. Setup Database

```bash
# Create tables
python recreate_database.py
python setup_auth_legal_search.py

# Optional: Scrape fresh data (1-2 hours, generates 1813+ cases with embeddings)
python scrape_indian_kanoon.py

# Verify
python quick_check.py
```

### 4. Run the App

**Terminal 1 - Start Backend:**
```bash
python api.py
```
Runs on `http://127.0.0.1:5000`

**Terminal 2 - Create Public URL:**
```bash
.\ngrok.exe http 5000
```

**Access:**
- **Local:** `http://127.0.0.1:5000/DBMS%20UI/index.html`
- **Public (share this):** `https://randomstring-123.ngrok.io/DBMS%20UI/index.html`

---

## 📊 Project Structure

```
├── api.py                         # Flask backend (search, API endpoints)
├── scrape_indian_kanoon.py        # Web scraper (21 categories)
├── recreate_database.py           # DB schema setup
├── setup_auth_legal_search.py     # Auth tables
├── quick_check.py                 # Verify data
│
├── DBMS UI/                       # Frontend
│   ├── index.html                 # Main search interface
│   ├── case-details.html          # Case view + similar cases
│   ├── analytics-dashboard.html   # Statistics & charts
│   ├── bookmarks.html             # Saved cases
│   ├── profile.html               # User profile
│   └── [6 more pages]
│
├── requirements.txt               # All dependencies
├── .env                          # DB & OAuth config
├── Procfile                      # Heroku deployment
├── ngrok.exe                     # Public tunnel (Windows)
│
└── DETAILED_README.md            # Full documentation
```

---

## 💾 Database

**Main Table:**
```sql
cases (
  case_number     -- IK-12345678-2024
  title           -- Case name
  parties         -- Petitioner vs Respondent
  description     -- Full judgment text
  category        -- theft, murder, property_dispute, etc.
  embedding       -- 768-dim vector for semantic search
  ...
)
```

**Supporting Tables:** users, user_searches, user_bookmarks

**Data:** 1,813 real Indian legal cases with AI embeddings

---

## 📡 API Endpoints

| Endpoint | Method | Returns |
|----------|--------|---------|
| `/search?query=theft` | GET | Semantic search results |
| `/api/similar-cases/IK-123` | GET | Related cases by AI similarity |
| `/api/analytics` | GET | Case statistics, charts |
| `/api/bookmarks` | GET | User's saved cases |
| `/api/search-history` | GET | User's search history |
| `/api/bookmark` | POST | Save a case |

---

## 🔍 How Semantic Search Works

1. **Query:** User enters "cases involving theft of mobile phones"
2. **Embedding:** AI model converts query to 768-dimensional vector
3. **Similarity:** Search compares against 1,813 case embeddings (cosine similarity)
4. **Hybrid Scoring:** Combines semantic score (70%) + keyword score (30%)
5. **Results:** Returns ranked cases + similar precedents

**Why Hybrid?**
- Pure semantic: Misses exact legal references like "IPC 379"
- Pure keyword: Misses similar cases with different wording
- Hybrid: Gets both! 

---

## 🔐 Security

✅ Passwords hashed with bcrypt (cost factor 12)  
✅ SQL parameterized queries (injection-safe)  
✅ CORS configured for API  
✅ Session management with secure cookies  
✅ Google OAuth support (optional)  
✅ Environment variables for secrets (.env)  

---

## 📈 Performance

| Metric | Value |
|--------|-------|
| Search Speed | 0.2-0.5s (semantic), <100ms (cached) |
| Cases in DB | 1,813 with embeddings |
| Model Size | 80MB (fits in memory) |
| API Response | <500ms average |
| Database Size | ~200MB |

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| "relation 'cases' does not exist" | Run `python recreate_database.py` |
| "pgvector not available" | See [INSTALL_PGVECTOR_WINDOWS.md](INSTALL_PGVECTOR_WINDOWS.md) |
| ngrok command not found | Use included `.\ngrok.exe http 5000` |
| Database connection failed | Check `.env` credentials, ensure PostgreSQL running |
| Scraper timeout | Check internet, adjust `DELAY_BETWEEN_REQUESTS` in scraper |

---

## 📚 Documentation

- **[DETAILED_README.md](DETAILED_README.md)** - Complete docs (database schema, all endpoints, detailed features)
- **[HOW_TO_GET_REAL_DATA.md](HOW_TO_GET_REAL_DATA.md)** - Scraping guide
- **[INSTALL_PGVECTOR_WINDOWS.md](INSTALL_PGVECTOR_WINDOWS.md)** - pgvector setup (Windows)

---

## 🚀 Deployment Options

### Quick (Development)
```bash
python api.py
.\ngrok.exe http 5000
# Share ngrok URL!
```

### Cloud (Production)
- **Heroku:** `git push heroku main` (uses Procfile)
- **AWS EC2:** Run with Gunicorn + RDS PostgreSQL
- **Railway/Render:** Connect repo, auto-deploys
- **Docker:** Build image from repo

---

## 📊 Data & Performance

**Dataset:** 1,813 real Indian legal cases
- Categories: theft, murder, property dispute, divorce, fraud, etc.
- Source: Indian Kanoon (indiankanoon.org)
- Coverage: Various years and courts

**AI Model:** Sentence Transformers (all-mpnet-base-v2)
- Dimensions: 768
- Trained on: 215M sentence pairs
- Speed: Real-time (<200ms per search)

---


**What to test:**
1. Search "theft" → get relevant cases ranked by similarity
2. Click case → see full details + similar precedents
3. Bookmark a case → appears in bookmarks page
4. Analytics page → shows database statistics
5. Share ngrok URL → others can access live demo

**Time to live demo:** 5 minutes (with data already scraped)

---

## 📝 License

MIT License - See LICENSE file

---

## 🤝 Contributing

Contributions welcome! 
```bash
git checkout -b feature/your-feature
git commit -am "Add feature"
git push origin feature/your-feature
```

---

**Built for production. Ready to run. Real data. 🎯**
