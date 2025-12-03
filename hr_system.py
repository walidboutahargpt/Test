"""Lightweight HR mini-system CLI.

Features:
- Employee profile management with link to Google Drive or local folder.
- Generate leave request and asset handover forms as Markdown files (print-ready).
- Persist data in a JSON datastore (hr_data.json by default).
- Produce summary reports for leave requests and asset handovers.

The CLI is intentionally minimal so it runs smoothly on macOS without extra services.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Dict, List, Optional

DATA_FILE = Path("hr_data.json")
FORMS_DIR = Path("forms")
REPORTS_DIR = Path("reports")


class HRDataStore:
    """Simple JSON-backed datastore for the HR system."""

    def __init__(self, path: Path = DATA_FILE):
        self.path = path
        self.data = {"employees": {}, "leave_requests": [], "asset_handovers": []}
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            try:
                self.data = json.loads(self.path.read_text())
            except json.JSONDecodeError:
                raise SystemExit(f"Data file {self.path} is corrupted; please fix or remove it.")

    def save(self) -> None:
        self.path.write_text(json.dumps(self.data, indent=2, ensure_ascii=False))

    # Employee helpers
    def add_employee(self, emp_id: str, name: str, title: str, email: str, folder: Optional[str]) -> None:
        employees: Dict[str, Dict[str, str]] = self.data.setdefault("employees", {})
        if emp_id in employees:
            raise SystemExit(f"Employee with id {emp_id} already exists.")
        employees[emp_id] = {
            "name": name,
            "title": title,
            "email": email,
            "folder_link": folder or "",
            "created_at": dt.datetime.utcnow().isoformat(),
        }
        self.save()

    def update_employee(self, emp_id: str, **fields: str) -> None:
        employees = self.data.get("employees", {})
        if emp_id not in employees:
            raise SystemExit(f"Employee {emp_id} not found.")
        employees[emp_id].update({k: v for k, v in fields.items() if v is not None})
        self.save()

    def get_employee(self, emp_id: str) -> Dict[str, str]:
        employees = self.data.get("employees", {})
        if emp_id not in employees:
            raise SystemExit(f"Employee {emp_id} not found.")
        return employees[emp_id]

    # Leave requests
    def add_leave_request(
        self, emp_id: str, start_date: str, end_date: str, reason: str, output_path: Path
    ) -> Dict[str, str]:
        request = {
            "employee_id": emp_id,
            "start_date": start_date,
            "end_date": end_date,
            "reason": reason,
            "created_at": dt.datetime.utcnow().isoformat(),
            "form_path": str(output_path),
        }
        self.data.setdefault("leave_requests", []).append(request)
        self.save()
        return request

    # Asset handovers
    def add_asset_handover(
        self, emp_id: str, asset_name: str, asset_tag: str, notes: str, output_path: Path
    ) -> Dict[str, str]:
        handover = {
            "employee_id": emp_id,
            "asset_name": asset_name,
            "asset_tag": asset_tag,
            "notes": notes,
            "created_at": dt.datetime.utcnow().isoformat(),
            "form_path": str(output_path),
        }
        self.data.setdefault("asset_handovers", []).append(handover)
        self.save()
        return handover


# Utility helpers

def _ensure_dirs(*dirs: Path) -> None:
    for directory in dirs:
        directory.mkdir(parents=True, exist_ok=True)


def _write_form(output_path: Path, content: str) -> None:
    output_path.write_text(content)
    print(f"Form saved to {output_path.resolve()}")


def _format_header(title: str) -> str:
    return f"# {title}\nGenerated on {dt.datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"


def _profile_snippet(employee: Dict[str, str]) -> str:
    lines = [f"- Employee: {employee['name']} ({employee['email']})", f"- Role: {employee['title']}"]
    if employee.get("folder_link"):
        lines.append(f"- Folder link: {employee['folder_link']}")
    return "\n".join(lines) + "\n"


# Command handlers

def create_employee(args: argparse.Namespace) -> None:
    store = HRDataStore(Path(args.data_file))
    store.add_employee(args.id, args.name, args.title, args.email, args.folder)
    print(f"Created employee {args.id} - {args.name}")


def show_employee(args: argparse.Namespace) -> None:
    store = HRDataStore(Path(args.data_file))
    employee = store.get_employee(args.id)
    print(_format_header("Employee Profile"))
    print(_profile_snippet(employee))


def leave_request(args: argparse.Namespace) -> None:
    store = HRDataStore(Path(args.data_file))
    employee = store.get_employee(args.id)
    _ensure_dirs(FORMS_DIR)
    output_path = FORMS_DIR / f"leave_request_{args.id}_{args.start_date}_to_{args.end_date}.md"
    content = _format_header("Leave Request (نموذج إجازة)")
    content += _profile_snippet(employee)
    content += f"- Leave dates: {args.start_date} → {args.end_date}\n- Reason: {args.reason}\n"
    content += "\nSignature: ______________________\n"
    _write_form(output_path, content)
    store.add_leave_request(args.id, args.start_date, args.end_date, args.reason, output_path)


def asset_handover(args: argparse.Namespace) -> None:
    store = HRDataStore(Path(args.data_file))
    employee = store.get_employee(args.id)
    _ensure_dirs(FORMS_DIR)
    output_path = FORMS_DIR / f"asset_handover_{args.id}_{args.asset_tag}.md"
    content = _format_header("Asset Handover (تسليم عهدة)")
    content += _profile_snippet(employee)
    content += f"- Asset: {args.asset_name}\n- Asset tag/serial: {args.asset_tag}\n- Notes: {args.notes}\n"
    content += "\nEmployee signature: ______________________\nReceiver signature: ______________________\n"
    _write_form(output_path, content)
    store.add_asset_handover(args.id, args.asset_name, args.asset_tag, args.notes, output_path)


def reports(args: argparse.Namespace) -> None:
    store = HRDataStore(Path(args.data_file))
    _ensure_dirs(REPORTS_DIR)
    report_path = REPORTS_DIR / "hr_reports.md"
    lines: List[str] = [
        _format_header("HR Reports"),
        "## Leave Requests\n",
    ]
    for req in store.data.get("leave_requests", []):
        employee = store.data.get("employees", {}).get(req["employee_id"], {})
        lines.append(
            f"- {req['start_date']} → {req['end_date']} | {employee.get('name', req['employee_id'])} | Reason: {req['reason']} | Form: {req['form_path']}\n"
        )
    lines.append("\n## Asset Handovers\n")
    for handover in store.data.get("asset_handovers", []):
        employee = store.data.get("employees", {}).get(handover["employee_id"], {})
        lines.append(
            f"- {handover['asset_name']} ({handover['asset_tag']}) | {employee.get('name', handover['employee_id'])} | Notes: {handover['notes']} | Form: {handover['form_path']}\n"
        )
    report_path.write_text("".join(lines))
    print(f"Report saved to {report_path.resolve()}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Lightweight HR mini-system")
    parser.add_argument("--data-file", default=str(DATA_FILE), help="Path to JSON datastore (default: hr_data.json)")

    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create-employee", help="Create a new employee profile")
    create.add_argument("--id", required=True, help="Employee ID")
    create.add_argument("--name", required=True, help="Full name")
    create.add_argument("--title", required=True, help="Job title")
    create.add_argument("--email", required=True, help="Email address")
    create.add_argument("--folder", help="Google Drive link or local folder path")
    create.set_defaults(func=create_employee)

    show = subparsers.add_parser("show-employee", help="Display an employee profile")
    show.add_argument("--id", required=True, help="Employee ID")
    show.set_defaults(func=show_employee)

    leave = subparsers.add_parser("leave-request", help="Generate a leave request form")
    leave.add_argument("--id", required=True, help="Employee ID")
    leave.add_argument("--start-date", required=True, help="Start date (YYYY-MM-DD)")
    leave.add_argument("--end-date", required=True, help="End date (YYYY-MM-DD)")
    leave.add_argument("--reason", required=True, help="Reason for leave")
    leave.set_defaults(func=leave_request)

    handover = subparsers.add_parser("asset-handover", help="Generate an asset handover form")
    handover.add_argument("--id", required=True, help="Employee ID")
    handover.add_argument("--asset-name", required=True, help="Asset name")
    handover.add_argument("--asset-tag", required=True, help="Asset tag/serial")
    handover.add_argument("--notes", default="", help="Additional notes")
    handover.set_defaults(func=asset_handover)

    report_cmd = subparsers.add_parser("reports", help="Generate HR summary reports")
    report_cmd.set_defaults(func=reports)

    return parser


def main(argv: Optional[List[str]] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
