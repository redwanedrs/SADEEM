# SADEEM

> A unified, production-grade astronomical image processing system: **ElectPyNasa** transforms raw deep-space telescopic data into scientific masterpieces, **GalaxyViewer** lets you explore multi-gigabyte DZI pyramids in the browser, and the **Colab notebook** runs the entire pipeline on Google's bandwidth.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![TypeScript 5](https://img.shields.io/badge/typescript-5-blue.svg)](https://www.typescriptlang.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Team — Guardians of the Galaxy

Built for the **NASA Space Apps Challenge 2025** by:

- DELLAL Radouane (team leader)
- ALI HALASA ABDERAHMEN
- LOUNANSA ABDERAHMEN
- YOUSEF HARMOUNI
- BOUAaLLAG YASMINE
- MERSEL FARES

---

## Repository structure

```
SADEEM/
│
├── electpynasa/              ← Python library + Electron UI: GHS stretching,
│   │                          multi-channel alignment, smart color balance,
│   │                          DZI pyramid generation
│   ├── src/electpynasa/      The installable Python package
│   ├── scripts/              Backward-compatible CLI shims
│   ├── tests/                66 passing pytest tests
│   ├── renderer/             Electron desktop UI
│   ├── main.js / preload.js  Electron shell
│   ├── pyproject.toml
│   └── README.md             Full architecture docs
│
├── galaxyviewer/            ← Modern DZI viewer (Vite + TypeScript + OpenSeadragon)
│   ├── src/
│   │   ├── core/            Config, EventBus, Errors, Logger
│   │   ├── services/        DziService, TileLoaderService, ViewportService,
│   │   │                    KeyboardService
│   │   ├── ui/              Viewer (owns OSD), Controls, ProgressBar,
│   │   │                    StatusBar, HelpOverlay, Theme
│   │   └── styles/          All chrome styling
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── README.md
│
├── colab/                   ← Google Colab notebooks
│   ├── electpynasa_colab_pipeline.ipynb       ← THE main notebook:
│   │                                            clones this repo, runs the
│   │                                            CLI, zips the pyramid, saves
│   │                                            to Drive + browser download
│   └── electpynasa_colab_downloader.ipynb     ← Auxiliary: standalone
│                                                downloader + tiler (no repo
│                                                needed; useful for raw MAST
│                                                downloads)
│
└── README.md                ← You are here
```

---

## The unified workflow

The system is designed around a **single source of truth**: the ElectPyNasa Python package. The same CLI runs **identically** on your laptop and on Google Colab — Colab is just a beefier environment with faster network and more disk.

```
┌─────────────────────────── Local machine ───────────────────────────┐
│                                                                     │
│   $ electpynasa-grayscale --input img.fits --output out             │
│   $ electpynasa-composite  --r R.fits --g G.fits --b B.fits ...     │
│   $ electpynasa-pyramid    --input out.tif --output dzi/            │
│                                                                     │
│   → outputs: 32-bit HDR TIFF + 8-bit preview + DZI pyramid          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────── Google Colab (same CLI) ─────────────────────┐
│                                                                     │
│   1. git clone https://github.com/redwanedrs/SADEEM                 │
│   2. pip install -r electpynasa/requirements.txt                    │
│   3. apt install libvips-tools                                     │
│   4. python -m electpynasa.cli.<pipeline> ...                       │
│   5. zip the pyramid output                                         │
│   6. save to Drive + trigger browser download                       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌────────────────────── GalaxyViewer (browser) ───────────────────────┐
│                                                                     │
│   npm run dev    →  http://localhost:5173/?src=.../image.dzi        │
│                                                                     │
│   Progressive tile loading · smooth zoom/pan · minimap · keyboard   │
│   shortcuts · dark space theme · fully responsive                   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Quickstart

### Option A — Run locally

```bash
# Clone the repo
git clone https://github.com/redwanedrs/SADEEM.git
cd SADEEM

# Set up the Python pipeline
cd electpynasa
pip install -r requirements-dev.txt

# Run a pipeline (CLI)
PYTHONPATH=src python -m electpynasa.cli.grayscale \
    --input path/to/image.fits \
    --output path/to/output_base

# Run the test suite
PYTHONPATH=src python -m pytest tests/ -v
# → 66 passed

# Launch the desktop UI (optional)
npm install && npm start
```

### Option B — Run on Google Colab (recommended for large images)

1. Open [colab.research.google.com](https://colab.research.google.com/)
2. **File → Upload Notebook** → select `colab/electpynasa_colab_pipeline.ipynb`
3. Run the cells top-to-bottom. The notebook:
   - Clones this repo into `/content/SADEEM/`
   - Installs all dependencies (Python + libvips)
   - Downloads a sample FITS file (or you can upload your own)
   - Runs the grayscale + pyramid CLIs
   - Zips the DZI pyramid into `electpynasa_pyramid.zip`
   - Copies the ZIP to Google Drive + triggers a browser download

### Option C — View a DZI pyramid with GalaxyViewer

```bash
cd SADEEM/galaxyviewer
npm install
npm run dev
# → http://localhost:5173

# Serve your DZI pyramid (the unzipped output from Colab)
cd path/to/pyramid_output
python3 -m http.server 8000

# Open the viewer:
# http://localhost:5173/?src=http://localhost:8000/image.dzi
```

---

## Project summaries

### `electpynasa/`

A modular astronomical image processing library with three pipelines:

| Pipeline      | Input                | Output                           | Algorithm                                                                      |
| ------------- | --------------------- | --------------------------------- | -------------------------------------------------------------------------------- |
| **Grayscale** | 1× FITS/TIFF          | 32-bit float TIFF                 | Percentile normalize → GHS stretch → shadow/highlight protection                 |
| **Composite** | 3× FITS/TIFF (R/G/B)  | 32-bit HDR TIFF + 8-bit preview   | Per-channel GHS → astroalign/ECC/ORB registration → Lupton smart color balance   |
| **Pyramid**   | Any TIFF/JPEG/PNG     | DZI pyramid (`.dzi` + `_files/`)  | libvips `dzsave` (multi-resolution tile tree)                                    |

Architecture: 7-layer package (utils → core → config → io → processing → pipelines → cli), strategy pattern for every algorithm, structured JSON logger for IPC, 66 pytest tests.

See [`electpynasa/README.md`](electpynasa/README.md) for full architecture docs.

### `galaxyviewer/`

A modern Deep Zoom Image viewer built with **Vite + TypeScript + OpenSeadragon**:

- **Progressive tile loading** — only fetches tiles for the current viewport
- **Smooth zoom/pan** — mouse wheel, pinch, keyboard, click-to-zoom
- **Minimap (navigator)** — top-right overview with viewport indicator
- **Keyboard shortcuts** — `+`/`-`/`0`/arrows/`F`/`H`/`Esc`
- **Help overlay** — press `H` to see all shortcuts
- **Status bar** — zoom %, image dimensions, cursor coordinates
- **Progress bar** — animated tile-load indicator with error flash
- **Dark "space" theme** — fully re-themeable via CSS custom properties
- **Responsive** — chrome collapses on mobile

Architecture: typed EventBus, single OpenSeadragon wrapper (`ui/Viewer.ts` is the only file that imports OSD), service-based separation (DziService / TileLoaderService / ViewportService / KeyboardService), centralized config + theme tokens.

See [`galaxyviewer/README.md`](galaxyviewer/README.md) for details.

### `colab/`

Two notebooks:

| Notebook                               | Purpose                                                                                                                                                          |
| --------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **`electpynasa_colab_pipeline.ipynb`**  | The main notebook. Clones this repo, installs deps, runs the CLI, zips the pyramid, saves to Drive + browser. **This is what you run on Colab.**                |
| `electpynasa_colab_downloader.ipynb`    | Auxiliary standalone downloader. Useful for downloading multi-GB FITS files from MAST with HTTP Range resume, then tiling them — works without cloning the repo. |

---

## Design principles

| Principle                  | Enforcement                                                                                              |
| --------------------------- | ---------------------------------------------------------------------------------------------------------- |
| **Single source of truth**  | The Colab notebook never duplicates pipeline logic — it calls the project's CLI                            |
| **Separation of concerns**  | I/O, algorithms, pipelines, and presentation each live in dedicated sub-packages                           |
| **Strategy pattern**        | Every algorithm (stretch, registration, balance) is a swappable strategy behind a stable ABC/interface     |
| **Pipeline orchestration**  | High-level pipelines compose low-level strategies into reproducible, observable workflows                  |
| **Observability first**     | Structured JSON logs flow through every layer (`__LOG__:{json}` + `SUCCESS:{path}` tokens)                 |
| **Typed everywhere**        | Python type hints + mypy-friendly; TypeScript strict mode + zero `any`                                     |
| **Testable**                | 66 pytest tests for electpynasa; TypeScript compiles cleanly; GalaxyViewer builds without warnings          |
| **Extensible**              | Adding a new stretch / registration / balance algorithm is 1 file + 1 line in the package `__init__`       |

---

## License

MIT — see `electpynasa/pyproject.toml` and `galaxyviewer/package.json`.

---

## Credits

Built for the NASA Space Apps Challenge 2025. Uses:

- [astropy](https://www.astropy.org/) + [astroquery](https://astroquery.readthedocs.io/) — FITS I/O and MAST archive access
- [tifffile](https://github.com/cgohlke/tifffile) — memory-mapped BigTIFF reading
- [OpenCV](https://opencv.org/) — ECC + ORB image registration
- [astroalign](https://astroalign.readthedocs.io/) — asterism-based stellar registration
- [libvips](https://www.libvips.org/) — multi-gigabyte DZI pyramid generation
- [OpenSeadragon](https://openseadragon.github.io/) — Deep Zoom Image rendering engine
- [Vite](https://vitejs.dev/) + [TypeScript](https://www.typescriptlang.org/) — GalaxyViewer build chain
