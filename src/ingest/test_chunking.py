
from pathlib import Path
from read_html import read_html
from chunk_text import chunk_text

project_root = Path(__file__).resolve().parents[2]
source_file = project_root / "data" / "raw" / "epa_policies_and_regulations.html"

document = read_html(source_file)
chunks = chunk_text(document["text"])

print("Document:", document["source"])
print("Total chunks:", len(chunks))
print("First chunk word count:", len(chunks[0].split()) if chunks else 0)
print("\nFirst chunk preview:\n")
print(chunks[0][:800] if chunks else "No chunks generated.")
