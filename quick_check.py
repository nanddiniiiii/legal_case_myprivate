import psycopg2

conn = psycopg2.connect(
    dbname="legal_search",
    user="postgres",
    password="12345",
    host="localhost",
    port="5432"
)
cur = conn.cursor()

# Check if embeddings exist
cur.execute("SELECT case_number, embedding IS NOT NULL as has_embedding FROM cases LIMIT 5;")
results = cur.fetchall()

print("=== EMBEDDING CHECK ===")
for case_num, has_emb in results:
    status = "✅ HAS embedding" if has_emb else "❌ NO embedding"
    print(f"{case_num}: {status}")

# Count cases with/without embeddings
cur.execute("SELECT COUNT(*) FROM cases WHERE embedding IS NOT NULL;")
with_emb = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM cases WHERE embedding IS NULL;")
without_emb = cur.fetchone()[0]

print(f"\nTotal: {with_emb} with embeddings, {without_emb} without")
print("\n⚠️ If embeddings are missing, run: python embed_cases.py")

cur.close()
conn.close()
