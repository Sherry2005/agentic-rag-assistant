
import os
from dotenv import load_dotenv
import psycopg

load_dotenv()

with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT d.source, COUNT(c.id)
            FROM documents d
            LEFT JOIN document_chunks c ON c.document_id = d.id
            WHERE d.source = %s
            GROUP BY d.source
        """, ("epa_policies_and_regulations.html",))

        print(cur.fetchall())
