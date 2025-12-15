# ==============================================================================
# IMPORT NECESSARY LIBRARIES
# ==============================================================================
from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
from sentence_transformers import SentenceTransformer
from pgvector.psycopg2 import register_vector
import numpy as np
import traceback
import random # Keep random for shuffling ties
import ast
from datetime import datetime, timezone

# ==============================================================================
# --- CONFIGURATION & AI MODEL LOADING ---
# ==============================================================================
app = Flask(__name__)
CORS(app)

print("--- Loading AI model for semantic search ---")
try:
    model = SentenceTransformer('all-MiniLM-L6-v2')
    print("✅ AI model loaded successfully.")
except Exception as e:
    print(f"❌ CRITICAL ERROR: Could not load SentenceTransformer model. Error: {e}")
    model = None

# ==============================================================================
# --- DATABASE CONNECTION FUNCTION ---
# ==============================================================================
def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            dbname="legal_search", # Ensure this matches your DB name
            user="postgres",       # Ensure this matches your DB user
            password="12345",      # Ensure this matches your DB password
            host="localhost",      # Ensure this matches your DB host
            port="5432"            # Ensure this matches your DB port
        )
        return conn
    except psycopg2.OperationalError as e:
        print(f"❌ DATABASE CONNECTION ERROR: {e}")
        raise e

# ==============================================================================
# --- ENHANCED SEARCH ENDPOINT (WITH DIVERSIFICATION & LARGER POOL) ---
# ==============================================================================
@app.route('/search', methods=['GET'])
def search_cases():
    """
    Enhanced hybrid search prioritizing description diversity in results.
    Fetches a larger pool initially.
    """
    print("\n\n--- SERVER LOG: New Diversified Search Request Received ---")
    query = request.args.get('query', '').strip()
    print(f"--- SERVER LOG: Received query: '{query}' ---")

    if not query:
        print("--- SERVER LOG: ERROR - Query parameter is empty. ---")
        return jsonify({"error": "Query parameter is required."}), 400
    if not model:
        print("--- SERVER LOG: CRITICAL ERROR - AI model not loaded. ---")
        return jsonify({"error": "AI model is not available."}), 503

    conn = None
    cur = None
    RESULTS_LIMIT = 20 # How many results to finally return
    # *** INCREASED FETCH POOL SIZE ***
    FETCH_POOL_SIZE = 1000 # Fetch more initially to find diverse descriptions

    try:
        print("--- SERVER LOG: Connecting to database for search... ---")
        conn = get_db_connection()
        register_vector(conn)
        cur = conn.cursor()
        print("--- SERVER LOG: ✅ DB Connection successful. ---")

        print("--- SERVER LOG: Generating query embedding... ---")
        query_embedding = model.encode(query)
        query_embedding_np = np.array(query_embedding, dtype=np.float32)
        print("--- SERVER LOG: ✅ Query embedding generated. ---")

        # --- Keyword Search ---
        print(f"--- SERVER LOG: Performing keyword search (pool size {FETCH_POOL_SIZE})... ---")
        keyword_query = """
            SELECT case_number, title, parties, description, embedding,
                   CASE WHEN LOWER(description) ILIKE LOWER(%s) THEN 25.0
                        WHEN LOWER(title) ILIKE LOWER(%s) THEN 20.0
                        ELSE 0.0 END as keyword_bonus
            FROM cases WHERE LOWER(description) ILIKE LOWER(%s) OR LOWER(title) ILIKE LOWER(%s)
            LIMIT %s;
        """
        search_pattern = f'%{query}%'
        cur.execute(keyword_query, (search_pattern, search_pattern, search_pattern, search_pattern, FETCH_POOL_SIZE))
        keyword_results_raw = cur.fetchall()
        print(f"--- SERVER LOG: Found {len(keyword_results_raw)} potential keyword matches. ---")

        # --- Semantic Search ---
        print(f"--- SERVER LOG: Performing semantic search (pool size {FETCH_POOL_SIZE})... ---")
        semantic_query = """
            SELECT case_number, title, parties, description, embedding, embedding <=> %s AS distance
            FROM cases ORDER BY distance ASC LIMIT %s;
        """
        cur.execute(semantic_query, (query_embedding_np, FETCH_POOL_SIZE))
        semantic_results_raw = cur.fetchall()
        print(f"--- SERVER LOG: Found {len(semantic_results_raw)} potential semantic matches. ---")

        # --- Combine, Deduplicate, Cache Embeddings ---
        print("--- SERVER LOG: Combining results, calculating scores... ---")
        all_results_dict = {}
        processed_embeddings_cache = {}

        def process_embedding(case_num, emb_val):
            # Inner function to handle embedding processing and caching
            if case_num in processed_embeddings_cache: return processed_embeddings_cache[case_num]
            try:
                if isinstance(emb_val, str): np_emb = np.array(ast.literal_eval(emb_val), dtype=np.float32)
                elif isinstance(emb_val, (list, np.ndarray)): np_emb = np.array(emb_val, dtype=np.float32)
                else: np_emb = None
                processed_embeddings_cache[case_num] = np_emb if (np_emb is not None and len(np_emb) > 0) else None
                return processed_embeddings_cache[case_num]
            except Exception as e:
                # print(f"--- SERVER LOG: ⚠️ Warn - Embedding processing error for {case_num}: {e}") # Reduce noise
                processed_embeddings_cache[case_num] = None
                return None

        # Process keyword results
        for kw_row in keyword_results_raw:
            case_number, title, parties, desc, emb_val, bonus = kw_row
            if case_number not in all_results_dict:
                all_results_dict[case_number] = {'title': title, 'parties': parties, 'description': desc, 'keyword_bonus': bonus, 'distance': 2.0}
                process_embedding(case_number, emb_val)

        # Process semantic results
        for sem_row in semantic_results_raw:
            case_number, title, parties, desc, emb_val, distance = sem_row
            distance = float(distance)
            if case_number in all_results_dict:
                all_results_dict[case_number]['distance'] = min(all_results_dict[case_number].get('distance', 2.0), distance)
            else:
                 all_results_dict[case_number] = {'title': title, 'parties': parties, 'description': desc, 'keyword_bonus': 0.0, 'distance': distance}
            if case_number not in processed_embeddings_cache:
                process_embedding(case_number, emb_val)

        if not all_results_dict:
            print("--- SERVER LOG: ✅ No combined results found. ---")
            return jsonify([])

        # --- Calculate Final Scores ---
        scored_results_list = []
        query_norm = np.linalg.norm(query_embedding_np)
        if query_norm < 1e-6: query_norm = 1.0

        for case_number, data in all_results_dict.items():
            case_embedding_np = processed_embeddings_cache.get(case_number)
            if case_embedding_np is None: continue

            case_norm = np.linalg.norm(case_embedding_np)
            if case_norm < 1e-6: case_norm = 1.0

            base_score = 0.0
            db_distance = data.get('distance', 2.0)
            if db_distance <= 1.0: # Use pgvector distance if valid
                cosine_similarity = 1.0 - db_distance
                base_score = max(0.0, cosine_similarity * 100.0)
            else: # Fallback: Calculate manually
                cosine_sim = np.dot(query_embedding_np, case_embedding_np) / (query_norm * case_norm)
                base_score = max(0.0, float(cosine_sim) * 100.0)

            final_score = min(100.0, base_score + float(data.get('keyword_bonus', 0.0)))

            scored_results_list.append({
                'case_number': str(case_number),
                'title': str(data.get('title', 'Untitled Case')),
                'parties': str(data.get('parties', 'Unknown vs Unknown')),
                'description': str(data.get('description', 'No content available.')),
                'score': round(final_score, 1)
            })

        print(f"--- SERVER LOG: ✅ Scored {len(scored_results_list)} unique potential results from pool. ---")

        # --- Prioritize Description Diversity ---
        print("--- SERVER LOG: Selecting top results with description diversity... ---")
        scored_results_list.sort(key=lambda x: x.get('score', 0), reverse=True)

        diverse_top_results = []
        seen_description_keys = set()
        description_key_length = 500 # Use first N chars to check uniqueness

        for result in scored_results_list:
            if len(diverse_top_results) >= RESULTS_LIMIT: break
            desc_text = result.get('description', '')
            desc_key = desc_text[:description_key_length]
            if desc_key not in seen_description_keys:
                diverse_top_results.append(result)
                seen_description_keys.add(desc_key)

        # Fill remaining spots if needed
        if len(diverse_top_results) < RESULTS_LIMIT:
            print(f"--- SERVER LOG: Only found {len(diverse_top_results)} unique descriptions. Filling remaining spots... ---")
            remaining_needed = RESULTS_LIMIT - len(diverse_top_results)
            included_case_numbers = {res['case_number'] for res in diverse_top_results}
            for result in scored_results_list:
                if remaining_needed <= 0: break
                if result['case_number'] not in included_case_numbers:
                    diverse_top_results.append(result)
                    included_case_numbers.add(result['case_number'])
                    remaining_needed -= 1

        print(f"--- SERVER LOG: ✅ Returning {len(diverse_top_results)} results prioritizing diversity. ---")

        # Log top results
        for i, result in enumerate(diverse_top_results[:5]):
            print(f"--- SERVER LOG: Top {i+1}: '{str(result.get('title','N/A'))[:40]}...' - Score: {result.get('score','N/A')}% ---")

        # --- Track Search ---
        try:
            user_email = request.headers.get('X-User-Email', 'anonymous')
            if table_exists(cur, 'user_searches'):
                cur.execute("""
                    INSERT INTO user_searches (user_email, query, results_count, searched_at)
                    VALUES (%s, %s, %s, %s);
                """, (user_email, query, len(diverse_top_results), datetime.now(timezone.utc)))
                conn.commit()
                print(f"--- SERVER LOG: 📊 Tracked search for user: {user_email} ---")
            else:
                print("--- SERVER LOG: ⚠️ Skipping search tracking ('user_searches' table not found). ---")
        except Exception as track_error:
            conn.rollback()
            print(f"--- SERVER LOG: ⚠️ Error tracking search: {track_error} ---")

        return jsonify(diverse_top_results)

    except psycopg2.OperationalError as db_err:
         print(f"--- SERVER LOG: ❌ DATABASE CONNECTION FAILED during search: {db_err} ---")
         traceback.print_exc()
         return jsonify({"error": "Database connection failed. Please try again later."}), 503
    except Exception as e:
        print(f"--- SERVER LOG: ❌ UNEXPECTED ERROR during search: {e} ---")
        traceback.print_exc()
        if conn: conn.rollback()
        return jsonify({"error": f"An internal server error occurred: {str(e)}"}), 500
    finally:
        if conn:
            if cur: cur.close()
            conn.close()
            print("--- SERVER LOG: Database connection closed (search). ---")


# ==============================================================================
# --- BROWSE BY CATEGORY ENDPOINT ---
# ==============================================================================
# In api.py

# ... (Keep imports, app setup, model loading, get_db_connection, search_cases, etc.) ...

# ==============================================================================
# --- BROWSE BY CATEGORY ENDPOINT (MODIFIED TO INCLUDE CASE_NUMBER) ---
# ==============================================================================
@app.route('/browse', methods=['GET'])
def browse_cases():
    """
    Handles browsing requests for specific categories.
    Returns case_number, title, and description.
    """
    category_id = request.args.get('category', '').strip() # e.g., 'criminal_law'
    category_name_display = request.args.get('name', category_id) # For logging
    print(f"\n\n--- SERVER LOG: Browse Request Received for category ID: '{category_id}' (Display Name: '{category_name_display}') ---")

    if not category_id:
         return jsonify({"error": "Category parameter is required."}), 400

    # Ensure this mapping aligns with categories produced by your generator
    category_mapping = {
        'supreme_court': 'constitutional', 'high_courts': 'civil', 'criminal_law': 'criminal',
        'civil_law': 'civil', 'corporate_law': 'commercial', 'tax_law': 'tax', 'labor_law': 'labour',
        'family_law': 'family', 'constitutional_law': 'constitutional', 'property_dispute': 'property',
        'banking': 'banking', 'motor_accident': 'mac', 'ip': 'ip', 'election': 'election',
        'ibc': 'ibc', 'arbitration': 'arbitration', 'consumer': 'consumer', 'service': 'service'
    }
    db_category_name = category_mapping.get(category_id)
    if not db_category_name:
        db_category_name = category_id.replace('_', ' ').lower()
        print(f"--- SERVER LOG: ⚠️ Category ID '{category_id}' not mapped. Falling back to: '{db_category_name}' ---")

    conn = None; cur = None
    try:
        print(f"--- SERVER LOG: Querying DB for category: '{db_category_name}' ---")
        conn = get_db_connection(); cur = conn.cursor()
        if not table_exists(cur, 'cases'): raise psycopg2.errors.UndefinedTable("Table 'cases' needed for browse.")

        # *** MODIFIED QUERY: Select case_number ***
        query = """
            SELECT case_number, title, description as judgment_text
            FROM cases
            WHERE LOWER(category) = LOWER(%s)
            ORDER BY RANDOM()
            LIMIT 50;
        """
        cur.execute(query, (db_category_name,))
        results_raw = cur.fetchall()
        count = len(results_raw)
        print(f"--- SERVER LOG: ✅ Found {count} cases for category '{db_category_name}'. ---")

        # *** MODIFIED RESPONSE: Include case_number ***
        final_results = [
            {'case_number': str(row[0] or ''), 'title': str(row[1] or ''), 'judgment_text': str(row[2] or '')}
            for row in results_raw
        ]
        return jsonify(final_results)

    except psycopg2.errors.UndefinedTable as e: print(f"--- SERVER LOG: ❌ SETUP ERROR - {e} ---"); return jsonify({"error": f"Setup error: {e}"}), 503
    except psycopg2.OperationalError as db_err: print(f"--- SERVER LOG: ❌ DB CONNECTION FAILED browse: {db_err} ---"); return jsonify({"error": "Database error"}), 503
    except Exception as e: print(f"--- SERVER LOG: ❌ ERROR during browse: {e} ---"); traceback.print_exc(); return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            if cur: cur.close()
            conn.close()
            print("--- SERVER LOG: DB connection closed (browse). ---")

# ... (Keep rest of api.py: auth endpoints, case details endpoint, main block) ...

# ==============================================================================
# --- AUTHENTICATION & PROFILE ENDPOINTS ---
# ==============================================================================

# Helper function to check if a table exists
def table_exists(cursor, table_name):
    try:
        cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = %s);", (table_name,))
        return cursor.fetchone()[0]
    except Exception as e:
        print(f"--- SERVER LOG: ⚠️ Error checking if table '{table_name}' exists: {e}")
        return False

@app.route('/register', methods=['POST'])
def register_user():
    conn = None; cur = None
    try:
        data = request.get_json();
        if not data: return jsonify({"error": "Invalid JSON"}), 400
        full_name = data.get('fullName','').strip(); email = data.get('email','').strip(); password = data.get('password','').strip()
        if not all([full_name, email, password]): return jsonify({"error": "Missing required fields"}), 400
        conn = get_db_connection(); cur = conn.cursor()
        if not table_exists(cur, 'users'): raise psycopg2.errors.UndefinedTable("Table 'users' needed for registration.")
        cur.execute("SELECT 1 FROM users WHERE email = %s LIMIT 1;", (email,))
        if cur.fetchone(): return jsonify({"error": "User already exists"}), 409
        cur.execute("INSERT INTO users (name, email, password, created_at) VALUES (%s, %s, %s, %s);", (full_name, email, password, datetime.now(timezone.utc)))
        conn.commit(); print(f"--- SERVER LOG: ✅ Registered: {email} ---"); return jsonify({"message": "User registered"}), 201
    except psycopg2.errors.UndefinedTable as e: print(f"--- SERVER LOG: ❌ SETUP ERROR - {e} ---"); return jsonify({"error": f"Setup error: {e}"}), 503
    except psycopg2.OperationalError as db_err: print(f"--- SERVER LOG: ❌ DB CONNECTION FAILED registration: {db_err} ---"); return jsonify({"error": "Database error"}), 503
    except Exception as e:
        print(f"--- SERVER LOG: ❌ ERROR registration: {e} ---")
        traceback.print_exc()
        if conn:
            conn.rollback()
        return jsonify({"error": f"Registration failed: {str(e)}"}), 500
    finally:
        if conn:
            if cur: cur.close()
            conn.close()

@app.route('/login', methods=['POST'])
def login_user():
    conn = None; cur = None
    try:
        data = request.get_json();
        if not data: return jsonify({"error": "Invalid JSON"}), 400
        email = data.get('email','').strip(); password = data.get('password','').strip()
        if not all([email, password]): return jsonify({"error": "Email/password required"}), 400
        conn = get_db_connection(); cur = conn.cursor()
        if not table_exists(cur, 'users'): raise psycopg2.errors.UndefinedTable("Table 'users' needed for login.")
        cur.execute("SELECT name, email FROM users WHERE email = %s AND password = %s;", (email, password)) # Plain password check!
        user = cur.fetchone()
        if user: print(f"--- SERVER LOG: ✅ Login OK: {email} ---"); return jsonify({"message": "Login successful", "user": {"name": user[0], "email": user[1]}}), 200
        else: print(f"--- SERVER LOG: ⚠️ Login FAILED: {email} ---"); return jsonify({"error": "Invalid credentials"}), 401
    except psycopg2.errors.UndefinedTable as e: print(f"--- SERVER LOG: ❌ SETUP ERROR - {e} ---"); return jsonify({"error": f"Setup error: {e}"}), 503
    except psycopg2.OperationalError as db_err: print(f"--- SERVER LOG: ❌ DB CONNECTION FAILED login: {db_err} ---"); return jsonify({"error": "Database error"}), 503
    except Exception as e:
        print(f"--- SERVER LOG: ❌ ERROR login: {e} ---")
        traceback.print_exc()
        return jsonify({"error": f"Login failed: {str(e)}"}), 500
    finally:
        if conn:
            if cur: cur.close()
            conn.close()

def calculate_time_ago(timestamp):
    if not timestamp: return "Unknown"
    try:
        if timestamp.tzinfo is None: timestamp = timestamp.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc); diff = now - timestamp
        seconds = diff.total_seconds(); days = diff.days
        if days > 1: return f"{days} days ago"
        elif days == 1: return "1 day ago"
        elif seconds >= 3600: hours = int(seconds // 3600); return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif seconds >= 60: minutes = int(seconds // 60); return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else: return "Just now"
    except Exception: return "Unknown time"

@app.route('/recent-searches', methods=['GET'])
def get_recent_searches():
    conn = None; cur = None
    try:
        user_email = request.args.get('email', 'anonymous'); limit = request.args.get('limit', 10, type=int)
        print(f"--- SERVER LOG: Fetching recent searches for: {user_email} ---")
        conn = get_db_connection(); cur = conn.cursor()
        if not table_exists(cur, 'user_searches'): raise psycopg2.errors.UndefinedTable("Table 'user_searches' needed for history.")
        cur.execute("SELECT query, results_count, searched_at FROM user_searches WHERE user_email = %s ORDER BY searched_at DESC LIMIT %s;", (user_email, limit))
        searches = cur.fetchall()
        recent_searches = [{"query": r[0], "results_count": r[1], "timestamp": r[2].isoformat() if r[2] else None, "time_ago": calculate_time_ago(r[2])} for r in searches]
        print(f"--- SERVER LOG: ✅ Found {len(recent_searches)} searches ---"); return jsonify(recent_searches), 200
    except psycopg2.errors.UndefinedTable as e: print(f"--- SERVER LOG: ❌ SETUP ERROR - {e} ---"); return jsonify({"error": f"Setup error: {e}"}), 503
    except psycopg2.OperationalError as db_err: print(f"--- SERVER LOG: ❌ DB CONNECTION FAILED history: {db_err} ---"); return jsonify({"error": "Database error"}), 503
    except Exception as e:
        print(f"--- SERVER LOG: ❌ ERROR fetching history: {e} ---")
        traceback.print_exc()
        return jsonify({"error": f"Could not fetch history: {str(e)}"}), 500
    finally:
        if conn:
            if cur: cur.close()
            conn.close()

@app.route('/user-stats', methods=['GET'])
def get_user_stats():
    conn = None; cur = None
    try:
        user_email = request.args.get('email');
        if not user_email: return jsonify({"error": "Email required"}), 400
        print(f"--- SERVER LOG: Fetching stats for: {user_email} ---")
        conn = get_db_connection(); cur = conn.cursor()
        if not table_exists(cur, 'users'): raise psycopg2.errors.UndefinedTable("Table 'users' needed for stats.")
        if not table_exists(cur, 'user_searches'): raise psycopg2.errors.UndefinedTable("Table 'user_searches' needed for stats.")
        bookmarks_table_exists = table_exists(cur, 'user_bookmarks')
        cur.execute("SELECT name, created_at FROM users WHERE email = %s;", (user_email,))
        user_info = cur.fetchone()
        if not user_info: return jsonify({"error": "User not found"}), 404
        user_name, created_at = user_info
        if created_at and created_at.tzinfo is None: created_at = created_at.replace(tzinfo=timezone.utc)
        days_active = max(1, (datetime.now(timezone.utc) - created_at).days) if created_at else 1
        member_since = created_at.strftime("%B %Y") if created_at else "Unknown"
        cur.execute("SELECT COUNT(*) FROM user_searches WHERE user_email = %s;", (user_email,))
        total_searches = cur.fetchone()[0]
        bookmarks_count = 0
        if bookmarks_table_exists: cur.execute("SELECT COUNT(*) FROM user_bookmarks WHERE user_email = %s;", (user_email,)); bookmarks_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM user_searches WHERE user_email = %s AND results_count > 0;", (user_email,))
        successful_searches = cur.fetchone()[0]
        success_rate = round((successful_searches / total_searches) * 100) if total_searches > 0 else 0
        research_hours = (total_searches * 1) // 60
        print(f"--- SERVER LOG: ✅ Stats fetched for {user_email} ---")
        return jsonify({"name": user_name, "member_since": member_since, "days_active": days_active, "total_searches": total_searches, "bookmarks": bookmarks_count, "research_time": f"{research_hours}h", "success_rate": f"{success_rate}%"}), 200
    except psycopg2.errors.UndefinedTable as e: print(f"--- SERVER LOG: ❌ SETUP ERROR - {e} ---"); return jsonify({"error": f"Setup error: {e}"}), 503
    except psycopg2.OperationalError as db_err: print(f"--- SERVER LOG: ❌ DB CONNECTION FAILED stats: {db_err} ---"); return jsonify({"error": "Database error"}), 503
    except Exception as e:
        print(f"--- SERVER LOG: ❌ ERROR fetching stats: {e} ---")
        traceback.print_exc()
        return jsonify({"error": f"Could not fetch stats: {str(e)}"}), 500
    finally:
        if conn:
            if cur: cur.close()
            conn.close()

@app.route('/update-profile', methods=['POST'])
def update_profile():
    conn = None; cur = None
    try:
        data = request.json;
        if not data: return jsonify({"error": "Invalid JSON"}), 400
        user_email = data.get('email'); new_name = data.get('name')
        if not user_email or not new_name: return jsonify({"error": "Email and name required"}), 400
        print(f"--- SERVER LOG: Updating profile for: {user_email} ---")
        conn = get_db_connection(); cur = conn.cursor()
        if not table_exists(cur, 'users'): raise psycopg2.errors.UndefinedTable("Table 'users' needed for update.")
        cur.execute("UPDATE users SET name = %s WHERE email = %s;", (new_name, user_email))
        if cur.rowcount == 0: return jsonify({"error": "User not found"}), 404
        conn.commit(); print(f"--- SERVER LOG: ✅ Profile updated for {user_email} ---"); return jsonify({"message": "Profile updated"}), 200
    except psycopg2.errors.UndefinedTable as e: print(f"--- SERVER LOG: ❌ SETUP ERROR - {e} ---"); return jsonify({"error": f"Setup error: {e}"}), 503
    except psycopg2.OperationalError as db_err: print(f"--- SERVER LOG: ❌ DB CONNECTION FAILED update profile: {db_err} ---"); return jsonify({"error": "Database error"}), 503
    except Exception as e:
        print(f"--- SERVER LOG: ❌ ERROR updating profile: {e} ---")
        traceback.print_exc()
        if conn:
            conn.rollback()
        return jsonify({"error": f"Profile update failed: {str(e)}"}), 500
    finally:
        if conn:
            if cur: cur.close()
            conn.close()

@app.route('/clear-search-history', methods=['POST'])
def clear_search_history():
    conn = None; cur = None
    try:
        data = request.json;
        if not data: return jsonify({"error": "Invalid JSON"}), 400
        user_email = data.get('email')
        if not user_email: return jsonify({"error": "Email required"}), 400
        print(f"--- SERVER LOG: Clearing history for: {user_email} ---")
        conn = get_db_connection(); cur = conn.cursor()
        if not table_exists(cur, 'user_searches'): raise psycopg2.errors.UndefinedTable("Table 'user_searches' needed for clear.")
        cur.execute("DELETE FROM user_searches WHERE user_email = %s;", (user_email,))
        deleted_count = cur.rowcount; conn.commit()
        print(f"--- SERVER LOG: ✅ Cleared {deleted_count} records ---"); return jsonify({"message": "History cleared", "deleted_count": deleted_count}), 200
    except psycopg2.errors.UndefinedTable as e: print(f"--- SERVER LOG: ❌ SETUP ERROR - {e} ---"); return jsonify({"error": f"Setup error: {e}"}), 503
    except psycopg2.OperationalError as db_err: print(f"--- SERVER LOG: ❌ DB CONNECTION FAILED clearing history: {db_err} ---"); return jsonify({"error": "Database error"}), 503
    except Exception as e:
        print(f"--- SERVER LOG: ❌ ERROR clearing history: {e} ---")
        traceback.print_exc()
        if conn:
            conn.rollback()
        return jsonify({"error": f"Failed to clear history: {str(e)}"}), 500
    finally:
        if conn:
            if cur: cur.close()
            conn.close()


# ==============================================================================
# --- CASE DETAILS ENDPOINT ---
# ==============================================================================
@app.route('/case/<case_number>', methods=['GET'])
def get_case_details(case_number):
    print(f"\n--- SERVER LOG: Fetching details for case: {case_number} ---")
    conn = None; cur = None
    try:
        conn = get_db_connection(); register_vector(conn); cur = conn.cursor()
        if not table_exists(cur, 'cases'): raise psycopg2.errors.UndefinedTable("Table 'cases' needed for details.")
        query = "SELECT id, case_number, title, parties, description, embedding, category FROM cases WHERE case_number = %s;"
        cur.execute(query, (case_number,))
        result = cur.fetchone()
        if not result: print(f"--- SERVER LOG: ⚠️ Case {case_number} not found. ---"); return jsonify({"error": "Case not found"}), 404
        case_id, db_case_number, title, parties, description, embedding_val, category = result
        petitioner = title or "Unknown Petitioner"; respondent = parties or "Unknown Respondent"
        case_embedding_np = None
        try:
            if isinstance(embedding_val, str): case_embedding_np = np.array(ast.literal_eval(embedding_val), dtype=np.float32)
            else: case_embedding_np = np.array(embedding_val, dtype=np.float32)
            if len(case_embedding_np) == 0: raise ValueError("Empty embedding")
        except Exception as emb_err: print(f"--- SERVER LOG: ❌ ERROR processing embedding for {db_case_number}: {emb_err} ---")
        similar_cases_list = []
        if case_embedding_np is not None:
            print(f"--- SERVER LOG: Finding similar cases for {db_case_number}... ---")
            similar_query = "SELECT case_number, title, parties, description, embedding <=> %s AS distance FROM cases WHERE id != %s ORDER BY distance ASC LIMIT 5;"
            try:
                cur.execute(similar_query, (case_embedding_np, case_id))
                similar_cases_raw = cur.fetchall()
                for sim_case in similar_cases_raw:
                    sim_num, sim_title, sim_parties, sim_desc, sim_dist = sim_case
                    sim_dist = float(sim_dist); similarity_pct = max(0.0, (1 - sim_dist) * 100.0)
                    similar_cases_list.append({"case_number": sim_num, "title": sim_title or '', "parties": sim_parties or '', "description": (sim_desc[:200] + "...") if sim_desc and len(sim_desc) > 200 else (sim_desc or ''), "similarity": round(similarity_pct, 1)})
                print(f"--- SERVER LOG: Found {len(similar_cases_list)} similar cases. ---")
            except Exception as sim_err: print(f"--- SERVER LOG: ⚠️ Error finding similar cases: {sim_err} ---")
        else: print(f"--- SERVER LOG: ⚠️ Skipping similar case search due to invalid embedding. ---")
        case_data = {
            "case_number": db_case_number, "title": petitioner, "petitioner": petitioner, "respondent": respondent,
            "parties": f"{petitioner} vs {respondent}", "judgment_date": "N/A", "bench": "N/A", # These fields are still missing from DB
            "category": category or "General", "year": "N/A", "judgment_text": description,
            "similar_cases": similar_cases_list
        }
        print(f"--- SERVER LOG: ✅ Details prepared for {db_case_number}. ---"); return jsonify(case_data), 200
    except psycopg2.errors.UndefinedTable as e: print(f"--- SERVER LOG: ❌ SETUP ERROR - {e} ---"); return jsonify({"error": f"Setup error: {e}"}), 503
    except psycopg2.OperationalError as db_err: print(f"--- SERVER LOG: ❌ DB CONNECTION FAILED case details: {db_err} ---"); return jsonify({"error": "Database error"}), 503
    except Exception as e:
        print(f"--- SERVER LOG: ❌ ERROR fetching case details: {e} ---")
        traceback.print_exc()
        return jsonify({"error": f"Could not retrieve details: {str(e)}"}), 500
    finally:
        if conn:
            if cur: cur.close()
            conn.close()
            print("--- SERVER LOG: DB connection closed (case details). ---")

# ==============================================================================
# --- MAIN EXECUTION BLOCK ---
# ==============================================================================
if __name__ == '__main__':
    print("--- Starting Flask Server ---")
    print("API will be available at http://127.0.0.1:5000")
    print("Ensure PostgreSQL is running and database 'legal_search' exists.")
    print("Ensure required tables (cases, users*, user_searches*, user_bookmarks*) exist. (*optional for core search)")
    print("Press CTRL+C to stop the server.")
    app.run(debug=True, host='127.0.0.1', port=5000)