"""Validate built pages, navigation anchors, images, and notebook preservation."""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
from urllib.parse import unquote, urlsplit
import zipfile

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"


def main():
    errors = []
    pages = {p.resolve(): BeautifulSoup(p.read_text(encoding="utf-8"), "html.parser") for p in SITE.rglob("*.html")}
    for path, soup in pages.items():
        for element in soup.select("a[href], img[src], script[src], link[href]"):
            href = element.get("href", element.get("src", ""))
            url = urlsplit(href)
            if url.scheme or url.netloc or href.startswith("data:"):
                continue
            if not url.path:
                target = path
            elif url.path.startswith("/"):
                # The site's own links are relative; root-relative URLs belong to hosting metadata.
                continue
            else:
                target = (path.parent / unquote(url.path)).resolve()
            if target.is_dir():
                target /= "index.html"
            if not target.is_file():
                errors.append(f"{path.relative_to(SITE)} -> missing {href}")
            elif url.fragment and target in pages:
                fragment = unquote(url.fragment)
                if not pages[target].find(id=fragment) and not pages[target].find(attrs={"name": fragment}):
                    errors.append(f"{path.relative_to(SITE)} -> missing anchor {href}")
        for table in soup.select("article table:not(.dataframe)"):
            rows = table.select("tr")
            widths = [sum(int(cell.get("colspan", 1)) for cell in row.find_all(["td", "th"], recursive=False)) for row in rows]
            if len(set(widths)) > 1:
                errors.append(f"{path.relative_to(SITE)} -> malformed table ({widths})")

    coverage = json.loads((ROOT / ".generated/coverage.json").read_text())
    sources = {details["notebook"] for details in coverage.values()}
    for filename in sources:
        notebook = json.loads((ROOT / filename).read_text(encoding="utf-8"))
        indices = [i for detail in coverage.values() if detail["notebook"] == filename for i in detail["cells"]]
        if Counter(indices) != Counter(range(len(notebook["cells"]))):
            errors.append(f"Incomplete/duplicated cell coverage for {filename}")
        downloaded = SITE / "downloads" / filename
        if not downloaded.exists() or downloaded.read_bytes() != (ROOT / filename).read_bytes():
            errors.append(f"Notebook download differs from source: {filename}")
    archive_path = SITE / "downloads/ml-field-guide-notebooks.zip"
    with zipfile.ZipFile(archive_path) as archive:
        for name in archive.namelist():
            if archive.read(name) != (ROOT / name).read_bytes():
                errors.append(f"Archive entry differs from source: {name}")

    for source_page in coverage:
        built_path = (SITE / Path(source_page).with_suffix("") / "index.html").resolve()
        if source_page.endswith("/index.md"):
            built_path = (SITE / Path(source_page).with_suffix(".html")).resolve()
        soup = pages.get(built_path)
        if soup is None or not soup.select_one("article h1"):
            errors.append(f"Missing rendered notebook page: {source_page}")
    combined = " ".join(soup.get_text(" ", strip=True) for soup in pages.values())
    for text in ("Q44.", "Generalization", "Random Forest", "Frozen validation-selected threshold"):
        if text not in combined:
            errors.append(f"Missing expected content: {text}")
    if not any(p.name.startswith("search") for p in SITE.rglob("*")):
        errors.append("No generated search assets found")
    if errors:
        raise SystemExit("Documentation checks failed:\n" + "\n".join(errors[:60]))
    print(f"Verified {len(pages)} HTML pages: local links, anchors, assets, tables, all notebook cells, and exact downloads.")


if __name__ == "__main__":
    main()
