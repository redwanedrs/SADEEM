# electPyNasa

> Professional, modular astronomical image processing engine: **GHS stretching**, **multi-channel alignment**, **Lupton smart color balance**, and **Deep Zoom Image (DZI) pyramid tiling** — wrapped in an Electron desktop UI.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests: 66 passing](https://img.shields.io/badge/tests-66%20passing-brightgreen.svg)](#testing)

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Directory Layout](#directory-layout)
4. [The Three Pipelines](#the-three-pipelines)
5. [Quickstart](#quickstart)
6. [CLI Reference](#cli-reference)
7. [Python API](#python-api)
8. [Extending the Library](#extending-the-library)
9. [Observability & Logging](#observability--logging)
10. [Testing](#testing)
11. [Design Decisions](#design-decisions)

---

## Overview

`electPyNasa` transforms raw deep-space telescopic data (FITS / TIFF, 16-bit or 32-bit float, dynamic range up to 10^6:1) into scientifically accurate, display-ready visualizations. It is built around four design principles:

| Principle | How it is enforced |
|-----------|---------------------|
| **Separation of concerns** | I/O, algorithms, pipelines, and presentation each live in a dedicated sub-package. |
| **Strategy pattern** | Every algorithm (stretch, registration, balance) is a swappable strategy behind a stable ABC. |
| **Pipeline orchestration** | High-level pipelines compose low-level strategies into reproducible, observable workflows. |
| **Observability first** | Structured JSON logs flow through every layer, enabling both human consoles and machine IPC. |

The library is shipped as a Python package (`electpynasa/`) plus a thin Electron desktop shell that consumes three CLIs via `child_process.spawn` and renders the structured logs into a live console.

---

## Architecture

```
┌──────────────────────── Electron app (renderer + main) ────────────────────────┐
│  renderer/index.html  ◀──▶  renderer/app.js  ◀──▶  preload.js (context bridge) │
│                                                              │                  │
│                                                              ▼                  │
│                                                       main.js (IPC handlers)   │
└──────────────────────────────────────────────────────────────┬──────────────────┘
                                                               │ spawn(python3, [script, ...args])
                                                               ▼
┌──────────────────────────── Python package (electpynasa/) ─────────────────────┐
│                                                                                 │
│  scripts/          Thin backward-compatible shims (delegate to cli/)            │
│       ▼                                                                         │
│  cli/              argparse entry points: grayscale.py, composite.py,           │
│                    pyramid.py                                                   │
│       ▼                                                                         │
│  pipelines/        High-level orchestration: GrayscalePipeline,                 │
│                    CompositePipeline, PyramidPipeline                           │
│       ▼                                                                         │
│  processing/       Strategy implementations:                                    │
│   ├── stretching/    GHS, Arcsinh, Logarithmic                                  │
│   ├── normalization/ Percentile                                                 │
│   ├── protection/    Shadow / Highlight                                          │
│   ├── registration/  Astroalign → ECC → ORB (cascading chain)                   │
│   └── balancing/     Lupton (background-neutralize + white-point + saturation)  │
│       ▼                                                                         │
│  io/               ImageLoader (FITS/TIFF), TIFFWriter, OpenCVWriter            │
│       ▼                                                                         │
│  core/             ABCs (interfaces.py), Pipeline base, types, exceptions       │
│  utils/            ScientificLogger (structured JSON), filesystem, sanity       │
│  config/           Frozen dataclasses with built-in validation                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Layered dependencies

Each layer may only import from the layer immediately below it. This keeps the dependency graph acyclic and makes it trivial to swap any layer in isolation.

```
cli          ─▶ pipelines ─▶ processing ─▶ core
                              │              │
                              └▶ io ─────────┘
                              │
                              └▶ config ─▶ utils
```

---

## Directory Layout

```
electpynasa/
├── README.md
├── pyproject.toml              # PEP 517/518 packaging + pytest config
├── requirements.txt            # Runtime dependencies
├── requirements-dev.txt        # + dev/test dependencies
├── package.json                # Electron app metadata
├── main.js                     # Electron main process
├── preload.js                  # Context-isolated bridge
│
├── renderer/                   # UI (HTML / CSS / JS, separated for maintainability)
│   ├── index.html
│   ├── styles.css
│   └── app.js
│
├── scripts/                    # Backward-compatible CLI shims
│   ├── ghs_stretch_grayscale.py
│   ├── create_pyramid.py
│   └── align/
│       └── ghs_auto_color.py
│
├── src/
│   └── electpynasa/            # The actual Python package
│       ├── __init__.py
│       ├── __version__.py
│       ├── __main__.py         # `python -m electpynasa` → version banner
│       ├── py.typed            # PEP 561 marker (ships type hints)
│       │
│       ├── cli/                # Argparse entry points
│       │   ├── common.py       # safe_main() — uniform exception handling
│       │   ├── grayscale.py
│       │   ├── composite.py
│       │   └── pyramid.py
│       │
│       ├── config/             # Frozen dataclass configs with validation
│       │   └── settings.py
│       │
│       ├── core/               # Foundation: types, ABCs, pipeline base
│       │   ├── types.py        # GrayImage, RGBImage, Channel, results
│       │   ├── interfaces.py   # StretchStrategy, RegistrationStrategy, …
│       │   └── pipeline.py     # Pipeline ABC with observable step runner
│       │
│       ├── io/                 # I/O layer
│       │   ├── loaders.py      # ImageLoader: FITSLoader + TIFFLoader
│       │   ├── writers.py      # TIFFWriter + OpenCVWriter
│       │   └── validators.py   # validate_image_path, validate_three_channels
│       │
│       ├── processing/         # Concrete strategies
│       │   ├── stretching/     # GHS, Arcsinh, Logarithmic
│       │   ├── normalization/  # PercentileNormalizer
│       │   ├── protection/     # ShadowHighlightProtector
│       │   ├── registration/   # Astroalign, ECC, ORB + chain builder
│       │   └── balancing/      # LuptonBalancer
│       │
│       ├── pipelines/          # High-level orchestration
│       │   ├── grayscale_pipeline.py
│       │   ├── composite_pipeline.py
│       │   └── pyramid_pipeline.py
│       │
│       └── utils/              # Cross-cutting concerns
│           ├── exceptions.py   # 11-class typed exception hierarchy
│           ├── logging.py      # ScientificLogger (structured JSON IPC)
│           ├── filesystem.py   # Path validation, discovery, output building
│           └── sanity.py       # require_2d, require_same_shape, etc.
│
└── tests/                      # pytest suite (66 tests, all passing)
    ├── conftest.py
    ├── unit/
    │   ├── test_stretching.py
    │   ├── test_normalization.py
    │   ├── test_balancing.py
    │   ├── test_registration.py
    │   ├── test_loaders.py
    │   ├── test_logger.py
    │   └── test_config.py
    └── integration/
        └── test_grayscale_pipeline.py
```

---

## The Three Pipelines

### 1. Grayscale GHS Pipeline (`GrayscalePipeline`)

Single FITS/TIFF image → percentile normalization → Generalized Hyperbolic Stretch → shadow/highlight protection → 32-bit float TIFF.

```
INPUT  ─▶ load ─▶ normalize ─▶ stretch ─▶ protect ─▶ write ─▶ OUTPUT (_grayscale.tif)
```

### 2. Color Composite Pipeline (`CompositePipeline`)

Three FITS/TIFF channels (R/G/B) → per-channel normalize + GHS + protect → register R&B to G (astroalign → ECC → ORB cascade) → stack to 32-bit HDR TIFF → Lupton smart color balance → 8-bit preview TIFF.

```
R ─┐
G ─┼─▶ load ─▶ stretch ─▶ register(R,B → G) ─▶ write_hdr ─▶ balance ─▶ OUTPUT
B ─┘                                                              ├─ _color_32bit.tiff
                                                                  └─ _color_8bit_preview.tiff
```

### 3. DZI Pyramid Pipeline (`PyramidPipeline`)

Large TIFF/JPEG/PNG/WebP → libvips `dzsave` → Deep Zoom Image pyramid (multi-resolution tile tree + `.dzi` manifest).

```
INPUT ─▶ validate ─▶ check_vips ─▶ prepare_output ─▶ run_dzsave ─▶ finalize ─▶ OUTPUT (.dzi + tiles/)
```

---

## Quickstart

### Prerequisites

- **Python 3.9+** with `numpy`, `opencv-python-headless`, `tifffile`, `astropy`, `astroalign`
- **Node.js 18+** with `electron` (dev dependency)
- **libvips** (only required for the DZI pyramid pipeline)

### Install (development mode)

```bash
git clone <repo>
cd electpynasa
pip install -r requirements-dev.txt
pip install -e .              # optional: installs the `electpynasa-*` CLI entry points
npm install                  # installs Electron
```

### Run the desktop app

```bash
npm start                    # launches the Electron UI
```

The UI spawns the Python scripts under `scripts/` with `PYTHONPATH=src/` so the `electpynasa` package is importable without installation.

---

## CLI Reference

Every CLI emits structured logs on stdout:

- `__LOG__:{json}` — one per event (timestamp, level, message, optional progress, optional extra)
- `SUCCESS:{path}` — terminal token carrying the primary output artifact

Exit codes: `0` success, `1` known ElectPyNasa error, `2` unexpected exception, `130` Ctrl-C.

### `electpynasa-grayscale` (alias: `python -m electpynasa.cli.grayscale`)

```
--input PATH         Input FITS or TIFF image
--output PATH        Output base path (suffixes appended automatically)
--k FLOAT            GHS stretch factor (default 2.5)
--L FLOAT            GHS local decay (default 6.0)
--s FLOAT            GHS symmetry point (default 0.20)
--sp FLOAT           Shadow protection threshold (default 0.01)
--hp FLOAT           Highlight protection threshold (default 0.98)
--lower-pct FLOAT    Normalization lower percentile (default 0.5)
--upper-pct FLOAT    Normalization upper percentile (default 99.5)
```

### `electpynasa-composite` (alias: `python -m electpynasa.cli.composite`)

```
--r PATH             Red channel image
--g PATH             Green channel image
--b PATH             Blue channel image
--output PATH        Output base path
--k FLOAT            GHS stretch factor (default 2.5)
--L FLOAT            GHS local decay (default 6.0)
--s FLOAT            GHS symmetry point (default 0.20)
--saturation FLOAT   Lupton saturation (default 1.35)
--q FLOAT            Lupton Q factor (default 7.5)
```

### `electpynasa-pyramid` (alias: `python -m electpynasa.cli.pyramid`)

```
--input PATH         Input image (TIFF/JPEG/PNG/WebP)
--output DIR         Output directory (image-named subdirectory is created inside)
--tileSize INT       Tile size in pixels (default 256)
--overlap INT        Tile overlap in pixels (default 1)
--format STR         Tile format: jpeg | png | webp (default jpeg)
--quality INT        JPEG/WebP quality 1-100 (default 90)
```

---

## Python API

Every pipeline is usable directly from Python — no CLI required.

```python
from electpynasa.config import GrayscalePipelineConfig, GHSConfig
from electpynasa.pipelines import GrayscalePipeline

config = GrayscalePipelineConfig(ghs=GHSConfig(k=3.0, L=8.0, s=0.15))
result = GrayscalePipeline(
    config=config,
    input_path="ngc3324.fits",
    output_base="output/ngc3324",
).run()

print(result.grayscale_path)
print(result.window)
print(result.shape)
```

```python
from electpynasa.pipelines import CompositePipeline

result = CompositePipeline(
    red_path="F444W.fits",
    green_path="F200W.fits",
    blue_path="F090W.fits",
    output_base="output/carina_composite",
).run()

print(result.hdr_path)      # 32-bit master
print(result.preview_path)  # 8-bit display preview
```

```python
from electpynasa.pipelines import PyramidPipeline

result = PyramidPipeline(
    input_path="output/carina_composite_color_8bit_preview.tiff",
    output_dir="output/deepzoom",
).run()

print(result.dzi_path)        # .dzi manifest
print(result.tiles_directory) # tiles/ folder
```

### Strategy composition

Need a custom stretch or registration algorithm? Implement the ABC and inject it into the pipeline.

```python
from electpynasa.core.interfaces import StretchStrategy
import numpy as np

class GammaStretch(StretchStrategy):
    def __init__(self, gamma: float = 2.2):
        self._gamma = gamma

    def stretch(self, image):
        return np.clip(image ** self._gamma, 0.0, 1.0)

# Then monkey-patch the pipeline step or write a new pipeline that uses it.
```

---

## Extending the Library

| You want to… | Where to add code |
|--------------|-------------------|
| Add a new stretch algorithm | `processing/stretching/` — implement `StretchStrategy`, register in `__init__.py` |
| Add a new registration strategy | `processing/registration/` — implement `RegistrationStrategy`, add to `RegistrationChainBuilder.build_default()` |
| Add a new color-balance algorithm | `processing/balancing/` — implement `BalancingStrategy` |
| Add a new file format | `io/loaders.py` — add a `_FormatLoader` subclass and register in `ImageLoader._LOADERS` |
| Add a new pipeline | `pipelines/` — subclass `Pipeline`, implement `build()` with steps, return a result dataclass |
| Add a new CLI | `cli/` — copy `grayscale.py`, swap the pipeline + arguments, register in `pyproject.toml` `[project.scripts]` |

Every algorithm and pipeline follows the same shape, so onboarding a new contributor is a matter of pointing them at one file in each layer.

---

## Observability & Logging

The `ScientificLogger` emits one JSON object per event on stdout:

```json
{
  "timestamp": 1782918844.453,
  "level": "INFO",
  "message": "Step 3/6: normalize",
  "progress": 33.33,
  "extra": { "lower_pct": 0.5, "upper_pct": 99.5 }
}
```

The Electron renderer parses every line:

- Lines starting with `__LOG__:` are JSON-parsed and rendered into the live console with timestamp, color-coded level, and message.
- The optional `progress` field updates the progress bar in real time.
- A terminal `SUCCESS:{path}` line marks pipeline completion and reveals the result-area link.

The structured schema is intentionally minimal and stable so non-Electron consumers (CI runners, notebook wrappers, microservices) can parse it with a single regex.

---

## Testing

The suite is split into:

- **`tests/unit/`** — fast, isolated tests for every module (stretching, normalization, protection, registration, balancing, loaders, writers, validators, logger, config).
- **`tests/integration/`** — end-to-end tests that drive real pipelines against synthetic FITS files on disk.

```bash
PYTHONPATH=src python -m pytest tests/ -v
# 66 passed in 1.12s
```

Coverage reporting:

```bash
PYTHONPATH=src python -m pytest tests/ --cov=electpynasa --cov-report=html
```

---

## Design Decisions

### Why frozen dataclasses for configs?

Frozen dataclasses are immutable, hashable, and trivially serializable. They prevent the "config was mutated halfway through the pipeline" class of bugs and make it easy to log a config snapshot at the start of each run.

### Why a `RegistrationChain` instead of a single registration function?

Astroalign is the most accurate strategy for stellar fields but fails on dense nebular regions. ECC handles affine distortions but needs similar intensity distributions. ORB is the most generic but least accurate. A chain lets us try them in order and pick the first that succeeds, which gives us robustness across heterogeneous inputs without forcing the caller to know which strategy to pick.

### Why a Pipeline base class with explicit steps?

Each step is a labeled callable. The base class automatically:

1. Emits a "Step N/M: label" log with progress percentage,
2. Wraps any unexpected exception in a `PipelineStepError` carrying the step name,
3. Threads a mutable `context` dict through every step so steps don't need to communicate via instance state.

This means adding a new step is one line (`self.add_step("name", self._step_method)`) and the step is automatically observable, error-wrapped, and threaded through the context.

### Why context-isolated Electron with a preload bridge?

The original app used `nodeIntegration: true` and `contextIsolation: false`, which is unsafe and prevents upgrading Electron. The new preload exposes a single audited `window.electpynasa` API surface (file picker, Python resolver, `child_process.spawn`, `process.env`). The renderer never touches Node APIs directly.

### Why are scripts kept at the project root?

The Electron app expects `scripts/ghs_stretch_grayscale.py`, `scripts/align/ghs_auto_color.py`, and `scripts/create_pyramid.py` to exist (matching the original layout). The scripts are now thin shims that delegate to the real CLI under `electpynasa/cli/`. This means the Electron UI works without any changes while the actual logic lives in the installable package.

---

## License

MIT — see `package.json` and `pyproject.toml`.
