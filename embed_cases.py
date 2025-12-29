# ==============================================================================
# IMPORT NECESSARY LIBRARIES
# ==============================================================================
import pandas as pd
import psycopg2
from sentence_transformers import SentenceTransformer
from pgvector.psycopg2 import register_vector
import numpy as np
from tqdm import tqdm
import random
import traceback

# ==============================================================================
# --- CONFIGURATION ---
# ==============================================================================
# The path to your CSV file
FILEPATH_KAGGLE = r"archive (2)\judgments.csv"

# Define a list of keywords for various legal categories
# These are used to enrich the data so the browse categories will work
category_keywords = {
    'criminal_law': ['theft', 'robbery', 'assault', 'homicide', 'murder', 'rape', 'sexual assault', 'harassment', 'domestic violence', 'fraud', 'smuggling'],
    'civil_law': ['contract dispute', 'property damage', 'negligence', 'malpractice', 'defamation', 'libel'],
    'corporate_law': ['corporate law', 'insolvency', 'bankruptcy', 'merger', 'acquisition'],
    'tax_law': ['tax evasion', 'income tax', 'customs duty'],
    'labor_law': ['labor law', 'employment', 'wrongful termination', 'workplace safety'],
    'family_law': ['domestic violence', 'divorce', 'custody', 'alimony'],
    'constitutional_law': ['appeal', 'writ petition', 'human rights']
}
all_keywords = [kw for sublist in category_keywords.values() for kw in sublist]

# ==============================================================================
# --- MAIN AI EMBEDDING AND DATABASE POPULATION SCRIPT (CORRECTED) ---
# ==============================================================================
def embed_and_populate():
    """
    The main function to perform the entire ETL (Extract, Transform, Load) process:
    1.  Loads the AI model.
    2.  Connects to the database and clears old data.
    3.  Reads and processes the CSV data using the REAL judgment text.
    4.  Generates vector embeddings from the REAL judgment text.
    5.  Inserts the final, correct data into the database.
    """
    print("--- Starting CORRECTED AI Embedding and Database Population Process ---")

    # --- Step 1: Load the AI Model ---
    print("\n--- Loading AI model 'all-MiniLM-L6-v2'... ---")
    try:
        model = SentenceTransformer('all-MiniLM-L6-v2')
        print("✅ AI model loaded successfully.")
    except Exception as e:
        print(f"❌ CRITICAL ERROR: Could not load SentenceTransformer model. Error: {e}")
        return

    conn = None
    try:
        # --- Step 2: Connect to Database and Clear Old Data ---
        print("\n--- Connecting to PostgreSQL database... ---")
        conn = psycopg2.connect(
            dbname="postgres", user="postgres", password="12345", host="localhost", port="5432"
        )
        register_vector(conn)
        cur = conn.cursor()
        print("✅ Database connection successful.")
        
        print("\n--- Clearing old data from the database ---")
        cur.execute("TRUNCATE TABLE cases RESTART IDENTITY CASCADE;")
        conn.commit()
        print("✅ Old data cleared.")

        # --- Step 3: Read and Process CSV Data ---
        print(f"\n--- Reading and processing data from {FILEPATH_KAGGLE} ---")
        df = pd.read_csv(FILEPATH_KAGGLE)
        
        # --- FIX: Manually create 'judgment_text' from other columns since it doesn't exist in the CSV ---
        print("\n--- Creating searchable text from available metadata ---")
        # Drop rows where the essential source columns are missing
        df.dropna(subset=['pet', 'res', 'Judgement_type', 'bench', 'judgement_by'], inplace=True)
        
        # Combine multiple relevant columns into a single searchable text block
        df['judgment_text'] = (
            df['Judgement_type'].astype(str) + ' | ' +
            df['bench'].astype(str) + ' | ' +
            df['judgement_by'].astype(str)
        )
        
        df.reset_index(drop=True, inplace=True)
        
        # --- Step 4: Create the Title ---
        print("\n--- Preparing title and searchable text for embedding ---")
        df['title'] = df['pet'].astype(str) + ' vs ' + df['res'].astype(str)
        # Use the newly created 'judgment_text' for the embeddings
        df['searchable_text'] = df['judgment_text'].astype(str)

        # --- Step 5: Generate Vector Embeddings from REAL Text ---
        print("\n--- Generating vector embeddings from REAL judgment text ---")
        texts_to_embed = df['searchable_text'].tolist()
        embeddings = model.encode(texts_to_embed, show_progress_bar=True)
        print(f"\n✅ Successfully processed and embedded {len(df)} cases.")

        # --- Step 6: Insert Correct Data into the Database ---
        print(f"\n--- Starting to insert {len(df)} cases with REAL embeddings into the database ---")
        
        for i, row in tqdm(df.iterrows(), total=len(df), desc="Inserting into DB"):
            title = row['title']
            judgment_text = row['searchable_text'] # This is the REAL, full judgment text
            embedding = embeddings[i]
            
            cur.execute(
                "INSERT INTO cases (title, judgment_text, embedding) VALUES (%s, %s, %s)",
                (title, judgment_text, np.array(embedding))
            )
        
        conn.commit()
        print("\n\n✅✅✅ DATABASE POPULATION WITH HIGH-QUALITY AI EMBEDDINGS COMPLETE! ✅✅✅")

    except Exception as e:
        print(f"\n❌ AN ERROR OCCURRED: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            cur.close()
            conn.close()
            print("\nDatabase connection closed.")


def get_db_connection():
    """
    Establishes a new database connection.
    Returns:
        conn: A new database connection object.
    """
    try:
        conn = psycopg2.connect(
            dbname="postgres", user="postgres", password="12345", host="localhost", port="5432"
        )
        print("--- Database connection established. ---")
        return conn
    except Exception as e:
        print(f"--- ❌ Error connecting to the database: {e} ---")
        return None


def embed_and_populate(csv_file_path, conn):
    """
    Embeds case data and populates the database.
    
    Args:
        csv_file_path (str): Path to the CSV file containing case data.
        conn: Active database connection.
    """
    print("--- Starting data embedding and population process ---")
    try:
        # Try to register pgvector, but continue without it if not available
        try:
            register_vector(conn)
            print("--- pgvector extension registered ---")
        except Exception as e:
            print(f"--- pgvector not available (OK - will store as text): {e} ---")
        
        cur = conn.cursor()
        print("--- Database cursor created. Clearing existing data... ---")
        
        # Clear existing data using CASCADE to handle foreign key constraints
        cur.execute("TRUNCATE TABLE cases RESTART IDENTITY CASCADE;")
        print("--- 'cases' table and dependent tables truncated. ---")

        # Load the dataset
        print(f"--- Loading dataset from '{csv_file_path}'... ---")
        df = pd.read_csv(csv_file_path)
        df = df.reset_index(drop=True)
        print(f"--- Dataset loaded. Found {len(df)} rows. ---")

        def ensure_series(possible_columns, default_value):
            for col in possible_columns:
                if col in df.columns:
                    return df[col].fillna(default_value).astype(str)
            return pd.Series([default_value] * len(df), index=df.index, dtype="string")

        # Build canonical columns expected by the database
        df['pet'] = ensure_series(['pet', 'petitioner_name', 'petitioner'], 'Unknown Petitioner')
        df['res'] = ensure_series(['res', 'respondent_name', 'respondent'], 'Unknown Respondent')
        df['judgement_by'] = ensure_series(['judgement_by', 'judge', 'judges'], 'Unknown Judge')
        df['bench'] = ensure_series(['bench', 'court'], 'Unknown Bench')
        df['judgement_type'] = ensure_series(['Judgement_type', 'judgement_type', 'case_type'], 'General Proceedings')
        df['judgment_date'] = ensure_series(['judgement_date', 'date_of_judgement', 'case_date'], '')

        # Compose title and enriched judgment text
        df['title'] = (df['pet'].astype(str) + ' vs ' + df['res'].astype(str)).str.strip()
        df['judgment_text'] = (
            'Bench: ' + df['bench'] + '. Presiding Judge: ' + df['judgement_by'] +
            '. Proceedings: ' + df['judgement_type']
        )

        # Initialize the sentence transformer model
        print("--- Initializing Sentence Transformer model 'all-MiniLM-L6-v2'... ---")
        model = SentenceTransformer('all-MiniLM-L6-v2')
        print("--- Model initialized successfully. ---")

        # Process in batches for much faster performance
        BATCH_SIZE = 100
        total_rows = len(df)
        
        # Prepare all text for batch embedding
        print("--- Preparing text for batch embedding ---")
        texts_to_embed = []
        for index, row in df.iterrows():
            title = str(row['title']) if row['title'] else 'Untitled Case'
            judgment_text_original = str(row['judgment_text']) if row['judgment_text'] else 'No judgment details provided.'
            simulated_keyword = random.choice(all_keywords)
            text_to_embed = f"Case Title: {title}. Judgment Details: {judgment_text_original}. Keywords: {simulated_keyword}"
            texts_to_embed.append(text_to_embed)
        
        # Generate all embeddings at once (much faster)
        print("--- Generating embeddings for all cases (this will take a few minutes) ---")
        embeddings = model.encode(texts_to_embed, show_progress_bar=True, batch_size=32)
        print("--- All embeddings generated! Now inserting into database ---")
        
        # Insert in batches
        for i in range(0, total_rows, BATCH_SIZE):
            batch_end = min(i + BATCH_SIZE, total_rows)
            batch_data = []
            
            for j in range(i, batch_end):
                row = df.iloc[j]
                title = str(row['title']) if row['title'] else 'Untitled Case'
                batch_data.append((title, texts_to_embed[j], embeddings[j].tolist()))
            
            try:
                cur.executemany(
                    "INSERT INTO cases (title, judgment_text, embedding) VALUES (%s, %s, %s)",
                    batch_data
                )
                conn.commit()
                print(f"--- Inserted batch {i//BATCH_SIZE + 1}/{(total_rows + BATCH_SIZE - 1)//BATCH_SIZE} ({batch_end}/{total_rows} rows) ---")
            except Exception as e:
                conn.rollback()
                print(f"--- ⚠️ Error inserting batch starting at row {i}: {e}. Skipping batch. ---")
                continue

        conn.commit()
        print(f"\n--- ✅ Success! All {total_rows} rows have been processed and inserted into the database. ---")

    except (Exception, psycopg2.DatabaseError) as error:
        print(f"--- ❌ CRITICAL DATABASE ERROR: {error} ---")
        traceback.print_exc()
        conn.rollback()
    finally:
        if 'cur' in locals() and cur:
            cur.close()
        print("--- Database cursor closed. ---")


def main():
    """
    Main entry point of the script.
    """
    print("--- Starting the script ---")
    
    # Establish a database connection
    conn = get_db_connection()
    if conn is None:
        print("❌ Failed to connect to the database. Exiting.")
        return
    
    # Embed and populate the database with cases from the CSV file
    embed_and_populate(FILEPATH_KAGGLE, conn)

    print("--- Script completed ---")


if __name__ == "__main__":
    main()

