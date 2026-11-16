"""Build a documentation site from the original, unmodified notebooks."""
from __future__ import annotations

import argparse
import copy
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import threading
import time
import zipfile

import nbformat
from nbconvert import MarkdownExporter
import yaml

ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / ".generated"
DOCS = GENERATED / "docs"
GENERATED_CONFIG = ROOT / "mkdocs.generated.yml"
NOTEBOOKS = {
    "foundations": ROOT / "ml-foundations-and-interview-notes.ipynb",
    "algorithms": ROOT / "ml-algorithms-explained.ipynb",
}
NUMBERED_HEADING = re.compile(r"^## (\d+)\. (.+)$", re.MULTILINE)


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


class GeneratedFiles:
    """Own only files recorded by this generator, never authored content."""

    def __init__(self):
        self.paths: set[str] = set()

    def write(self, path: Path, content: str | bytes):
        path = path.resolve()
        if not path.is_relative_to(GENERATED.resolve()):
            raise ValueError(f"Refusing to write outside generated directory: {path}")
        data = content.encode("utf-8") if isinstance(content, str) else content
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists() or path.read_bytes() != data:
            path.write_bytes(data)
        self.paths.add(path.relative_to(GENERATED).as_posix())

    def finish(self):
        manifest = GENERATED / "files.json"
        previous = json.loads(manifest.read_text()) if manifest.exists() else []
        for relative in set(previous) - self.paths:
            stale = (GENERATED / relative).resolve()
            if not stale.is_relative_to(GENERATED.resolve()):
                raise ValueError(f"Unsafe generated-file manifest entry: {relative}")
            if stale.is_file():
                stale.unlink()
        manifest.write_text(json.dumps(sorted(self.paths), indent=2), encoding="utf-8")


def split_notebook(family: str, path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    # Older source notebooks omit cell IDs. Normalize the build copy only.
    for index, cell in enumerate(data["cells"]):
        cell.setdefault("id", f"{family}-{index}")
    notebook = nbformat.reads(json.dumps(data), as_version=4)
    nbformat.validate(notebook)
    chunks = [{"number": 0, "title": "Overview & setup", "path": f"{family}/index.md", "cells": [], "indices": []}]
    for index, original in enumerate(notebook.cells):
        cell = copy.deepcopy(original)
        match = NUMBERED_HEADING.search(cell.source) if cell.cell_type == "markdown" else None
        if match:
            number, title = int(match[1]), match[2]
            directory = "revision" if family == "foundations" and number >= 23 else family
            chunks.append({"number": number, "title": title,
                           "path": f"{directory}/{number:02d}-{slug(title)}.md", "cells": [], "indices": []})
        chunks[-1]["cells"].append(cell)
        chunks[-1]["indices"].append(index)
    if len({c["number"] for c in chunks}) != len(chunks):
        raise ValueError(f"Duplicate section numbers in {path.name}")
    return notebook, chunks


def relative_link(source: str, target: str) -> str:
    return os.path.relpath(DOCS / target, (DOCS / source).parent).replace(os.sep, "/")


def generate() -> dict:
    files = GeneratedFiles()
    all_chunks = {}
    original_notebooks = {}
    for family, path in NOTEBOOKS.items():
        original_notebooks[family], all_chunks[family] = split_notebook(family, path)

    image_paths: set[Path] = set()
    # Validate and copy referenced notebook images, keeping source filenames intact.
    for notebook in original_notebooks.values():
        for cell in notebook.cells:
            if cell.cell_type == "markdown":
                for reference in re.findall(r"!\[[^\]]*\]\(([^)]+\.png)\)", cell.source):
                    source = (ROOT / reference).resolve()
                    if not source.is_relative_to(ROOT) or not source.is_file():
                        raise ValueError(f"Missing or unsafe notebook illustration: {reference}")
                    image_paths.add(source)
    for path in image_paths:
        files.write(DOCS / "assets/notebook-images" / path.name, path.read_bytes())

    for path in (ROOT / "docs").rglob("*"):
        if path.is_file():
            files.write(DOCS / path.relative_to(ROOT / "docs"), path.read_bytes())

    coverage = {}
    exporter = MarkdownExporter()
    for family, chunks in all_chunks.items():
        source_path = NOTEBOOKS[family]
        section_links = {f"#section-{chunk['number']}": chunk["path"] for chunk in chunks if chunk["number"]}
        for chunk in chunks:
            target = DOCS / chunk["path"]
            cells = chunk["cells"]
            for cell in cells:
                if cell.cell_type == "markdown":
                    # On a topic page, the numbered topic is H1; context banners are H2.
                    cell.source = re.sub(r"^# (.+)$", r"## \1", cell.source, flags=re.MULTILINE)
                    if chunk["number"]:
                        cell.source = NUMBERED_HEADING.sub(lambda m: f"# {m[2]}", cell.source, count=1)
                    elif cell is cells[0]:
                        cell.source = re.sub(r"^## .+$", "# Overview & setup", cell.source, count=1, flags=re.MULTILINE)
                    mappings = {p.name: f"{name}/index.md" for name, p in NOTEBOOKS.items()}
                    mappings.update(section_links)
                    mappings.update({p.name: f"assets/notebook-images/{p.name}" for p in image_paths})
                    for old, new in mappings.items():
                        cell.source = cell.source.replace(f"]({old})", f"]({relative_link(chunk['path'], new)})")
                else:
                    for output in cell.get("outputs", []):
                        if output.output_type == "error":
                            raise ValueError(f"Saved error in {source_path.name}; rerun and save the notebook")
                        if "text/html" in output.get("data", {}):
                            output.data["text/html"] = re.sub(r"<style[^>]*>.*?</style>", "", output.data["text/html"], flags=re.DOTALL)
            partial = nbformat.v4.new_notebook(cells=cells)
            body, resources = exporter.from_notebook_node(partial, resources={
                "unique_key": f"{family}-{chunk['number']:02d}",
                "output_files_dir": "../assets/outputs",
            })
            for filename, data in resources.get("outputs", {}).items():
                files.write(target.parent / filename, data)
            # Numbered source headings may be preceded by an explicit HTML anchor.
            heading = re.search(r"^# .+$", body, re.MULTILINE)
            if heading is None:
                raise ValueError(f"No title found for {chunk['path']}")
            source_link = relative_link(chunk["path"], f"downloads/{source_path.name}")
            intro_link = relative_link(chunk["path"], f"{family}/index.md")
            note = f'\n\n<p class="notebook-origin">From the {family} notebook · <a href="{source_link}" download>Download .ipynb</a> · <a href="{intro_link}">Overview & setup</a></p>'
            if any(c.cell_type == "code" for c in cells):
                note += '\n\n!!! info "Running the examples"\n    These cells share state with earlier notebook cells. Run the complete notebook from the top; this page displays saved results.\n'
            body = body[:heading.end()] + note + body[heading.end():]
            # Pandas HTML output stays native HTML; Markdown and math use the site renderer.
            files.write(target, "<!-- Generated from a notebook. Edit the source .ipynb. -->\n\n" + body)
            coverage[chunk["path"]] = {"notebook": source_path.name, "cells": chunk["indices"], "title": chunk["title"]}

    revision = [c for c in all_chunks["foundations"] if c["number"] >= 23]
    files.write(DOCS / "revision/index.md", "# Questions & revision\n\nPractice explaining the concepts before checking the concise answers.\n\n" +
                "\n".join(f"- [{c['title']}]({Path(c['path']).name})" for c in revision) + "\n")

    downloads = list(NOTEBOOKS.values()) + sorted(image_paths)
    for path in NOTEBOOKS.values():
        files.write(DOCS / "downloads" / path.name, path.read_bytes())
    # Stable timestamps avoid changing this large archive on every preview refresh.
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        for path in downloads:
            info = zipfile.ZipInfo(path.name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            bundle.writestr(info, path.read_bytes())
    files.write(DOCS / "downloads/ml-field-guide-notebooks.zip", archive.getvalue())
    files.write(DOCS / "downloads.md", """# Download & run

## Complete notebook bundle

[Download both notebooks and all illustrations](downloads/ml-field-guide-notebooks.zip){ .md-button .md-button--primary }

Extract the ZIP into one folder before opening the notebooks. Keep the PNG illustrations alongside the notebooks so the algorithm diagrams display correctly.

## Individual notebooks

- [Foundations and interview notes](downloads/ml-foundations-and-interview-notes.ipynb)
- [Algorithms explained](downloads/ml-algorithms-explained.ipynb)

The individual algorithm notebook refers to local PNG files; use the complete bundle to include them. The foundations figures are embedded in saved cell outputs.

## Python environment

Use JupyterLab or a notebook-enabled editor, with a Python environment containing:

```bash
python -m pip install jupyterlab numpy pandas matplotlib seaborn scikit-learn
python -m jupyterlab
```

Open the foundations notebook first. To execute examples, restart the kernel and run the complete notebook from top to bottom. Individual web pages are reading views, not independent Python programs. The website's saved outputs can be read without installing anything.
""")

    foundations = [c for c in all_chunks["foundations"] if c["number"] < 23]
    algorithms = all_chunks["algorithms"]

    def entries(chunks):
        return [{(f"{c['number']:02d} · " if c["number"] else "") + c["title"]: c["path"]} for c in chunks]

    config = yaml.safe_load((ROOT / "mkdocs.yml").read_text(encoding="utf-8"))
    config["docs_dir"] = ".generated/docs"
    config["site_dir"] = "site"
    if os.environ.get("DOCS_SITE_URL"):
        config["site_url"] = os.environ["DOCS_SITE_URL"].rstrip("/") + "/"
    config["nav"] = [
        {"Start here": [{"Welcome": "index.md"}, {"Download & run": "downloads.md"}]},
        {"Foundations": [
            {"Overview & setup": foundations[0]["path"]},
            {"Frame the problem": entries(foundations[1:6])},
            {"Build and validate": entries(foundations[6:12])},
            {"Measure and understand": entries(foundations[12:19])},
            {"Put it into practice": entries(foundations[19:])},
        ]},
        {"Algorithms": [
            {"Overview & setup": algorithms[0]["path"]},
            {"Getting started": entries(algorithms[1:3])},
            {"Supervised learning": entries(algorithms[3:12])},
            {"Unsupervised learning": entries(algorithms[12:15])},
            *entries(algorithms[15:]),
        ]},
        {"Questions & revision": [{"Overview": "revision/index.md"}, *entries(revision)]},
        {"Project guide": [{"Maintaining the documentation": "maintaining.md"}]},
    ]
    generated_config = yaml.safe_dump(config, sort_keys=False, allow_unicode=True)
    if not GENERATED_CONFIG.exists() or GENERATED_CONFIG.read_text(encoding="utf-8") != generated_config:
        GENERATED_CONFIG.write_text(generated_config, encoding="utf-8")
    files.write(GENERATED / "coverage.json", json.dumps(coverage, indent=2))
    files.finish()
    print(f"Generated {len(coverage)} notebook pages from all {sum(len(n.cells) for n in original_notebooks.values())} cells.", flush=True)
    return coverage


def input_signature():
    paths = [*NOTEBOOKS.values(), ROOT / "mkdocs.yml", *ROOT.glob("*.png"),
             *(p for p in (ROOT / "docs").rglob("*") if p.is_file())]
    return tuple((str(p), p.stat().st_mtime_ns, p.stat().st_size) for p in sorted(paths))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["generate", "build", "serve"])
    parser.add_argument("--address", default="127.0.0.1:8000", help="Preview bind address")
    args = parser.parse_args()
    os.chdir(ROOT)
    generate()
    if args.command == "generate":
        return
    command = [sys.executable, "-m", "zensical", args.command, "-f", GENERATED_CONFIG.name]
    if args.command == "build":
        subprocess.run([*command, "--clean", "--strict"], check=True)
        subprocess.run([sys.executable, str(ROOT / "scripts/check_docs.py")], check=True)
    else:
        stop = threading.Event()
        def watch():
            signature = input_signature()
            while not stop.wait(1):
                try:
                    current = input_signature()
                except FileNotFoundError:
                    # An editor may briefly remove a file during an atomic save.
                    continue
                if current != signature:
                    # Wait for notebook editors to finish their atomic save.
                    time.sleep(0.4)
                    try:
                        generate()
                        signature = input_signature()
                    except Exception as exc:
                        print(f"Regeneration failed; save corrected sources to retry: {exc}", file=sys.stderr)
                        signature = current
        watcher = threading.Thread(target=watch, daemon=True)
        watcher.start()
        try:
            subprocess.run([*command, "--dev-addr", args.address], check=True)
        except KeyboardInterrupt:
            pass
        finally:
            stop.set()


if __name__ == "__main__":
    main()
