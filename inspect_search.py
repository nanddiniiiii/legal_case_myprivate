import psycopg2
import numpy as np
from sentence_transformers import SentenceTransformer

# Load the same model as your API
model = SentenceTransformer('all-MiniLM-L6-v2')

# Connect to database
conn = psycopg2.connect(
    dbname="postgres", 
    user="postgres", 
    password="12345", 
    host="localhost", 
    port="5432"
)

cur = conn.cursor()

# Test search for "theft"
query = "theft"
query_embedding = model.encode(query)

print(f"=== DEBUGGING SEARCH FOR '{query}' ===\n")

# Get some cases that contain "theft" in title or text
cur.execute("""
    SELECT caseid, title, judgment_text, embedding
    FROM cases 
    WHERE LOWER(title) LIKE %s OR LOWER(judgment_text) LIKE %s
    LIMIT 5
""", (f'%{query.lower()}%', f'%{query.lower()}%'))

theft_cases = cur.fetchall()

print(f"Found {len(theft_cases)} cases containing '{query}':\n")

for caseid, title, text, embedding in theft_cases:
    # Calculate real similarity
    case_embedding = np.array(embedding)
    
    # Calculate cosine similarity
    query_norm = np.linalg.norm(query_embedding)
    case_norm = np.linalg.norm(case_embedding)
    
    if case_norm > 0 and query_norm > 0:
        cosine_sim = np.dot(query_embedding, case_embedding) / (query_norm * case_norm)
        similarity_percent = cosine_sim * 100
    else:
        similarity_percent = 0
    
    print(f"Case {caseid}: {similarity_percent:.2f}% similarity")
    print(f"Title: {title}")
    print(f"Content preview: {text[:200]}...")
    print(f"Contains 'theft': {'theft' in text.lower()}")
    print("-" * 60)

# Now test the top semantic results
print(f"\n=== TOP SEMANTIC MATCHES FOR '{query}' ===\n")

cur.execute("""
    SELECT caseid, title, judgment_text, embedding <=> %s AS distance
    FROM cases
    ORDER BY distance
    LIMIT 5
""", (query_embedding,))

semantic_results = cur.fetchall()

for caseid, title, text, distance in semantic_results:
    similarity_percent = (1 - distance) * 100  # Convert distance to similarity
    print(f"Case {caseid}: {similarity_percent:.2f}% similarity")
    print(f"Title: {title}")
    print(f"Content preview: {text[:200]}...")
    print(f"Contains 'theft': {'theft' in text.lower()}")
    print("-" * 60)

conn.close()