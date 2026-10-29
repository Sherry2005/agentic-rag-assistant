
from dotenv import load_dotenv
import os
import psycopg

load_dotenv()

with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_name IN ('documents', 'document_chunks')
            ORDER BY table_name;
        """)
        tables = [row[0] for row in cur.fetchall()]

        cur.execute("""
            SELECT indexname
            FROM pg_indexes
            WHERE schemaname = 'public'
              AND tablename = 'document_chunks';
        """)
        indexes = [row[0] for row in cur.fetchall()]

print("Tables:", tables)
print("Indexes:", indexes)
