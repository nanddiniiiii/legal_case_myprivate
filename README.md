# Legal Case Retrieval System 

🚀 **AI-Powered Semantic Search for Legal Cases**

## 📋 Project Overview

A full-stack legal case search system that uses AI-powered semantic search with PostgreSQL vector embeddings to search through 47,400+ legal cases using natural language queries.

### 🎯 Key Features

- **Semantic Search**: Uses sentence transformers (all-MiniLM-L6-v2) to understand query meaning, not just keywords
- **Hybrid Search**: Combines keyword matching with vector similarity for optimal results
- **PostgreSQL + pgvector**: Efficient vector storage and similarity search
- **47,400+ Legal Cases**: Realistic case descriptions across 15+ categories
- **Modern UI**: Clean, responsive interface with dark mode

## 🏗️ Tech Stack

**Backend:**
- Python 3.8+
- Flask (REST API)
- PostgreSQL 12+ with pgvector extension
- sentence-transformers (AI embeddings)

**Frontend:**
- HTML5, CSS3, JavaScript
- Bootstrap 5
- Font Awesome icons

**AI/ML:**
- Sentence Transformers (all-MiniLM-L6-v2 model)
- 384-dimensional embeddings
- Cosine similarity for semantic matching

## 🗄️ Database Schema

```sql
CREATE TABLE cases (
    id SERIAL PRIMARY KEY,
    case_number VARCHAR(50) UNIQUE,
    title TEXT,                    -- Petitioner name
    parties TEXT,                  -- Respondent name
    description TEXT,              -- Full case description
    embedding VECTOR(384),         -- AI embedding
    category VARCHAR(50)           -- Case category
);
```

## 🚀 Local Setup

### Prerequisites

1. Python 3.8 or higher
2. PostgreSQL 12+ installed
3. pip (Python package manager)

### Step 1: Database Setup

```bash
# Create database
psql -U postgres
CREATE DATABASE legal_search;
\c legal_search

# Enable pgvector extension
CREATE EXTENSION vector;

# Create table
CREATE TABLE cases (
    id SERIAL PRIMARY KEY,
    case_number VARCHAR(50) UNIQUE,
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
# Run the data generation script
python embed_cases.py
```

This will:
- Generate realistic legal case descriptions
- Create AI embeddings for each case
- Populate the database with 47,400+ cases

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

## 🎨 Features

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

## 📊 How It Works

1. **User Query**: User enters search like "vehicle theft at night"
2. **AI Embedding**: Query converted to 384-dimensional vector
3. **Hybrid Search**:
   - Keyword search finds exact matches
   - Vector search finds semantically similar cases
4. **Scoring**: Combined score from both methods
5. **Results**: Top 20 most relevant cases returned

## 🔧 Technical Details

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

## 📁 Project Structure

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

## 🌐 Deployment

### Option 1: Render.com + Neon.tech (Free)

**Backend (Render.com):**
1. Create `requirements.txt`
2. Deploy Flask app
3. Add environment variables

**Database (Neon.tech):**
1. Create PostgreSQL instance
2. Enable pgvector extension
3. Import data

**Frontend (GitHub Pages):**
1. Push to GitHub
2. Enable GitHub Pages
3. Update API URL

### Option 2: AWS/Cloud
- EC2/Elastic Beanstalk for API
- RDS PostgreSQL with pgvector
- S3 + CloudFront for frontend

## 🎓 Learning Outcomes

This project demonstrates:
- Full-stack development (Python, PostgreSQL, HTML/CSS/JS)
- AI/ML integration (embeddings, similarity search)
- Modern database techniques (vector search, pgvector)
- RESTful API design
- Semantic search algorithms
- Data engineering (ETL pipeline)

## 🐛 Troubleshooting

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
# Install pgvector extension in PostgreSQL
CREATE EXTENSION vector;
```

## 📈 Future Improvements

- [ ] Add user authentication
- [ ] Implement caching (Redis)
- [ ] Add pagination for results
- [ ] Export results to PDF
- [ ] Case comparison feature
- [ ] Citation graph visualization
- [ ] Advanced filters (date, court, etc.)
- [ ] Real-time search suggestions

## 🤝 Contributing

This is a personal DBMS project. Feedback and suggestions are welcome!

## 📄 License

This project is for educational purposes.

## 👨‍💻 Author

**Your Name**
- GitHub: [@your-username](https://github.com/your-username)
- LinkedIn: [Your LinkedIn](https://linkedin.com/in/your-profile)

## 🙏 Acknowledgments

- Sentence Transformers library
- pgvector PostgreSQL extension
- Legal case data sources
- Kaggle legal datasets

---

⭐ **Star this repo if you find it helpful!**
