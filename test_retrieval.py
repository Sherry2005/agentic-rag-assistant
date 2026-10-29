
import os

import psycopg
from dotenv import load_dotenv
from fastembed import TextEmbedding
from pgvector.psycopg import register_vector

load_dotenv()
MODEL_NAME = "BAAI/bge-small-en-v1.5"

def main():
    question = input("Ask a question: ").strip()
    if not question:
        print("Please enter a question.")
        return

    model = TextEmbedding(model_name=MODEL_NAME)
    query_embedding = list(model.embed([question]))[0].tolist()

    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        register_vector(conn)

        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT d.source, c.content, c.metadata,
                       1 - (c.embedding <=> %s::vector) AS similarity
                FROM document_chunks c
                JOIN documents d ON d.id = c.document_id
                WHERE c.embedding IS NOT NULL
                ORDER BY c.embedding <=> %s::vector
                LIMIT 5
                """,
                (query_embedding, query_embedding),
            )

            results = cur.fetchall()

    for i, (source, content, metadata, similarity) in enumerate(results, 1):
        print(f"\n--- Result {i} | Similarity: {similarity:.3f} ---")
        print(f"Source: {source}")
        print(f"Metadata: {metadata}")
        print(f"Text: {content[:1000]}")

if __name__ == "__main__":
    main()
