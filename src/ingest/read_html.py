
from pathlib import Path
from bs4 import BeautifulSoup

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "epa_policies_and_regulations.html"
)


def read_html(path: Path) -> dict:
    html = path.read_text(encoding="utf-8", errors="replace")
    soup = BeautifulSoup(html, "html.parser")

    for element in soup(["script", "style", "noscript"]):
        element.decompose()

    if soup.title and soup.title.get_text(strip=True):
        title = soup.title.get_text(" ", strip=True)
    elif "femp_federal_renewable_energy" in path.name:
        title = "Federal Renewable Energy Resource Guide"
    elif "epa_policies_and_regulations" in path.name:
        title = "EPA Renewable Energy Policies and Regulations"
    else:
        title = path.stem.replace("_", " ").title()

    text = soup.get_text(" ", strip=True)

    return {
        "source": path.name,
        "title": title,
        "text": text,
    }


if __name__ == "__main__":
    document = read_html(SOURCE_FILE)

    print("Source:", document["source"])
    print("Title:", document["title"])
    print("Characters:", len(document["text"]))
    print("\nPreview:\n")
    print(document["text"][:1000])
