# Maintaining the documentation

## Edit once, publish consistently

The root `.ipynb` files are the source of truth for the learning material. The build reads them with **nbformat**, converts cells with **nbconvert**, and gives the generated Markdown to **Zensical** for navigation, search, code highlighting, and page rendering.

| Source | Purpose |
|---|---|
| `ml-foundations-and-interview-notes.ipynb` | Concept notes, figures, questions, and revision |
| `ml-algorithms-explained.ipynb` | Algorithm walkthroughs and saved results |
| `docs/` | Home page, supporting documentation, and theme assets |
| `mkdocs.yml` | Zensical's MkDocs-compatible theme configuration |
| `scripts/docs.py` | Notebook conversion, generated navigation, build, and preview |
| `scripts/check_docs.py` | Built-site link, asset, content, and download checks |

Do not edit `.generated/`, `mkdocs.generated.yml`, or `site/`: they are rebuildable output and excluded from Git. The original notebook files are not modified by the documentation build.

## Build or preview

Install `requirements-docs.txt` in a Python 3.12+ virtual environment, then run:

```bash
python scripts/docs.py serve
```

Open the printed local URL. The preview watches the notebooks, root PNG illustrations, `docs/`, and `mkdocs.yml`, regenerating the documentation when these change. Save notebook edits to trigger updates. Restart preview after changing the build scripts or dependencies.

For a production build and link checks:

```bash
python scripts/docs.py build
```

The deployable files are in `site/`. Serve them over HTTP; opening `index.html` as a local file does not provide the same routing and search behavior.

## Update a notebook

1. Edit the source notebook. Keep each numbered topic heading in its own Markdown cell (`## 3. Topic title`).
2. If code changes, run the notebook in its ML environment and save its outputs.
3. Run the documentation build. It uses saved results and never executes notebook code or installs notebook dependencies.
4. Review the affected pages and check the console for validation failures.

Each numbered section becomes a page. Navigation labels come from the notebook headings. The foundations questions and final checklist appear under **Questions & revision**. Notebook-only links are rewritten to their website destinations; notebook downloads retain the original content.

The algorithm pages share setup/import/helper cells from the notebook's opening. Code snippets on an individual page are not necessarily standalone. Open the complete notebook and run it in order when experimenting.

## Publish on GitHub Pages

The repository includes separate validation and publication workflows:

- Pull requests and pushes to `main` or `master` build and validate the documentation.
- Publication is **manual**. In repository **Settings → Pages**, select **GitHub Actions** as the source. Then run **Deploy documentation** from the Actions tab on the default branch.

The deployment workflow obtains the correct Pages base URL, builds and checks the site, uploads `site/`, and deploys it. No hard-coded account name or repository URL is required. Building locally does not publish anything.

For another static host, run the same build command and upload the contents of `site/`. Set `DOCS_SITE_URL` to the final full URL, including any repository subpath, when building for hosting.

## Framework choice and legacy files

[Zensical](https://zensical.org/docs/get-started/) is the successor from the Material for MkDocs team. It accepts a familiar MkDocs-style configuration and generates a static site. This project uses nbconvert before the site build rather than depending on a notebook-specific MkDocs plugin.

`export_notebook_to_html.py` and `ml-algorithms-explained.html` are retained as legacy artifacts. They are not inputs to this site; the supported documentation command is `python scripts/docs.py build`.

The theme uses local system fonts. MathJax is vendored with its license, so formulas do not require a third-party CDN at reading time. External reference links still require internet access.
