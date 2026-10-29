import argparse
import json
import os
from pathlib import Path
import sys

from dotenv import load_dotenv
from fastembed import TextEmbedding
import psycopg
from psycopg.types.json import Jsonb
from pgvector.psycopg import register_vector

# Make the ingest folder importable.
HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

from read_html import read_html
from chunk_text import chunk_text

load_dotenv(PROJECT_ROOT / ".env")

SOURCE_FILE = (
    PROJECT_ROOT / "data" / "raw" / "epa_policies_and_regulations.html"
)
MODEL_NAME = "BAAI/bge-small-en-v1.5"

def load_jsonl(path):
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--jsonl",
        type=Path,
        help="Path to preprocessed JSONL chunks",
    )
    parser.add_argument(
        "--html",
        type=Path,
        help="Path to an HTML file to ingest",
    )
    args = parser.parse_args()

    if args.jsonl:
        jsonl_path = args.jsonl
        chunks_data = load_jsonl(jsonl_path)

        if not chunks_data:
            raise ValueError(f"No chunks found in {jsonl_path}")

        source = chunks_data[0]["source_doc"]
        title = "Solar Renewable Energy Certificate (SREC) Markets: Status and Trends"
        chunks = [item["text"] for item in chunks_data]

        metadata = [
            {
                **{
                    key: item.get(key)
                    for key in (
                        "id",
                        "source_doc",
                        "pdf_page",
                        "printed_page",
                        "section",
                        "chunk_type",
                        "table_id",
                    )
                },
                "title": title,
            }
            for item in chunks_data
        ]
    else:
        html_path = args.html or SOURCE_FILE
        document = read_html(html_path)
        source = document["source"]
        title = document["title"]
        chunks = chunk_text(document["text"])
        metadata = [
            {
                "source": source,
                "title": title,
                "chunk_index": index,
            }
            for index, _ in enumerate(chunks)
        ]
    print(f"Document: {source}")
    print(f"Chunks: {len(chunks)}")
    print("Loading embedding model (the first run downloads it)...")

    model = TextEmbedding(model_name=MODEL_NAME)
    embeddings = list(model.embed(chunks))

    database_url = os.environ["DATABASE_URL"]

    with psycopg.connect(database_url) as conn:
        register_vector(conn)

        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO documents (source, title)
                VALUES (%s, %s)
                ON CONFLICT (source)
                DO UPDATE SET title = EXCLUDED.title
                RETURNING id
                """,
                (source, title),
            )
            document_id = cur.fetchone()[0]

            for index, (content, embedding, meta) in enumerate(
                zip(chunks, embeddings, metadata)
            ):
                cur.execute(
                    """
                    INSERT INTO document_chunks
                        (document_id, chunk_index, content, embedding, metadata)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (document_id, chunk_index)
                    DO UPDATE SET
                        content = EXCLUDED.content,
                        embedding = EXCLUDED.embedding,
                        metadata = EXCLUDED.metadata
                    """,
                    (
                        document_id,
                        index,
                        content,
                        embedding.tolist(),
                        Jsonb(meta),
                    ),
                )

            cur.execute(
                """
                DELETE FROM document_chunks
                WHERE document_id = %s AND chunk_index >= %s
                """,
                (document_id, len(chunks)),
            )

    print(f"Successfully stored {len(chunks)} chunks in Neon.")
if __name__ == "__main__":
    main()
