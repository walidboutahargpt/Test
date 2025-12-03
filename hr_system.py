"""Streamlit-based HR mini-system with PDF generation.

Features:
- Modern Streamlit UI with dashboard, employees, leave requests, asset handovers, and reports.
- JSON datastore with automatic seeding of demo data on first run.
- PDF generation for leave requests, asset handovers, and consolidated reports.
- macOS-friendly setup with lightweight dependencies.
"""
from __future__ import annotations

import datetime as dt
import json
import sys
import uuid
from pathlib import Path
from typing import Dict, List, Optional

import streamlit as st
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


# --- Streamlit UI helpers -------------------------------------------------


def render_header(title: str, subtitle: str | None = None) -> None:
    st.markdown(f"## {title}")
    if subtitle:
        st.caption(subtitle)


def render_dashboard() -> None:
    stats = store.stats()
    employees = store.list_employees()
    leave_requests = store.list_leave_requests()
    handovers = store.list_asset_handovers()

    st.markdown("### Quick stats")
    c1, c2, c3 = st.columns(3)
    c1.metric("Employees", stats["employees"])
    c2.metric("Leave Requests", stats["leave_requests"])
    c3.metric("Asset Handovers", stats["asset_handovers"])

    st.markdown("### Latest activity")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Recent Leave Requests (نموذج إجازة)**")
        for req in sorted(leave_requests, key=lambda r: r["created_at"], reverse=True)[:3]:
            emp = next((e for e in employees if e["id"] == req["employee_id"]), None)
            st.write(f"• {req['start_date']} → {req['end_date']} — {emp['name'] if emp else req['employee_id']}")
    with col2:
        st.markdown("**Recent Asset Handovers (تسليم عهدة)**")
        for handover in sorted(handovers, key=lambda h: h["created_at"], reverse=True)[:3]:
            emp = next((e for e in employees if e["id"] == handover["employee_id"]), None)
            st.write(
                f"• {handover['asset_name']} ({handover['asset_tag']}) — {emp['name'] if emp else handover['employee_id']}"
            )


def render_employees() -> None:
    render_header("Employees", "Directory with search and quick links")
    query = st.text_input("Search by name, title, email, or ID", key="emp-search")
    employees = store.list_employees()
    if query:
        employees = [
            emp
            for emp in employees
            if query.lower() in emp["name"].lower()
            or query.lower() in emp["title"].lower()
            or query.lower() in emp["email"].lower()
            or query.lower() in emp["id"].lower()
        ]

    st.dataframe(
        employees,
        use_container_width=True,
        hide_index=True,
        column_config={
            "id": "Employee ID",
            "name": "Name",
            "title": "Title",
            "email": "Email",
            "folder_link": "Folder link",
            "created_at": None,
        },
    )

    with st.expander("Add new employee"):
        emp_id = st.text_input("Employee ID", key="emp-id")
        name = st.text_input("Full name", key="emp-name")
        title = st.text_input("Title", key="emp-title")
        email = st.text_input("Email", key="emp-email")
        folder = st.text_input("Google Drive / local folder link", key="emp-folder")
        if st.button("Save employee"):
            if not all([emp_id, name, title, email]):
                st.error("Please fill in all required fields.")
            else:
                try:
                    store.add_employee(emp_id.strip(), name.strip(), title.strip(), email.strip(), folder.strip())
                    st.success(f"Employee {name} added successfully.")
                except ValueError as exc:
                    st.error(str(exc))

    st.markdown("---")
    st.markdown("### Employee details")
    selected = st.selectbox("View employee", [emp["id"] for emp in store.list_employees()])
    employee = store.get_employee(selected)
    if employee:
        st.subheader(employee["name"])
        st.write(f"**ID:** {employee['id']}")
        st.write(f"**Title:** {employee['title']}")
        st.write(f"**Email:** {employee['email']}")
        if employee.get("folder_link"):
            st.write(f"**Folder:** {employee['folder_link']}")

        leave_requests = [req for req in store.list_leave_requests() if req["employee_id"] == employee["id"]]
        handovers = [ho for ho in store.list_asset_handovers() if ho["employee_id"] == employee["id"]]
        st.markdown("**Leave Requests (نموذج إجازة):**")
        st.dataframe(leave_requests, use_container_width=True, hide_index=True)
        st.markdown("**Asset Handovers (تسليم عهدة):**")
        st.dataframe(handovers, use_container_width=True, hide_index=True)


def render_leave_requests() -> None:
    render_header("Leave Requests (نموذج إجازة)", "Create and browse leave forms")
    employees = store.list_employees()
    emp_options = {f"{emp['name']} ({emp['id']})": emp["id"] for emp in employees}

    with st.form("leave-form"):
        employee_choice = st.selectbox("Employee", list(emp_options.keys()))
        start_date = st.date_input("Start date")
        end_date = st.date_input("End date")
        reason = st.text_area("Reason")
        submitted = st.form_submit_button("Save & generate PDF")

    if submitted:
        emp_id = emp_options[employee_choice]
        employee = store.get_employee(emp_id)
        if not employee:
            st.error("Employee not found.")
        else:
            pdf_path = FORMS_DIR / f"leave_request_{emp_id}_{uuid.uuid4().hex[:6]}.pdf"
            record = store.add_leave_request(
                emp_id,
                start_date.isoformat(),
                end_date.isoformat(),
                reason.strip(),
                pdf_path,
            )
            generate_leave_pdf(employee, record, pdf_path)
            st.success("Leave request saved and PDF generated.")
            st.download_button("Download PDF", pdf_path.read_bytes(), file_name=pdf_path.name)

    st.markdown("---")
    filter_emp = st.selectbox("Filter by employee", ["All"] + list(emp_options.keys()))
    requests_list = store.list_leave_requests()
    if filter_emp != "All":
        selected_id = emp_options[filter_emp]
        requests_list = [req for req in requests_list if req["employee_id"] == selected_id]
    st.dataframe(requests_list, use_container_width=True, hide_index=True)

    st.markdown("Existing PDFs")
    _ensure_dirs(FORMS_DIR)
    for pdf in sorted(FORMS_DIR.glob("leave_request_*.pdf")):
        st.write(f"• {pdf.name}")


def render_asset_handovers() -> None:
    render_header("Asset Handovers (تسليم عهدة)", "Capture and track company assets")
    employees = store.list_employees()
    emp_options = {f"{emp['name']} ({emp['id']})": emp["id"] for emp in employees}

    with st.form("asset-form"):
        employee_choice = st.selectbox("Employee", list(emp_options.keys()), key="asset-emp")
        asset_name = st.text_input("Asset name")
        asset_tag = st.text_input("Asset tag / serial")
        notes = st.text_area("Notes")
        submitted = st.form_submit_button("Save & generate PDF")

    if submitted:
        emp_id = emp_options[employee_choice]
        employee = store.get_employee(emp_id)
        if not employee:
            st.error("Employee not found.")
        else:
            pdf_path = FORMS_DIR / f"asset_handover_{emp_id}_{uuid.uuid4().hex[:6]}.pdf"
            record = store.add_asset_handover(emp_id, asset_name.strip(), asset_tag.strip(), notes.strip(), pdf_path)
            generate_asset_pdf(employee, record, pdf_path)
            st.success("Asset handover saved and PDF generated.")
            st.download_button("Download PDF", pdf_path.read_bytes(), file_name=pdf_path.name)

    st.markdown("---")
    filter_emp = st.selectbox("Filter by employee", ["All"] + list(emp_options.keys()), key="asset-filter")
    handovers_list = store.list_asset_handovers()
    if filter_emp != "All":
        selected_id = emp_options[filter_emp]
        handovers_list = [ho for ho in handovers_list if ho["employee_id"] == selected_id]
    st.dataframe(handovers_list, use_container_width=True, hide_index=True)

    st.markdown("Existing PDFs")
    _ensure_dirs(FORMS_DIR)
    for pdf in sorted(FORMS_DIR.glob("asset_handover_*.pdf")):
        st.write(f"• {pdf.name}")


def render_reports() -> None:
    render_header("Reports", "Summaries plus PDF export")
    employees = store.data.get("employees", {})
    leave_requests = store.list_leave_requests()
    handovers = store.list_asset_handovers()

    st.markdown("### Leave requests")
    st.dataframe(leave_requests, use_container_width=True, hide_index=True)

    st.markdown("### Asset handovers")
    st.dataframe(handovers, use_container_width=True, hide_index=True)

    if st.button("Generate PDF report"):
        pdf_path = REPORTS_DIR / f"hr_reports_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        generate_report_pdf(employees, leave_requests, handovers, pdf_path)
        st.success("Report PDF generated.")
        st.download_button("Download report", pdf_path.read_bytes(), file_name=pdf_path.name)

    st.markdown("Existing reports")
    _ensure_dirs(REPORTS_DIR)
    for pdf in sorted(REPORTS_DIR.glob("hr_reports_*.pdf")):
        st.write(f"• {pdf.name}")


# --- Entrypoint -----------------------------------------------------------


def main() -> None:
    _ensure_dirs(FORMS_DIR, REPORTS_DIR)
    st.set_page_config(page_title="HR Mini-System", layout="wide")
    st.sidebar.title("HR Mini-System")
    page = st.sidebar.radio(
        "Navigation",
        ["Dashboard", "Employees", "Leave Requests", "Asset Handovers", "Reports"],
    )

    if page == "Dashboard":
        render_dashboard()
    elif page == "Employees":
        render_employees()
    elif page == "Leave Requests":
        render_leave_requests()
    elif page == "Asset Handovers":
        render_asset_handovers()
    elif page == "Reports":
        render_reports()

    st.sidebar.markdown("---")
    st.sidebar.info("Run via `streamlit run hr_system.py` on macOS.")


def run() -> None:
    """Allow `python hr_system.py` to launch the Streamlit app."""
    import streamlit.web.cli as stcli

    sys.argv = ["streamlit", "run", str(Path(__file__).resolve())]
    sys.exit(stcli.main())


if __name__ == "__main__":
    run()

# --- Quickstart (macOS) ---
# 1) Install dependencies:  python -m pip install -r requirements.txt
# 2) Start the app:         streamlit run hr_system.py   # or: python hr_system.py
# 3) Open your browser:     http://localhost:8501
