# Legal Search Pro - AI-Powered Case Database

> **Full-Stack Legal Case Management System with AI-Powered Semantic Search**

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0-green.svg)](https://flask.palletsprojects.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)](https://www.postgresql.org/)
[![AI](https://img.shields.io/badge/AI-Sentence_Transformers-orange.svg)](https://www.sbert.net/)

**Live Demo:** Available on request (ngrok-based deployment)  
*Contact for live demo URL during interviews*

---

## Overview

**Legal Search Pro** is a full-stack AI-powered legal case database with **2,160 real Indian legal cases** from Indian Kanoon. Features semantic search, NLP-based key facts extraction, citation detection, and vector similarity for finding related precedents.

### Key Features

-  **Hybrid Semantic Search** - Combines vector similarity with keyword matching for optimal results
- *Why hybrid?* Pure semantic search may miss exact statutory references (e.g., "IPC 379"), while hybrid scoring balances semantic relevance with legal keyword precision
-  **NLP Extraction** - Auto-extracts key facts, issues, and arguments from case text
-  **Citation Detection** - Identifies IPC sections, CrPC, Evidence Act, Constitution articles with clickable links
-  **Similar Cases** - Finds related precedents using cosine similarity on 384-dim embeddings
-  **Advanced Filters** - Search by category, date range, court, judge
- **User System** - Authentication, search history, bookmarks
-  **Smart Caching** - Fast repeated searches with in-memory cache

---

## Tech Stack

**Backend:** Python 3.11, Flask 3.0, PostgreSQL 15  
**AI/ML:** Sentence Transformers (all-MiniLM-L6-v2), NumPy  
**Frontend:** HTML5/CSS3/JavaScript, Bootstrap 5  
**Deployment:** ngrok tunnel (local), optimized for cloud deployment

---

## Database Schema

```sql
-- Main cases table with vector embeddings
CREATE TABLE cases (
    id SERIAL PRIMARY KEY,
    case_number VARCHAR(100) UNIQUE NOT NULL,
    title TEXT NOT NULL,
    parties TEXT,
    description TEXT NOT NULL,
    category VARCHAR(50),
    court VARCHAR(100),
    judge VARCHAR(200),
    judgment_date DATE,
    citation TEXT,
    statute_involved TEXT,
    embedding TEXT,  -- AI embedding for semantic search (384-dim, stored as text)
    created_at TIMESTAMP DEFAULT NOW()
);

-- Users with authentication
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    password VARCHAR(255),  -- bcrypt hashed
    created_at TIMESTAMP DEFAULT NOW()
);

-- Search history tracking
CREATE TABLE user_searches (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    query TEXT NOT NULL,
    results_count INTEGER,
    search_timestamp TIMESTAMP DEFAULT NOW()
);

-- Bookmarks
CREATE TABLE user_bookmarks (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    case_number VARCHAR(100) REFERENCES cases(case_number),
    bookmarked_at TIMESTAMP DEFAULT NOW()
);
```

---

## 🚀 Installation & Setup

### **Prerequisites**
- Python 3.11+
- PostgreSQL 15+ with pgvector extension
- Git

### **Local Development**

1. **Clone the repository**
```bash
git clone https://github.com/YOUR_USERNAME/legal-case-dbms.git
cd legal-case-dbms
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up PostgreSQL database**
```bash
# Create database
psql -U postgres
CREATE DATABASE legal_search;

# Run setup script
python setup_auth_legal_search.py
```

4. **Configure environment variables**
```bash
# Create .env file
cp .env.example .env

# Edit .env with your credentials:
DB_NAME=legal_search
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
SECRET_KEY=your-secret-key
```

5. **Import case data (2,160 cases)**
```bash
python recreate_database.py
```

6. **Generate embeddings**
```bash
python embed_cases.py
```

7. **Run the application**
```bash
python api.py
```

8. **Access the app**
- Frontend: `http://127.0.0.1:5000/DBMS%20UI/index.html`
- API: `http://127.0.0.1:5000/api/stats`

---

## 📡 API Documentation

### **Search Endpoint**
```http
GET /search?query=theft&category=criminal&limit=20
```

**Response:**
```json
{
  "results": [
    {
      "case_number": "2018-001",
      "title": "State v. Kumar",
      "parties": "State of Delhi v. Rajesh Kumar",
      "description": "Case involving theft under IPC Section 379...",
      "category": "criminal",
      "score": 0.92,
      "relevance_reason": "High semantic match + keyword bonus"
    }
  ],
  "total": 15,
  "query_time": 0.234
}
```

### **Key Facts Extraction**
```http
GET /api/extract-key-facts/2018-001
```

**Response:**
```json
{
  "facts": [
    "Accused charged with theft of mobile phone",
    "Incident occurred on March 15, 2018"
  ],
  "issues": [
    "Whether the accused committed theft",
    "Whether prosecution proved guilt beyond reasonable doubt"
  ],
  "legal_provisions": ["IPC Section 379", "Evidence Act Section 27"]
}
```

### **Citation Extraction**
```http
GET /api/extract-citations/2018-001
```

**Response:**
```json
{
  "ipc_sections": ["Section 379 IPC", "Section 411 IPC"],
  "crpc_sections": ["Section 161 CrPC"],
  "evidence_act": ["Section 27 of Evidence Act"],
  "case_citations": ["State of Punjab v. Baldev Singh (1999)"]
}
```

### **Similar Cases (AI)**
```http
GET /api/similar-cases/2018-001?limit=5
```

**Response:**
```json
{
  "similar_cases": [
    {
      "case_number": "2019-045",
      "title": "State v. Sharma",
      "similarity": 87,
      "category": "criminal"
    }
  ]
}
```

---

## 📊 Project Structure

```
legal-case-dbms/
├── api.py                      # Main Flask application (1950+ lines)
├── requirements.txt            # Python dependencies
├── Procfile                    # Production server config
├── runtime.txt                 # Python version
├── DEPLOYMENT.md              # Deployment guide
├── TECHNICAL_DOCS.md          # Technical documentation
│
├── DBMS UI/                   # Frontend application
│   ├── index.html             # Main search page (817 lines)
│   ├── case-details.html      # Case details with AI features (900+ lines)
│   ├── login.html             # Authentication (584 lines)
│   ├── signup.html            # User registration
│   ├── browse.html            # Browse by category
│   ├── admin-dashboard.html   # Admin analytics
│   └── profile.html           # User profile
│
├── embed_cases.py             # Generate AI embeddings
├── recreate_database.py       # Database setup script
├── scrape_indian_kanoon.py    # Data scraper
├── populate_years.py          # Year data population
└── setup_auth_legal_search.py # Authentication setup
```

---

## 🎨 Features Showcase

### **1. Intelligent Search**
- Natural language queries: "cases involving theft of mobile phones"
- Category filtering: Criminal, Civil, Constitutional, Tax, etc.
- Date range filtering
- Real-time search suggestions

### **2. Case Details Page**
- **Key Facts Section** - Auto-extracted facts, issues, arguments
- **Legal Citations** - Clickable badges for IPC, CrPC, Evidence Act
- **Related Precedents** - AI-powered similar case recommendations
- **Network Analysis** - Visual representation of case connections

### **3. User Dashboard**
- Search history with timestamps
- Bookmarked cases
- Recent activity feed
- Personalized recommendations

### **4. Admin Panel**
- Total cases, users, searches analytics
- Category distribution charts
- Popular search terms
- System health monitoring

---

## 🔒 Security Features

- ✅ bcrypt password hashing (cost factor 12)
- ✅ SQL injection prevention (parameterized queries)
- ✅ CORS configuration for API security
- ✅ Environment variable management
- ✅ Session management with secure cookies

---

## 🚀 Deployment

**Current Setup: ngrok Tunnel (Local)**

1. Start Flask backend:
```bash
python api.py
```

2. Start ngrok tunnel:
```bash
ngrok http 5000
```

3. Share the ngrok HTTPS URL!

**Note:** Link is active only when your laptop is running. Perfect for demos, interviews, and resume links. For 24/7 deployment, consider AWS EC2, Railway, or Render.

---

## 📈 Performance Metrics

- **Search Speed:** ~0.2-0.5 seconds for semantic search
- **Database Size:** 2,160 Indian legal cases with 384-dim embeddings
- **Citation Detection:** Regex-based pattern matching for IPC, CrPC, Evidence Act, Constitution
- **API Response Time:** <500ms average (with caching)
- **Model:** all-MiniLM-L6-v2 (80MB, optimized for speed)

---

## ⚠️ Current Limitations

- **Citation extraction** uses regex patterns (not ML-based), may miss complex references
- **No reranking** with cross-encoders (using single-stage retrieval)
- **No OCR support** for scanned PDF judgments
- **Embeddings stored as text** (pgvector extension optional)
- **Local deployment only** (ngrok-based, not 24/7)

---

## 🛠️ Future Enhancements

- [ ] OAuth 2.0 integration (Google/Microsoft login)
- [ ] Document upload and OCR for case PDFs
- [ ] Cross-encoder reranking for improved relevance
- [ ] Export search results to PDF/Excel
- [ ] Mobile application (React Native)
- [ ] Multi-language support (Hindi, Tamil, etc.)
- [ ] Integration with more legal databases
- [ ] GraphQL API

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---
## 🙏 Acknowledgments

- **Sentence Transformers** - For powerful semantic embeddings
- **Indian Kanoon** - Legal case data source
- **PostgreSQL** - Robust database system
- **Flask** - Lightweight web framework

---

## 📸 Screenshots

### Main Search Interface
*Coming Soon *

### Case Details with AI Features
*Coming Soon*

### Admin Dashboard
*Coming Soon *

---


</div>
````
    title TEXT,
    parties TEXT,
    description TEXT,
    embedding VECTOR(384),
    category VARCHAR(50)
);
```

### Step 2: Install Dependencies

```bash
pip install flask flask-cors psycopg2-binary sentence-transformers pgvector numpy pandas
```

### Step 3: Configure Database Connection

Update database credentials in `api.py`:

```python
conn = psycopg2.connect(
    dbname="legal_search",
    user="postgres",
    password="your_password",  # Update this
    host="localhost",
    port="5432"
)
```

### Step 4: Populate Database

```bash
# Run the data import and embedding generation script
python update_embeddings.py
```

This will:
- Load 2,160 real Indian legal cases from Indian Kanoon data
- Generate 384-dim AI embeddings for each case using all-MiniLM-L6-v2
- Populate the database with structured case data

### Step 5: Start the API Server

```bash
python api.py
```

Server will start at `http://localhost:5000`

### Step 6: Open the Frontend

Open `DBMS UI/index.html` in your browser

## 📡 API Endpoints

### Search Cases
```
GET /search?query=your_search_query
```

**Example:**
```bash
curl "http://localhost:5000/search?query=theft"
```

**Response:**
```json
[
  {
    "case_number": "CASE-000123-2023",
    "title": "State vs. John Doe",
    "parties": "Complainant vs. Accused",
    "description": "Case description...",
    "score": 89.5
  }
]
```

### Get Case Details
```
GET /case/<case_number>
```

## Features

### 1. Semantic Search
- Understands meaning, not just keywords
- "car theft" matches "automobile stolen", "vehicle burglary"
- Uses AI embeddings for context-aware search

### 2. Hybrid Scoring
- Combines keyword matching (25% bonus)
- Vector similarity (0-100% base score)
- Results sorted by relevance

### 3. Browse by Category
- Criminal Law (Theft, Murder, Assault, etc.)
- Civil Law (Contracts, Property Disputes)
- Family Law (Divorce, Custody)
- Corporate Law
- Tax Law
- And more...

### 4. Advanced Results
- Relevance score for each result
- Highlighted matches
- Case details view
- Responsive design

## How It Works

1. **User Query**: User enters search like "vehicle theft at night"
2. **AI Embedding**: Query converted to 384-dimensional vector
3. **Hybrid Search**:
   - Keyword search finds exact matches
   - Vector search finds semantically similar cases
4. **Scoring**: Combined score from both methods
5. **Results**: Top 20 most relevant cases returned

## Technical Details

### Vector Embeddings
- Model: `all-MiniLM-L6-v2`
- Dimensions: 384
- Speed: Fast inference, no GPU needed
- Accuracy: High quality semantic understanding

### Search Algorithm
```python
# Keyword bonus: +25 points for exact description match
# Semantic score: Cosine similarity * 100
# Final score = Semantic score + Keyword bonus (max 100)
```

### Performance
- Search latency: < 500ms for 47K cases
- Handles concurrent requests
- Efficient vector indexing

## Project Structure

```
dbms_proj/
├── api.py                      # Flask API server
├── embed_cases.py              # Data generation & embedding
├── test_api.py                 # API testing script
├── DBMS UI/                    # Frontend
│   ├── index.html             # Search interface
│   ├── browse.html            # Category browsing
│   └── case-details.html      # Case details view
├── archive (2)/                # Data source (CSV)
└── README.md
```

## Future Deployment Options

For 24/7 availability:
- **AWS EC2** (t2.micro free tier, 1GB RAM)
- **Railway** (requires image optimization)
- **Render** (paid tier for AI models)
- **ngrok Pro** ($8/month for permanent URL)

## Learning Outcomes

This project demonstrates:
- Full-stack development (Python, PostgreSQL, HTML/CSS/JS)
- AI/ML integration (embeddings, similarity search)
- Modern database techniques (vector search, pgvector)
- RESTful API design
- Semantic search algorithms
- Data engineering (ETL pipeline)

## Troubleshooting

**Issue: "AI model not loaded"**
```bash
pip install sentence-transformers torch
```

**Issue: "Database connection failed"**
- Check PostgreSQL is running
- Verify credentials in api.py
- Ensure database exists

**Issue: "pgvector not found"**
```bash
# pgvector is optional - app has fallback using NumPy
# To enable pgvector (optional):
CREATE EXTENSION vector;
```

---

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---
## 👤 Author

**Nandini Padavala**  
GitHub: [@nanddiniiiii](https://github.com/nanddiniiiii) | LinkedIn: [Nandini Padavala](https://www.linkedin.com/in/nandini-padavala-299893352/)

---

## 🙏 Acknowledgments

- **Sentence Transformers** - Semantic embeddings
- **Indian Kanoon** - Legal case data
- **PostgreSQL & Flask** - Core infrastructure

---

<div align="center">

[⬆ Back to Top](#-legal-search-pro---ai-powered-case-database)

</div>
````
