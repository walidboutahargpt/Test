"""Web-based HR mini-system with PDF generation.

Features:
- Responsive Flask web UI for dashboard, employee management, leave requests, asset handovers, and reports.
- JSON datastore with automatic seeding of demo data on first run.
- PDF generation for leave requests, asset handovers, and consolidated reports.
- macOS-friendly setup with lightweight dependencies.
"""
from __future__ import annotations

import datetime as dt
import json
import uuid
from pathlib import Path
from typing import Dict, List, Optional

from flask import (
    Flask,
    Response,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    send_from_directory,
    url_for,
)
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

DATA_FILE = Path("hr_data.json")
FORMS_DIR = Path("forms_pdfs")
REPORTS_DIR = Path("reports")


class HRDataStore:
    """Simple JSON-backed datastore for the HR system."""

    def __init__(self, path: Path = DATA_FILE):
        self.path = path
        self.data: Dict[str, object] = {"employees": {}, "leave_requests": [], "asset_handovers": []}
        self._load_or_seed()

    def _load_or_seed(self) -> None:
        if self.path.exists():
            try:
                self.data = json.loads(self.path.read_text())
            except json.JSONDecodeError:
                raise SystemExit(f"Data file {self.path} is corrupted; please fix or remove it.")
        else:
            self._seed_demo_data()
            self.save()

    def _seed_demo_data(self) -> None:
        self.data = {
            "employees": {
                "E-001": {
                    "name": "Layla Hassan",
                    "title": "HR Specialist",
                    "email": "layla.hassan@example.com",
                    "folder_link": "https://drive.google.com/demo-employee-layla",
                    "created_at": dt.datetime.utcnow().isoformat(),
                },
                "E-002": {
                    "name": "Omar Saleh",
                    "title": "Finance Analyst",
                    "email": "omar.saleh@example.com",
                    "folder_link": "/Users/omar/Documents/Finance",
                    "created_at": dt.datetime.utcnow().isoformat(),
                },
                "E-003": {
                    "name": "Sara Ibrahim",
                    "title": "IT Support Engineer",
                    "email": "sara.ibrahim@example.com",
                    "folder_link": "https://drive.google.com/demo-employee-sara",
                    "created_at": dt.datetime.utcnow().isoformat(),
                },
            },
            "leave_requests": [
                {
                    "id": "LR-1001",
                    "employee_id": "E-001",
                    "start_date": "2024-09-01",
                    "end_date": "2024-09-05",
                    "reason": "Family trip",
                    "created_at": dt.datetime.utcnow().isoformat(),
                    "pdf_path": "leave_request_E-001_LR-1001.pdf",
                },
                {
                    "id": "LR-1002",
                    "employee_id": "E-003",
                    "start_date": "2024-10-15",
                    "end_date": "2024-10-18",
                    "reason": "Technical conference",
                    "created_at": dt.datetime.utcnow().isoformat(),
                    "pdf_path": "leave_request_E-003_LR-1002.pdf",
                },
            ],
            "asset_handovers": [
                {
                    "id": "AH-2001",
                    "employee_id": "E-002",
                    "asset_name": "MacBook Pro 14",
                    "asset_tag": "MBP-14-2023-021",
                    "notes": "Finance tools pre-installed",
                    "created_at": dt.datetime.utcnow().isoformat(),
                    "pdf_path": "asset_handover_E-002_AH-2001.pdf",
                },
                {
                    "id": "AH-2002",
                    "employee_id": "E-003",
                    "asset_name": "iPhone 14",
                    "asset_tag": "IPH-14-009",
                    "notes": "For on-call support",
                    "created_at": dt.datetime.utcnow().isoformat(),
                    "pdf_path": "asset_handover_E-003_AH-2002.pdf",
                },
            ],
        }

    def save(self) -> None:
        self.path.write_text(json.dumps(self.data, indent=2, ensure_ascii=False))

    def list_employees(self) -> List[Dict[str, str]]:
        return [dict({"id": emp_id}, **payload) for emp_id, payload in self.data.get("employees", {}).items()]

    def add_employee(self, emp_id: str, name: str, title: str, email: str, folder: Optional[str]) -> None:
        employees: Dict[str, Dict[str, str]] = self.data.setdefault("employees", {})
        if emp_id in employees:
            raise ValueError(f"Employee with id {emp_id} already exists.")
        employees[emp_id] = {
            "name": name,
            "title": title,
            "email": email,
            "folder_link": folder or "",
            "created_at": dt.datetime.utcnow().isoformat(),
        }
        self.save()

    def get_employee(self, emp_id: str) -> Optional[Dict[str, str]]:
        employee = self.data.get("employees", {}).get(emp_id)
        if not employee:
            return None
        return dict({"id": emp_id}, **employee)

    def add_leave_request(self, emp_id: str, start_date: str, end_date: str, reason: str, pdf_path: Path) -> Dict[str, str]:
        request = {
            "id": f"LR-{uuid.uuid4().hex[:8].upper()}",
            "employee_id": emp_id,
            "start_date": start_date,
            "end_date": end_date,
            "reason": reason,
            "created_at": dt.datetime.utcnow().isoformat(),
            "pdf_path": pdf_path.name,
        }
        self.data.setdefault("leave_requests", []).append(request)
        self.save()
        return request

    def add_asset_handover(
        self, emp_id: str, asset_name: str, asset_tag: str, notes: str, pdf_path: Path
    ) -> Dict[str, str]:
        handover = {
            "id": f"AH-{uuid.uuid4().hex[:8].upper()}",
            "employee_id": emp_id,
            "asset_name": asset_name,
            "asset_tag": asset_tag,
            "notes": notes,
            "created_at": dt.datetime.utcnow().isoformat(),
            "pdf_path": pdf_path.name,
        }
        self.data.setdefault("asset_handovers", []).append(handover)
        self.save()
        return handover

    def list_leave_requests(self) -> List[Dict[str, str]]:
        return list(self.data.get("leave_requests", []))

    def list_asset_handovers(self) -> List[Dict[str, str]]:
        return list(self.data.get("asset_handovers", []))

    def stats(self) -> Dict[str, int]:
        return {
            "employees": len(self.data.get("employees", {})),
            "leave_requests": len(self.data.get("leave_requests", [])),
            "asset_handovers": len(self.data.get("asset_handovers", [])),
        }


store = HRDataStore()


def _ensure_dirs(*dirs: Path) -> None:
    for directory in dirs:
        directory.mkdir(parents=True, exist_ok=True)


def _draw_header(pdf: canvas.Canvas, title: str) -> None:
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(72, 780, title)
    pdf.setFont("Helvetica", 10)
    pdf.drawString(72, 760, f"Generated on {dt.datetime.now().strftime('%Y-%m-%d %H:%M')}")


def _draw_footer(pdf: canvas.Canvas) -> None:
    pdf.setFont("Helvetica-Oblique", 9)
    pdf.drawString(72, 40, "Signature: ______________________")
    pdf.drawRightString(540, 40, "HR Mini System")


def _draw_paragraph(pdf: canvas.Canvas, text: str, x: int, y: int, width: int) -> int:
    style = ParagraphStyle(name="Body", fontName="Helvetica", fontSize=12, leading=16)
    para = Paragraph(text, style=style)
    _, height = para.wrap(width, 800)
    para.drawOn(pdf, x, y - height)
    return y - height - 12


def generate_leave_pdf(employee: Dict[str, str], request: Dict[str, str], output_path: Path) -> None:
    _ensure_dirs(FORMS_DIR)
    pdf = canvas.Canvas(str(output_path), pagesize=A4)
    _draw_header(pdf, "Leave Request (نموذج إجازة)")

    y = 720
    pdf.setFont("Helvetica", 12)
    pdf.drawString(72, y, f"Employee: {employee['name']} ({employee['id']})")
    y -= 20
    pdf.drawString(72, y, f"Role: {employee['title']}")
    y -= 20
    pdf.drawString(72, y, f"Email: {employee['email']}")
    y -= 20
    if employee.get("folder_link"):
        pdf.drawString(72, y, f"Folder: {employee['folder_link']}")
        y -= 20

    text = f"Leave dates: {request['start_date']} → {request['end_date']}<br/>Reason: {request['reason']}"
    y = _draw_paragraph(pdf, text, 72, y, 450)

    _draw_footer(pdf)
    pdf.showPage()
    pdf.save()


def generate_asset_pdf(employee: Dict[str, str], handover: Dict[str, str], output_path: Path) -> None:
    _ensure_dirs(FORMS_DIR)
    pdf = canvas.Canvas(str(output_path), pagesize=A4)
    _draw_header(pdf, "Asset Handover (تسليم عهدة)")

    y = 720
    pdf.setFont("Helvetica", 12)
    pdf.drawString(72, y, f"Employee: {employee['name']} ({employee['id']})")
    y -= 20
    pdf.drawString(72, y, f"Role: {employee['title']}")
    y -= 20
    pdf.drawString(72, y, f"Email: {employee['email']}")
    y -= 20

    lines = [
        f"Asset: {handover['asset_name']}",
        f"Asset tag/serial: {handover['asset_tag']}",
        f"Notes: {handover['notes'] or 'N/A'}",
    ]
    text = "<br/>".join(lines)
    y = _draw_paragraph(pdf, text, 72, y, 450)

    pdf.setFont("Helvetica", 12)
    pdf.drawString(72, y, "Employee signature: ______________________")
    y -= 18
    pdf.drawString(72, y, "Receiver signature: ______________________")

    _draw_footer(pdf)
    pdf.showPage()
    pdf.save()


def generate_report_pdf(
    employees: Dict[str, Dict[str, str]],
    leave_requests: List[Dict[str, str]],
    handovers: List[Dict[str, str]],
    output_path: Path,
) -> None:
    _ensure_dirs(REPORTS_DIR)
    pdf = canvas.Canvas(str(output_path), pagesize=A4)
    _draw_header(pdf, "HR Reports")

    y = 720
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(72, y, "Leave Requests")
    y -= 16
    pdf.setFont("Helvetica", 11)
    for req in leave_requests:
        employee = employees.get(req["employee_id"], {})
        line = (
            f"{req['start_date']} → {req['end_date']} | {employee.get('name', req['employee_id'])} |"
            f" Reason: {req['reason']}"
        )
        pdf.drawString(72, y, line)
        y -= 16
        if y < 150:
            _draw_footer(pdf)
            pdf.showPage()
            y = 760
    y -= 12
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(72, y, "Asset Handovers")
    y -= 16
    pdf.setFont("Helvetica", 11)
    for handover in handovers:
        employee = employees.get(handover["employee_id"], {})
        line = (
            f"{handover['asset_name']} ({handover['asset_tag']}) | {employee.get('name', handover['employee_id'])}"
            f" | Notes: {handover['notes']}"
        )
        pdf.drawString(72, y, line)
        y -= 16
        if y < 150:
            _draw_footer(pdf)
            pdf.showPage()
            y = 760

    _draw_footer(pdf)
    pdf.showPage()
    pdf.save()


app = Flask(__name__)
app.secret_key = "hr-mini-system-secret"


@app.context_processor
def inject_common_data() -> Dict[str, object]:
    return {"nav_counts": store.stats()}


@app.route("/")
def dashboard() -> str:
    stats = store.stats()
    employees = store.list_employees()
    leave_requests = store.list_leave_requests()
    handovers = store.list_asset_handovers()
    recent_leave = sorted(leave_requests, key=lambda x: x["created_at"], reverse=True)[:3]
    recent_handover = sorted(handovers, key=lambda x: x["created_at"], reverse=True)[:3]
    return render_template(
        "dashboard.html",
        stats=stats,
        employees=employees,
        recent_leave=recent_leave,
        recent_handover=recent_handover,
    )


@app.route("/employees", methods=["GET", "POST"])
def employees() -> str:
    error: Optional[str] = None
    if request.method == "POST":
        emp_id = request.form.get("emp_id", "").strip()
        name = request.form.get("name", "").strip()
        title = request.form.get("title", "").strip()
        email = request.form.get("email", "").strip()
        folder = request.form.get("folder", "").strip()
        if not all([emp_id, name, title, email]):
            error = "Please fill in all required fields."
        else:
            try:
                store.add_employee(emp_id, name, title, email, folder)
                flash(f"Employee {name} added successfully", "success")
                return redirect(url_for("employees"))
            except ValueError as exc:
                error = str(exc)
    query = request.args.get("q", "").lower()
    employees_list = store.list_employees()
    if query:
        employees_list = [
            emp
            for emp in employees_list
            if query in emp["name"].lower()
            or query in emp["title"].lower()
            or query in emp["email"].lower()
            or query in emp["id"].lower()
        ]
    return render_template("employees.html", employees=employees_list, query=query, error=error)


@app.route("/employees/<emp_id>")
def employee_detail(emp_id: str) -> Response | str:
    employee = store.get_employee(emp_id)
    if not employee:
        flash("Employee not found", "error")
        return redirect(url_for("employees"))
    leave_requests = [req for req in store.list_leave_requests() if req["employee_id"] == emp_id]
    handovers = [ho for ho in store.list_asset_handovers() if ho["employee_id"] == emp_id]
    return render_template(
        "employee_detail.html",
        employee=employee,
        leave_requests=leave_requests,
        handovers=handovers,
    )


@app.route("/leave-requests", methods=["GET", "POST"])
def leave_requests() -> str:
    error: Optional[str] = None
    employees = store.list_employees()
    if request.method == "POST":
        emp_id = request.form.get("employee_id", "").strip()
        start_date = request.form.get("start_date", "").strip()
        end_date = request.form.get("end_date", "").strip()
        reason = request.form.get("reason", "").strip()
        if not all([emp_id, start_date, end_date, reason]):
            error = "All fields are required."
        else:
            employee = store.get_employee(emp_id)
            if not employee:
                error = "Employee not found."
            else:
                pdf_path = FORMS_DIR / f"leave_request_{emp_id}_{uuid.uuid4().hex[:6]}.pdf"
                record = store.add_leave_request(emp_id, start_date, end_date, reason, pdf_path)
                generate_leave_pdf(employee, record, pdf_path)
                flash("Leave request saved and PDF generated.", "success")
                return redirect(url_for("leave_requests"))

    filter_emp = request.args.get("employee_id", "").strip()
    requests_list = store.list_leave_requests()
    if filter_emp:
        requests_list = [req for req in requests_list if req["employee_id"] == filter_emp]
    return render_template(
        "leave_requests.html",
        employees=employees,
        requests=requests_list,
        filter_emp=filter_emp,
        error=error,
    )


@app.route("/asset-handovers", methods=["GET", "POST"])
def asset_handovers() -> str:
    error: Optional[str] = None
    employees = store.list_employees()
    if request.method == "POST":
        emp_id = request.form.get("employee_id", "").strip()
        asset_name = request.form.get("asset_name", "").strip()
        asset_tag = request.form.get("asset_tag", "").strip()
        notes = request.form.get("notes", "").strip()
        if not all([emp_id, asset_name, asset_tag]):
            error = "Employee, asset name, and asset tag are required."
        else:
            employee = store.get_employee(emp_id)
            if not employee:
                error = "Employee not found."
            else:
                pdf_path = FORMS_DIR / f"asset_handover_{emp_id}_{uuid.uuid4().hex[:6]}.pdf"
                record = store.add_asset_handover(emp_id, asset_name, asset_tag, notes, pdf_path)
                generate_asset_pdf(employee, record, pdf_path)
                flash("Asset handover saved and PDF generated.", "success")
                return redirect(url_for("asset_handovers"))

    filter_emp = request.args.get("employee_id", "").strip()
    handovers_list = store.list_asset_handovers()
    if filter_emp:
        handovers_list = [ho for ho in handovers_list if ho["employee_id"] == filter_emp]
    return render_template(
        "asset_handovers.html",
        employees=employees,
        handovers=handovers_list,
        filter_emp=filter_emp,
        error=error,
    )


@app.route("/reports")
def reports() -> str:
    employees = store.data.get("employees", {})
    leave_requests = store.list_leave_requests()
    handovers = store.list_asset_handovers()
    return render_template(
        "reports.html",
        employees=employees,
        leave_requests=leave_requests,
        handovers=handovers,
    )


@app.route("/reports/export")
def export_reports() -> Response:
    pdf_path = REPORTS_DIR / f"hr_reports_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    generate_report_pdf(store.data.get("employees", {}), store.list_leave_requests(), store.list_asset_handovers(), pdf_path)
    flash("Report PDF generated.", "success")
    return send_file(pdf_path, as_attachment=True)


@app.route("/forms_pdfs/<path:filename>")
def serve_form_pdf(filename: str) -> Response:
    return send_from_directory(FORMS_DIR, filename)


@app.route("/reports/<path:filename>")
def serve_report_file(filename: str) -> Response:
    return send_from_directory(REPORTS_DIR, filename)


def run() -> None:
    """Run the Flask development server."""
    _ensure_dirs(FORMS_DIR, REPORTS_DIR)
    app.run(host="0.0.0.0", port=5000, debug=False)


if __name__ == "__main__":
    run()

# --- Quickstart (macOS) ---
# 1) Install dependencies:  python -m pip install -r requirements.txt
# 2) Start the app:         python hr_system.py
# 3) Open your browser:     http://localhost:5000
