import os
from dotenv import load_dotenv
import psycopg

load_dotenv()

database_url = os.getenv("DATABASE_URL")

if not database_url:
    raise RuntimeError("DATABASE_URL is missing from your .env file.")

try:
    with psycopg.connect(database_url, connect_timeout=15) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT current_database(), version()")
            database, version = cur.fetchone()

    print("Connection successful!")
    print("Database:", database)
    print("PostgreSQL:", version.split(",")[0])

except Exception as exc:
    print("Connection failed:", type(exc).__name__)
    print("Check your .env connection string and Neon connection settings.")
