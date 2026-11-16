# Machine Learning Field Guide

Concise ML foundations, practical algorithm walkthroughs, and interview questions. Read the foundations first, then work through the algorithms.

## Notebooks

1. [ML foundations and interview notes](ml-foundations-and-interview-notes.ipynb) — short notes, formulas, figures, evaluation examples, and 44 practice questions.
2. [ML algorithms explained](ml-algorithms-explained.ipynb) — data preparation, fitting, prediction, and evaluation across the main algorithm families.

## Documentation website

The Zensical site generates topic pages directly from both notebooks, preserving code, saved tables, plots, and mathematical notation. It includes search, light/dark themes, chapter navigation, and notebook downloads. There is no separately maintained copy of the learning content.

### Windows / PowerShell

For a fresh checkout (skip these two commands if you already have the project open):

```powershell
git clone https://github.com/RiyanBhargava/machine-learning-algorithms-explained.git
cd machine-learning-algorithms-explained
```

From the repository folder:

```powershell
python -m venv .venv-docs
.\.venv-docs\Scripts\python.exe -m pip install -r requirements-docs.txt
.\.venv-docs\Scripts\python.exe scripts/docs.py serve
```

### macOS / Linux

```bash
python3 -m venv .venv-docs
.venv-docs/bin/python -m pip install -r requirements-docs.txt
.venv-docs/bin/python scripts/docs.py serve
```

Open **http://127.0.0.1:8000**. Use Python 3.12 or newer. The preview regenerates pages when notebooks, illustrations, site configuration, or authored documentation change.

Keep the terminal open while reading. Stop the server with **Ctrl+C**. Subsequent runs need only the last `serve` command. If port 8000 is occupied, append `--address 127.0.0.1:8001` and open that address instead. No environment activation or PowerShell execution-policy change is required with the explicit Python paths above.

### Build and verify

```powershell
.\.venv-docs\Scripts\python.exe scripts/docs.py build
```

On macOS/Linux use `.venv-docs/bin/python`. The command generates pages, performs a strict Zensical build, and checks links, images, notebook downloads, and key content. Static output goes to `site/`.

Documentation builds do **not** execute notebooks. To change results, run and save the notebook in an environment with its ML dependencies, then rebuild. The site's download bundle includes both notebooks and their referenced PNG illustrations.

## Run the notebooks in JupyterLab

Use a separate environment to keep notebook packages independent from the documentation tooling. From the repository folder on Windows:

```powershell
python -m venv .venv-ml
.\.venv-ml\Scripts\python.exe -m pip install -r requirements-notebooks.txt
.\.venv-ml\Scripts\python.exe -m jupyterlab
```

On macOS/Linux, use `python3 -m venv .venv-ml` and `.venv-ml/bin/python` for the next two commands. In JupyterLab, open `ml-foundations-and-interview-notes.ipynb` first, then `ml-algorithms-explained.ipynb`. Select the Python kernel and use **Run → Run All Cells**. Keep the PNG files alongside the notebooks. To read saved outputs, execution is optional.

## Publishing

GitHub Actions validates the site on pull requests and pushes to `main`/`master`. To publish, select **GitHub Actions** in repository **Settings → Pages**, then manually run **Deploy documentation** from the Actions tab on the default branch. The workflow derives the Pages URL automatically. No deployment happens from local builds.

See [the maintenance guide](docs/maintaining.md) for the authoring workflow and other hosting options.

## Source layout

```text
*.ipynb               Learning content and saved results
*.png                 Notebook illustrations
docs/                 Home page, maintenance guide, styles, and scripts
mkdocs.yml            Zensical's MkDocs-compatible configuration
scripts/docs.py       Generate, build, and preview documentation
scripts/check_docs.py Verify the generated website
requirements-docs.txt Pinned direct documentation dependencies
requirements-notebooks.txt Dependencies for executing notebook examples
.github/workflows/    Validation and manual GitHub Pages deployment
.generated/           Generated Markdown/assets/config (ignored)
mkdocs.generated.yml  Generated navigation/configuration (ignored)
site/                 Static website (ignored)
```

The old single-page HTML export is retained for reference; it is superseded by the documentation build. [Zensical](https://zensical.org/docs/get-started/) handles the website, and [nbconvert](https://nbconvert.readthedocs.io/) handles notebook conversion.
