# Lightweight HR Mini-System

This repository provides a small, macOS-friendly HR CLI for managing employee profiles, linking them to Google Drive/local folders, generating HR forms, and producing summary reports.

## Features
- Create and view employee profiles with Drive/local folder links.
- Generate printable Markdown forms:
  - Leave request form (نموذج إجازة)
  - Asset handover form (تسليم عهدة)
- Store data in a single JSON file (`hr_data.json` by default).
- Produce consolidated HR reports (leave requests and asset handovers).

## Prerequisites
- Python 3.9+ (preinstalled on macOS).

## Quickstart
```bash
# Create a virtual environment (optional but recommended)
python3 -m venv .venv
source .venv/bin/activate

# Install the CLI locally (creates the `hr-system` entrypoint)
pip install .

# Create an employee profile
hr-system create-employee --id EMP001 --name "Fatima Ali" --title "HR Generalist" \
  --email fatima@example.com --folder "https://drive.google.com/..."

# View the profile
hr-system show-employee --id EMP001

# Generate a leave request
hr-system leave-request --id EMP001 --start-date 2025-06-01 --end-date 2025-06-07 \
  --reason "Family trip"

# Generate an asset handover form
hr-system asset-handover --id EMP001 --asset-name "MacBook Pro" --asset-tag MBP-2025-17 \
  --notes "Includes charger and USB-C hub"

# Build consolidated reports
hr-system reports
```

Generated forms are saved in the `forms/` directory, and reports land in `reports/hr_reports.md`. All HR data is persisted in `hr_data.json`, which you can relocate by passing `--data-file` to any command.

## Packaging and running on macOS
### 1) Editable install for daily use
If you want to keep hacking on the code but run it as a command, install it in editable mode:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .

# Confirm the CLI works
hr-system -h
```

### 2) Build a wheel for distribution
Generate a wheel you can copy to another Mac (no external dependencies needed beyond Python 3.9+):

```bash
python -m pip install --upgrade build
python -m build  # produces dist/hr_mini_system-<version>-py3-none-any.whl

# On the target Mac
pip install dist/hr_mini_system-<version>-py3-none-any.whl
hr-system -h
```

### 3) Create a standalone binary (optional)
If you prefer a single executable without requiring Python on the target machine, package it with PyInstaller:

```bash
python -m pip install --upgrade pyinstaller
pyinstaller hr_system.py --onefile --name hr-system

# The binary will be at dist/hr-system (or dist/hr-system.app on macOS)
./dist/hr-system -h
```

## Design notes
- **Architecture:** single-file CLI with a JSON datastore; no external services or databases are required, keeping it lightweight for macOS laptops.
- **Data model:** employees + recorded leave requests and asset handovers, each form linked to its generated Markdown file.
- **Printing:** Markdown outputs can be opened in any editor or browser and printed to PDF or paper.
- **Extensibility:** new form/report types can be added by extending `hr_system.py` with additional subcommands and datastore collections.
