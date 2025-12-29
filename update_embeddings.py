"""
Update embeddings for existing cases in database
Changes from 768-dim (all-mpnet-base-v2) to 384-dim (all-MiniLM-L6-v2)
KEEPS ALL EXISTING DATA - only updates embedding column
"""
import psycopg2
from sentence_transformers import SentenceTransformer
import numpy as np
from tqdm import tqdm

print("=== UPDATING EMBEDDINGS FOR EXISTING CASES ===\n")

# Load the NEW model (384-dim)
print("Loading all-MiniLM-L6-v2 model (384-dim)...")
model = SentenceTransformer('all-MiniLM-L6-v2')
print("✅ Model loaded\n")

# Connect to database
conn = psycopg2.connect(
    dbname="legal_search",
    user="postgres",
    password="12345",
    host="localhost",
    port="5432"
)
cur = conn.cursor()

# Get all cases
print("Fetching all cases from database...")
cur.execute("SELECT case_number, title, description FROM cases ORDER BY case_number;")
all_cases = cur.fetchall()
print(f"✅ Found {len(all_cases)} cases\n")

print("Generating new 384-dim embeddings...\n")
updated = 0
failed = 0

for case_number, title, description in tqdm(all_cases, desc="Updating embeddings"):
    try:
        # Combine title and description for embedding
        text = f"{title or ''} {description or ''}"
        
        # Generate new 384-dim embedding
        embedding = model.encode(text)
        embedding_list = embedding.tolist()
        
        # Update the embedding in database
        cur.execute(
            "UPDATE cases SET embedding = %s WHERE case_number = %s;",
            (str(embedding_list), case_number)
        )
        updated += 1
        
        # Commit every 100 cases
        if updated % 100 == 0:
            conn.commit()
    except Exception as e:
        print(f"\n❌ Failed for case {case_number}: {e}")
        failed += 1

# Final commit
conn.commit()
cur.close()
conn.close()

print(f"\n{'='*50}")
print(f"✅ COMPLETED!")
print(f"Updated: {updated} cases")
print(f"Failed: {failed} cases")
print(f"All embeddings are now 384-dimensional")
print(f"{'='*50}")
