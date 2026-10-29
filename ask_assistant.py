
import os

import psycopg
from dotenv import load_dotenv
from fastembed import TextEmbedding
from groq import Groq
from pgvector.psycopg import register_vector

load_dotenv()

MODEL_NAME = "BAAI/bge-small-en-v1.5"
GROQ_MODEL = "openai/gpt-oss-120b"

# Initialize the embedding model once per Python process.
_embedding_model = None


def get_embedding_model():
    global _embedding_model

    if _embedding_model is None:
        _embedding_model = TextEmbedding(model_name=MODEL_NAME)

    return _embedding_model


def retrieve(question, model=None, limit=8):
    if model is None:
        model = get_embedding_model()

    query_embedding = list(model.embed([question]))[0].tolist()

    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        register_vector(conn)

        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT d.source, c.content, c.metadata,
                       c.embedding <=> %s::vector AS distance
                FROM document_chunks c
                JOIN documents d ON d.id = c.document_id
                WHERE c.embedding IS NOT NULL
                  AND COALESCE(c.metadata->>'section', '') <> 'front matter'
                ORDER BY c.embedding <=> %s::vector
                LIMIT %s
                """,
                (query_embedding, query_embedding, limit),
            )
            return cur.fetchall()



def answer_question(question):
    """Answer a question and return deduplicated, structured sources."""
    question = question.strip()

    if not question:
        raise ValueError("Question cannot be empty.")

    results = retrieve(question)

    if not results:
        return {
            "question": question,
            "answer": "No relevant information was found in the indexed documents.",
            "sources": [],
        }

    sources = []
    context_parts = []
    seen_chunks = set()

    for source, content, metadata, distance in results:
        metadata = metadata or {}

        page = metadata.get("printed_page", metadata.get("pdf_page"))
        section = metadata.get("section")
        title = metadata.get("title")
        chunk_index = metadata.get("chunk_index")

        # Skip duplicate chunks without confusing citation numbering.
        chunk_key = (source, " ".join(content.split()).casefold())

        if chunk_key in seen_chunks:
            continue

        seen_chunks.add(chunk_key)

        source_id = len(sources) + 1

        source_info = {
            "id": source_id,
            "source": source,
            "title": title,
            "page": page,
            "section": section,
            "chunk_index": chunk_index,
        }
        sources.append(source_info)

        details = []
        if title:
            details.append(f"title: {title}")
        if page is not None:
            details.append(f"page: {page}")
        if section:
            details.append(f"section: {section}")
        if chunk_index is not None:
            details.append(f"chunk: {chunk_index}")

        source_details = ", ".join(details) or source

        context_parts.append(
            f"[Source {source_id}: {source}, {source_details}]\n{content}"
        )

    context = "\n\n".join(context_parts)

    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        temperature=0.2,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a document-grounded research assistant. "
                    "Answer using only the supplied context. "
                    "Cite factual claims using [Source N], matching the "
                    "provided source numbers exactly. Only cite sources "
                    "that support the associated claim. Never invent facts, "
                    "page numbers, or citations. Distinguish legal "
                    "requirements from recommendations or guidance. "
                    "If the context is insufficient, say so."
                ),
            },
            {
                "role": "user",
                "content": f"Question: {question}\n\nContext:\n{context}",
            },
        ],
    )

    answer = response.choices[0].message.content or ""

    return {
        "question": question,
        "answer": answer,
        "sources": sources,
    }


def main():
    question = input("Ask your assistant: ").strip()
    if not question:
        return

    result = answer_question(question)

    print("\n--- Answer ---\n")
    print(result["answer"])

    print("\n--- Sources ---")
    for source in result["sources"]:
        details = []
        if source["title"]:
            details.append(f"Title: {source['title']}")
        if source["page"] is not None:
            details.append(f"Page: {source['page']}")
        if source["section"]:
            details.append(f"Section: {source['section']}")
        if source["chunk_index"] is not None:
            details.append(f"Chunk: {source['chunk_index']}")

        print(
            f"[Source {source['id']}] {source['source']} | "
            + " | ".join(details)
        )


if __name__ == "__main__":
    main()
