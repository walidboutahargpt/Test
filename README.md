# Lightweight HR Mini-System (Web)

A macOS-friendly HR mini-system with a modern web UI. Manage employees, leave requests (نموذج إجازة), asset handovers (تسليم عهدة), and generate PDFs for forms and reports—all backed by a simple JSON file.

## Features
- Responsive Flask UI with dashboard, employee list & detail pages, leave requests, asset handovers, and reports.
- JSON datastore (`hr_data.json`) with automatic demo data seeding on first run (3 sample employees plus sample requests/handovers).
- PDF generation (ReportLab) for leave requests, asset handovers, and consolidated HR reports saved to `forms_pdfs/` and `reports/`.
- Quick filtering/search for employees, leave requests, and asset handovers.
- Mac-friendly setup: no database required; run with a single command.

## Quickstart (macOS)
```bash
# 1) (Optional) Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2) Install dependencies
python -m pip install -r requirements.txt

# 3) Start the app
python hr_system.py

# 4) Open the UI
open http://localhost:5000  # or paste into your browser
```

> On first run, `hr_data.json` is created with demo employees, leave requests, and asset handovers so the UI is populated immediately.

## Usage highlights
- **Dashboard:** quick stats and latest leave/asset activity.
- **Employees:** search/filter, view, and add new employees. Each profile links to its Google Drive/local folder path.
- **Leave Request (نموذج إجازة):** create a request, generate a PDF to `forms_pdfs/`, and view all requests with employee filtering.
- **Asset Handover (تسليم عهدة):** capture handovers, generate PDFs, and filter by employee.
- **Reports:** view consolidated tables and export a PDF report to `reports/`.

## PDF output locations
- Individual forms: `forms_pdfs/leave_request_<id>.pdf` and `forms_pdfs/asset_handover_<id>.pdf`
- Consolidated reports: `reports/hr_reports_<timestamp>.pdf`

## Development notes
- Built with Flask + ReportLab; no database dependencies.
- Data is persisted in `hr_data.json`. Delete the file to regenerate fresh demo data.
- The Flask app entrypoint is `hr_system.py` (also exposed as `hr-system` if you `pip install .`).
