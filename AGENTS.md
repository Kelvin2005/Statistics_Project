# Repository Guidelines

## Project Structure & Module Organization
This repository supports a Red Sea maritime disruption data project. Top-level notes live in `readme.md`, `diary.md`, and `agent.md`. Production scripts are in `scripts/`: `download_acled.py`, `download_portwatch.py`, `collect_aishub.py`, and `run_analysis_real.py`. Generated and source datasets are stored under `data/`, with subdirectories such as `data/acled_data/`, `data/portwatch/`, and `data/aishub/`. Method notes and data descriptions belong in `docs/`; source PDFs and assignment/reference materials belong in `references/`. Use Chinese for project explanations, analysis notes, and contributor-facing discussion unless a dependency or API requires English.

## Build, Test, and Development Commands
Use `environment.yml` to create or update the Conda environment named `Prob`, then execute scripts from the repository root.

```bash
conda env update -f environment.yml
conda activate Prob
python scripts/download_portwatch.py --start-date 2023-01-01
python scripts/download_acled.py
python scripts/collect_aishub.py --once
python scripts/run_analysis_real.py
```

Install the current script dependencies in your environment before running analysis: `pandas`, `numpy`, `matplotlib`, `statsmodels`, and `requests`.

## Coding Style & Naming Conventions
Use Python 3 and keep scripts importable from the repository root. Prefer `pathlib.Path` for file locations and write outputs into the existing `data/<source>/` folders. Use 4-space indentation, `snake_case` for variables/functions, `UPPER_CASE` for constants, and descriptive dataset filenames such as `red_sea_yemen_houthi_related_2023_plus.csv`. Keep comments concise and focused on data assumptions, API quirks, or statistical choices.

## Testing Guidelines
No automated test suite is currently present. Before submitting script changes, run the affected command with a narrow date range or `--once` where available. For analysis changes, verify that `python scripts/run_analysis_real.py` reads the expected CSVs and completes model fitting. If tests are added later, place them under `tests/` and name files `test_<module>.py`.

## Commit & Pull Request Guidelines
Recent commits are short and descriptive, for example `加入了PortWatch数据。` and `加入了readme`. Keep commit messages focused on the changed data source, script, or documentation. Pull requests should describe the purpose, list commands run, mention any changed generated data files, and link relevant issues or assignment notes. Include screenshots only when plots or notebook-style outputs change.

## Security & Configuration Tips
Do not commit API credentials or raw private data. Use `ACLED_EMAIL`, `ACLED_PASSWORD`, and `AISHUB_USERNAME` environment variables. Keep token caches such as `data/acled_API.json` local; it is already ignored by `.gitignore`.
