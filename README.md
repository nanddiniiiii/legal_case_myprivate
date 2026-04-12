# Legal Search Pro - AI-Powered Case Database

> Full-Stack Legal Case Management System with AI-Powered Semantic Search

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0-green.svg)](https://flask.palletsprojects.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)](https://www.postgresql.org/)
[![AI](https://img.shields.io/badge/AI-Sentence_Transformers-orange.svg)](https://www.sbert.net/)

Live Demo: Available on request (ngrok-based deployment)
Contact for live demo URL during interviews

---

## Overview

Legal Search Pro is a full-stack AI-powered legal case database with 2,160 real Indian legal cases from Indian Kanoon. Features semantic search, NLP-based key facts extraction, citation detection, and vector similarity for finding related precedents.

### Key Features

* Hybrid Semantic Search - Combines vector similarity with keyword matching for optimal results
* Why hybrid? Pure semantic search may miss exact statutory references (e.g., "IPC 379"), while hybrid scoring balances semantic relevance with legal keyword precision
* NLP Extraction - Auto-extracts key facts, issues, and arguments from case text
* Citation Detection - Identifies IPC sections, CrPC, Evidence Act, Constitution articles with clickable links
* Similar Cases - Finds related precedents using cosine similarity on 384-dim embeddings
* Advanced Filters - Search by category, date range, court, judge
* User System - Authentication, search history, bookmarks
* Smart Caching - Fast repeated searches with in-memory cache

---

## Tech Stack

Backend: Python 3.11, Flask 3.0, PostgreSQL 15
AI/ML: Sentence Transformers (all-MiniLM-L6-v2), NumPy
Frontend: HTML5/CSS3/JavaScript, Bootstrap 5
Deployment: ngrok tunnel (local), optimized for cloud deployment

---

## Database Schema

```sql
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
    embedding TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    password VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE user_searches (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    query TEXT NOT NULL,
    results_count INTEGER,
    search_timestamp TIMESTAMP DEFAULT NOW()
);

CREATE TABLE user_bookmarks (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    case_number VARCHAR(100) REFERENCES cases(case_number),
    bookmarked_at TIMESTAMP DEFAULT NOW()
);
```

---

## Installation & Setup

### Prerequisites

* Python 3.11+
* PostgreSQL 15+ with pgvector extension
* Git

### Local Development

1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/legal-case-dbms.git
cd legal-case-dbms
```

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Set up PostgreSQL database

```bash
psql -U postgres
CREATE DATABASE legal_search;

python setup_auth_legal_search.py
```

4. Configure environment variables

```bash
cp .env.example .env
```

Edit:

```
DB_NAME=legal_search
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
SECRET_KEY=your-secret-key
```

5. Import case data

```bash
python recreate_database.py
```

6. Generate embeddings

```bash
python embed_cases.py
```

7. Run the application

```bash
python api.py
```

8. Access the app

* Frontend: http://127.0.0.1:5000/DBMS%20UI/index.html
* API: http://127.0.0.1:5000/api/stats

---

## API Documentation

### Search Endpoint

```
GET /search?query=theft&category=criminal&limit=20
```

### Key Facts Extraction

```
GET /api/extract-key-facts/2018-001
```

### Citation Extraction

```
GET /api/extract-citations/2018-001
```

### Similar Cases

```
GET /api/similar-cases/2018-001?limit=5
```

---

## Project Structure

```
legal-case-dbms/
├── api.py
├── requirements.txt
├── Procfile
├── runtime.txt
├── DEPLOYMENT.md
├── TECHNICAL_DOCS.md
├── DBMS UI/
├── embed_cases.py
├── recreate_database.py
├── scrape_indian_kanoon.py
├── populate_years.py
└── setup_auth_legal_search.py
```

---

## Features Showcase

### Intelligent Search

* Natural language queries
* Category filtering
* Date range filtering

### Case Details Page

* Key facts extraction
* Legal citations
* Similar cases

### User Dashboard

* Search history
* Bookmarks
* Activity feed

### Admin Panel

* Analytics
* Category stats
* System monitoring

---

## Security Features

* bcrypt password hashing
* SQL injection prevention
* CORS configuration
* Environment variables
* Secure sessions

---

## Deployment

Current Setup: ngrok tunnel

```bash
python api.py
ngrok http 5000
```

---

## Performance Metrics

* Search Speed: ~0.2-0.5 seconds
* Database Size: 2,160 cases
* API Response: <500ms

---

## Limitations

* Regex-based citation extraction
* No cross-encoder reranking
* No OCR support
* Local deployment only

---

## Future Enhancements

* OAuth login
* OCR support
* Reranking
* Export features
* Mobile app
* Multi-language

---

## Contributing

1. Fork
2. Branch
3. Commit
4. Push
5. PR

---

## Author

Nandini Padavala
GitHub: https://github.com/nanddiniiiii
LinkedIn: https://www.linkedin.com/in/nandini-padavala-299893352/

---

## Acknowledgments

* Sentence Transformers
* Indian Kanoon
* PostgreSQL
* Flask

---
