import os
import re
import uuid
import hashlib
import base64
import json
from io import BytesIO
from datetime import date
import pandas as pd
import streamlit as st
try:
    from dotenv import load_dotenv
    _DOTENV_AVAILABLE = True
except Exception:
    # If python-dotenv is not installed in the environment, provide
    # a noop fallback and let the app continue (Streamlit will show
    # a warning later if required env vars are missing).
    def load_dotenv(*args, **kwargs):
        return False

    _DOTENV_AVAILABLE = False
from supabase import create_client, Client
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from datetime import date, datetime


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="School Management System",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

# Load .env
load_dotenv()

def get_setting(name):
    value = os.getenv(name)
    if value:
        return value

    try:
        return st.secrets[name]
    except Exception:
        return None


# Get Supabase credentials
SUPABASE_URL = get_setting("SUPABASE_URL")
SUPABASE_KEY = get_setting("SUPABASE_KEY")

# Check credentials
if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("Supabase URL or Key is missing. Add SUPABASE_URL and SUPABASE_KEY to Streamlit secrets.")
    st.stop()

# Connect Supabase
@st.cache_resource
def init_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSET_PATHS = [
    os.path.join(BASE_DIR, "assets", "s.png"),
    os.path.join(os.path.dirname(BASE_DIR), "assets", "s.png"),
    os.path.join(BASE_DIR, "venv", "assets", "s.png"),
]
LOGIN_IMAGE_PATH = next(
    (path for path in ASSET_PATHS if os.path.isfile(path)),
    None
)


# =========================================================
# PREMIUM DASHBOARD THEME
# =========================================================

st.markdown(
    """
    <style>

    .stApp {
        background:
            radial-gradient(circle at top left, rgba(56, 189, 248, 0.20), transparent 25%),
            radial-gradient(circle at top right, rgba(192, 132, 252, 0.22), transparent 30%),
            linear-gradient(135deg, #020617 0%, #0f172a 45%, #111827 100%);
        color: #f8fafc;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(2, 6, 23, 0.98), rgba(15, 23, 42, 0.95));
        border-right: 1px solid rgba(148, 163, 184, 0.18);
    }

    [data-testid="stSidebar"] * {
        color: #f8fafc !important;
    }

    h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
    }

    p, label, span {
        color: #e2e8f0 !important;
    }

    .stTextInput input,
    .stTextArea textarea,
    .stNumberInput input {
        background-color: rgba(15, 23, 42, 0.9) !important;
        color: #ffffff !important;
        border: 1px solid rgba(96, 165, 250, 0.35) !important;
        border-radius: 10px !important;
    }

    [data-baseweb="select"] > div {
        background-color: rgba(15, 23, 42, 0.9) !important;
        color: white !important;
    }

    .stButton > button {
        background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
        color: white;
        border-radius: 999px;
        border: none;
        font-weight: 700;
        padding: 0.55rem 1.2rem;
        box-shadow: 0 8px 20px rgba(59, 130, 246, 0.24);
    }

    .stButton > button:hover {
        background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
        transform: translateY(-1px);
    }

    [data-testid="stMetric"] {
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.95), rgba(30, 41, 59, 0.9));
        border: 1px solid rgba(125, 211, 252, 0.25);
        border-radius: 16px;
        padding: 16px;
        box-shadow: 0 10px 25px rgba(2, 8, 23, 0.28);
    }

    .school-card {
        background: rgba(15, 23, 42, 0.72);
        border: 1px solid rgba(125, 211, 252, 0.2);
        border-radius: 18px;
        padding: 24px;
        margin-bottom: 20px;
        backdrop-filter: blur(16px);
        box-shadow: 0 14px 40px rgba(2, 8, 23, 0.35);
        animation: fadeIn 1.2s ease-in-out;
    }

    .login-panel {
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.92), rgba(59, 130, 246, 0.90), rgba(139, 92, 246, 0.9));
        border: 1px solid rgba(255,255,255,0.16);
        border-radius: 22px;
        padding: 24px;
        box-shadow: 0 18px 45px rgba(2, 8, 23, 0.35);
        animation: slideUp 0.9s ease-out;
    }

    .hero-card {
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.95), rgba(37, 99, 235, 0.75), rgba(147, 51, 234, 0.75));
        border: 1px solid rgba(255,255,255,0.18);
        border-radius: 24px;
        padding: 28px;
        margin-bottom: 18px;
        box-shadow: 0 16px 40px rgba(2, 8, 23, 0.3);
    }

    .hero-badge {
        display: inline-block;
        padding: 0.35rem 0.7rem;
        background: rgba(255,255,255,0.12);
        border: 1px solid rgba(255,255,255,0.18);
        border-radius: 999px;
        font-size: 0.8rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 0.75rem;
    }

    .hero-card h1, .hero-card h2 {
        margin: 0 0 0.5rem 0;
        color: #ffffff !important;
    }

    .hero-card p {
        margin: 0;
        color: #e0f2fe !important;
        font-size: 1rem;
    }

    .animated-glow {
        position: relative;
        overflow: hidden;
    }

    .animated-glow::after {
        content: "";
        position: absolute;
        inset: -2px;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.18), transparent);
        transform: translateX(-120%);
        animation: shimmer 2.6s infinite;
    }

    [data-testid="stTab"] {
        color: #cbd5e1 !important;
    }

    [data-testid="stTab"][aria-selected="true"] {
        color: #ffffff !important;
        background: rgba(59, 130, 246, 0.18);
        border-radius: 10px;
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(8px); }
        to { opacity: 1; transform: translateY(0); }
    }

    @keyframes slideUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }

    @keyframes shimmer {
        100% { transform: translateX(120%); }
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# SESSION STATE
# =========================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "role" not in st.session_state:
    st.session_state.role = ""

if "username" not in st.session_state:
    st.session_state.username = ""

if "admission_no" not in st.session_state:
    st.session_state.admission_no = ""

if "principal_logged_in" not in st.session_state:
    st.session_state.principal_logged_in = False


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def logout():

    st.session_state.logged_in = False
    st.session_state.role = ""
    st.session_state.username = ""
    st.session_state.admission_no = ""
    st.session_state.principal_logged_in = False

    st.rerun()


def get_grade(percentage):

    if percentage >= 90:
        return "A+"

    elif percentage >= 80:
        return "A"

    elif percentage >= 70:
        return "B+"

    elif percentage >= 60:
        return "B"

    elif percentage >= 50:
        return "C+"

    elif percentage >= 40:
        return "C"

    else:
        return "F"


def create_receipt_pdf(receipt, school=None):

    buffer = BytesIO()

    pdf = canvas.Canvas(
        buffer,
        pagesize=A4
    )

    width, height = A4

    school_name = (
        school.get(
            "school_name",
            "SCHOOL MANAGEMENT SYSTEM"
        )
        if school
        else "SCHOOL MANAGEMENT SYSTEM"
    )

    receipt_no = receipt.get(
        "receipt_no",
        "N/A"
    )

    student_name = receipt.get(
        "student_name",
        ""
    )

    admission_no = receipt.get(
        "admission_no",
        ""
    )

    class_name = receipt.get(
        "class_name",
        ""
    )

    fee_type = receipt.get(
        "fee_type",
        ""
    )

    total_fee = receipt.get(
        "total_fee",
        0
    )

    paid_amount = receipt.get(
        "paid_amount",
        0
    )

    due_amount = receipt.get(
        "due_amount",
        0
    )

    payment_status = receipt.get(
        "payment_status"
    ) or (
        "Paid"
        if float(due_amount or 0) <= 0
        else "Due"
    )

    payment_method = receipt.get(
        "payment_method",
        ""
    )

    payment_date = receipt.get(
        "payment_date",
        str(date.today())
    )

    remarks = receipt.get(
        "remarks",
        ""
    )

    generated_at = receipt.get(
        "generated_at",
        datetime.now().strftime(
            "%d-%m-%Y %H:%M:%S"
        )
    )

    accountant_name = receipt.get(
        "accountant_name",
        st.session_state.get(
            "username",
            "Accountant"
        )
    )

    pdf.setFillColorRGB(0.08, 0.16, 0.36)
    pdf.rect(35, height - 105, width - 70, 80, fill=1, stroke=0)
    pdf.setFillColorRGB(1, 1, 1)

    pdf.setFont("Helvetica-Bold", 20)
    pdf.drawCentredString(
        width / 2,
        height - 70,
        school_name.upper()
    )

    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawCentredString(
        width / 2,
        height - 95,
        "FEE PAYMENT RECEIPT"
    )

    pdf.setFillColorRGB(0, 0, 0)
    pdf.setFont("Helvetica", 10)

    pdf.drawString(70, height - 130, f"Receipt No: {receipt_no}")
    pdf.drawRightString(width - 70, height - 130, f"Date: {payment_date}")
    pdf.drawRightString(width - 70, height - 148, f"Time: {generated_at}")

    pdf.setLineWidth(0.8)
    pdf.line(70, height - 165, width - 70, height - 165)

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(70, height - 190, "Student Information")
    pdf.drawString(330, height - 190, "Fee Summary")

    pdf.setFont("Helvetica", 10)
    y = height - 220

    student_lines = [
        f"Student Name: {student_name}",
        f"Admission No: {admission_no}",
        f"Class: {class_name}",
        f"Fee Type: {fee_type}",
        f"Payment Method: {payment_method}",
        f"Payment Status: {payment_status}"
    ]

    fee_lines = [
        f"Total Fee: Rs. {total_fee:,.2f}",
        f"Paid Amount: Rs. {paid_amount:,.2f}",
        f"Due Amount: Rs. {due_amount:,.2f}",
        f"Payment Date: {payment_date}",
        f"Remarks: {remarks or 'N/A'}"
    ]

    for line in student_lines:
        pdf.drawString(70, y, line)
        y -= 18

    y = height - 220
    for line in fee_lines:
        pdf.drawString(330, y, line)
        y -= 18

    pdf.line(70, height - 330, width - 70, height - 330)

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(70, height - 360, "Payment Details")

    pdf.setFont("Helvetica", 10)
    pdf.drawString(70, height - 385, f"Receipt generated on: {generated_at}")
    pdf.drawString(70, height - 405, f"Prepared by: {accountant_name}")

    pdf.drawString(70, height - 455, "________________________________")
    pdf.drawString(70, height - 475, "Accountant Signature")

    pdf.drawRightString(width - 140, height - 455, "________________________________")
    pdf.drawRightString(width - 140, height - 475, "Student Sign")

    pdf.save()

    buffer.seek(0)

    return buffer.getvalue()


def humanize_key(key):

    if not key:
        return ""

    label = str(key).replace("_", " ").strip()
    return label.title()


def format_display_value(value):

    if value is None:
        return ""

    if isinstance(value, (int, float)):
        if value == int(value):
            return str(int(value))
        return f"{value:,.2f}"

    return str(value)


def get_teacher_payroll_fields(teacher):

    known_order = [
        "teacher_id",
        "name",
        "department",
        "designation",
        "subject",
        "qualification",
        "phone",
        "email",
        "address",
        "joining_date",
        "salary",
        "allowances",
        "deductions",
        "net_salary"
    ]

    visible_fields = []
    seen = set()

    account_key = None
    for key in teacher.keys():
        normalized_key = str(key).strip().lower().replace(" ", "_")
        if normalized_key in {
            "account_number",
            "account_no",
            "bank_account_number",
            "teacher_account_number",
            "account"
        }:
            account_key = key
            break

    for key in known_order:
        if key in teacher:
            visible_fields.append((humanize_key(key), teacher.get(key)))
            seen.add(key)

    if account_key:
        visible_fields.append(("Account Number", teacher.get(account_key)))
        seen.add(account_key)

    for key, value in teacher.items():
        if key in seen or key in {"id", "created_at", "updated_at"}:
            continue
        visible_fields.append((humanize_key(key), value))

    return visible_fields


def create_payroll_report_html(teachers, school_name="Shree Janta Secondary School"):

    if not teachers:
        return "<div style='padding:24px;'>No teacher data available.</div>"

    teacher_cards = []

    for teacher in teachers:
        salary = float(teacher.get("salary", teacher.get("monthly_salary", 0)) or 0)
        allowances = float(teacher.get("allowances", teacher.get("allowance", 0)) or 0)
        deductions = float(teacher.get("deductions", teacher.get("deduction", 0)) or 0)
        net_salary = float(teacher.get("net_salary", salary + allowances - deductions) or 0)

        rows = []
        for label, value in get_teacher_payroll_fields(teacher):
            if label.lower() in {"salary", "allowances", "deductions", "net salary"}:
                if label.lower() == "salary":
                    displayed_value = f"Rs. {salary:,.2f}"
                elif label.lower() == "allowances":
                    displayed_value = f"Rs. {allowances:,.2f}"
                elif label.lower() == "deductions":
                    displayed_value = f"Rs. {deductions:,.2f}"
                else:
                    displayed_value = f"Rs. {net_salary:,.2f}"
            else:
                displayed_value = format_display_value(value)

            rows.append(
                f"<tr><td style='padding:8px 10px;border-bottom:1px solid #e5e7eb;font-weight:bold;color:#374151;'>{label}</td><td style='padding:8px 10px;border-bottom:1px solid #e5e7eb;'>{displayed_value}</td></tr>"
            )

        teacher_cards.append(
            f"""
            <div style="margin-top:24px;border:1px solid #e5e7eb;border-radius:12px;padding:16px;background:#fff;">
                <h3 style="margin:0 0 12px 0;color:#0f172a;">{format_display_value(teacher.get('teacher_id', 'N/A'))} - {format_display_value(teacher.get('name', 'N/A'))}</h3>
                <table style="width:100%;border-collapse:collapse;font-size:13px;">
                    {''.join(rows)}
                </table>
            </div>
            """
        )

    report_html = f"""
    <style>
    body {{ background: #f8fafc; margin: 0; padding: 20px; }}
    .payroll-card {{ font-family: Arial, sans-serif; max-width: 900px; margin: 0 auto; background: #ffffff; color: #111827; border: 2px solid #0f172a; border-radius: 14px; padding: 24px; box-shadow: 0 12px 30px rgba(0,0,0,0.12); }}
    .payroll-header {{ background: linear-gradient(90deg, #0f172a 0%, #1d4ed8 100%); color:white; padding:18px 20px; border-radius:10px; text-align:center; }}
    .payroll-title {{ font-size: 24px; font-weight: bold; margin: 0; }}
    .payroll-subtitle {{ font-size: 13px; margin-top: 4px; opacity: 0.92; }}
    .payroll-summary {{ display:flex; justify-content:space-between; margin: 16px 0 8px; font-size: 13px; color:#374151; }}
    .print-btn {{ display:inline-block; margin-top: 14px; padding:10px 16px; background:#2563eb; color:white; border:none; border-radius:8px; cursor:pointer; font-size:14px; }}
    @media print {{ body {{ background:white !important; }} .no-print {{ display:none !important; }} .payroll-card {{ box-shadow:none; border:1px solid #111827; }} }}
    </style>
    <div class="payroll-card">
        <div class="payroll-header">
            <div class="payroll-title">{school_name}</div>
            <div class="payroll-subtitle">Official Teacher Payroll Report</div>
        </div>
        <div class="payroll-summary">
            <div><b>Total Teachers:</b> {len(teachers)}</div>
            <div><b>Generated On:</b> {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}</div>
        </div>
        {''.join(teacher_cards)}
        <div class="no-print" style="margin-top:24px;">
            <button class="print-btn" onclick="window.print()">🖨 Print Payroll Report</button>
        </div>
    </div>
    <script>
    window.onload = function() {{ setTimeout(function() {{ window.print(); }}, 400); }};
    </script>
    """

    return report_html


def save_salary_payment_fallback(payload):

    fallback_path = os.path.join(BASE_DIR, "salary_payments.json")

    if os.path.exists(fallback_path):
        with open(fallback_path, "r", encoding="utf-8") as handle:
            try:
                existing = json.load(handle)
            except json.JSONDecodeError:
                existing = []
    else:
        existing = []

    if not isinstance(existing, list):
        existing = []

    existing.append(payload)

    with open(fallback_path, "w", encoding="utf-8") as handle:
        json.dump(existing, handle, indent=2)

    return fallback_path


def get_teacher_by_id(teacher_id):

    if not teacher_id:
        return None

    try:
        result = (
            supabase
            .table("teachers")
            .select("*")
            .eq("teacher_id", teacher_id.strip())
            .limit(1)
            .execute()
        )

        if not result.data:
            return None

        return result.data[0]

    except Exception:
        return None


def get_teacher_account_number(teacher):

    if not teacher:
        return "N/A"

    for key in [
        "account_number",
        "account_no",
        "bank_account_number",
        "teacher_account_number",
        "account"
    ]:
        if key in teacher and teacher.get(key):
            return teacher.get(key)

    for key, value in teacher.items():
        normalized = str(key).strip().lower().replace(" ", "_")
        if normalized in {
            "account_number",
            "account_no",
            "bank_account_number",
            "teacher_account_number",
            "account"
        } and value:
            return value

    return "N/A"


def get_all_teachers():

    try:
        result = (
            supabase
            .table("teachers")
            .select("*")
            .order("id", desc=True)
            .execute()
        )
        return result.data or []
    except Exception:
        return []


def get_teacher_salary_summary(teacher):

    if not teacher:
        return {
            "teacher_id": "",
            "teacher_name": "",
            "department": "",
            "designation": "",
            "account_number": "N/A",
            "salary": 0.0,
            "allowances": 0.0,
            "deductions": 0.0,
            "bonus": 0.0,
            "net_salary": 0.0,
            "final_payable_amount": 0.0,
        }

    base_salary = float(teacher.get("salary", 0) or 0)
    allowances = float(teacher.get("allowances", teacher.get("allowance", 0)) or 0)
    deductions = float(teacher.get("deductions", teacher.get("deduction", 0)) or 0)
    bonus = float(teacher.get("bonus", 0) or 0)
    net_salary = float(teacher.get("net_salary", base_salary + allowances - deductions) or 0)
    final_payable = float(net_salary + bonus)

    return {
        "teacher_id": teacher.get("teacher_id", ""),
        "teacher_name": teacher.get("name", ""),
        "department": teacher.get("department") or teacher.get("subject") or "",
        "designation": teacher.get("designation") or "Teacher",
        "account_number": get_teacher_account_number(teacher),
        "salary": base_salary,
        "allowances": allowances,
        "deductions": deductions,
        "bonus": bonus,
        "net_salary": net_salary,
        "final_payable_amount": final_payable,
    }


def create_all_salary_receipts_html(teachers):

    if not teachers:
        return "<div style='padding:24px;'>No teacher data available.</div>"

    rows = []
    for idx, teacher in enumerate(teachers, start=1):
        summary = get_teacher_salary_summary(teacher)
        rows.append(
            f"""
            <tr>
                <td>{idx}</td>
                <td>{summary['teacher_id']}</td>
                <td>{summary['teacher_name']}</td>
                <td>{summary['department']}</td>
                <td>{summary['designation']}</td>
                <td>{summary['account_number']}</td>
                <td>Rs. {summary['salary']:,.2f}</td>
                <td>Rs. {summary['allowances']:,.2f}</td>
                <td>Rs. {summary['deductions']:,.2f}</td>
                <td>Rs. {summary['bonus']:,.2f}</td>
                <td>Rs. {summary['net_salary']:,.2f}</td>
                <td>Rs. {summary['final_payable_amount']:,.2f}</td>
            </tr>
            """
        )

    school_name = "Shree Janta Secondary School"
    generated_at = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

    return f"""
    <style>
    @page {{ size: A4 landscape; margin: 10mm; }}
    html, body {{ width: 100%; height: auto; margin: 0; padding: 0; overflow: visible !important; }}
    body {{ background: #f8fafc; }}
    .report-container {{ font-family: Arial, sans-serif; width: 100%; padding: 14px; box-sizing: border-box; }}
    .report-card {{ background: #ffffff; color: #111827; border: 1px solid #0f172a; border-radius: 12px; padding: 16px; box-shadow: 0 12px 30px rgba(0,0,0,0.08); }}
    .report-header {{ background: linear-gradient(90deg, #0f172a 0%, #1d4ed8 100%); color: white; padding: 16px 18px; border-radius: 10px; text-align: center; }}
    .report-title {{ font-size: 22px; font-weight: bold; margin: 0; }}
    .report-subtitle {{ font-size: 13px; margin-top: 4px; opacity: 0.92; }}
    .report-meta {{ display: flex; justify-content: space-between; flex-wrap: wrap; margin: 16px 0 10px; gap: 10px; font-size: 12px; color: #374151; }}
    .report-meta div {{ min-width: 180px; }}
    .table-container {{ overflow-x: auto; width: 100%; }}
    .report-table {{ width: 100%; border-collapse: collapse; font-size: 11px; table-layout: fixed; margin-top: 10px; }}
    .report-table th, .report-table td {{ padding: 8px 10px; border: 1px solid #e5e7eb; text-align: left; vertical-align: middle; }}
    .report-table th {{ background: #0f172a; color: white; font-size: 11px; text-transform: uppercase; letter-spacing: 0.02em; }}
    .report-table tbody tr:nth-child(even) {{ background: #f8fafc; }}
    .report-table td {{ white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
    .report-table th:nth-child(1) {{ width: 3%; }}
    .report-table th:nth-child(2) {{ width: 8%; }}
    .report-table th:nth-child(3) {{ width: 15%; }}
    .report-table th:nth-child(4) {{ width: 12%; }}
    .report-table th:nth-child(5) {{ width: 12%; }}
    .report-table th:nth-child(6) {{ width: 14%; }}
    .report-table th:nth-child(7), .report-table th:nth-child(8), .report-table th:nth-child(9), .report-table th:nth-child(10), .report-table th:nth-child(11), .report-table th:nth-child(12) {{ width: 8%; }}
    .print-btn {{ display:inline-block; margin-top: 18px; padding: 10px 16px; background: #2563eb; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 13px; }}
    @media print {{
        body {{ background: white !important; }}
        .no-print {{ display:none !important; }}
        .report-card {{ box-shadow:none; border:1px solid #111827; }}
        .report-meta {{ color: #111827; }}
        .table-container {{ overflow: visible !important; }}
        .report-table td, .report-table th {{ font-size: 10px; padding: 6px 8px; }}
    }}
    </style>
    <div class="report-container">
        <div class="report-card">
            <div class="report-header">
                <div class="report-title">{school_name}</div>
                <div class="report-subtitle">All Teacher Salary Report</div>
            </div>
            <div class="report-meta">
                <div><strong>Total Teachers:</strong> {len(teachers)}</div>
                <div><strong>Generated On:</strong> {generated_at}</div>
                <div><strong>Prepared By:</strong> {st.session_state.get('username', 'Admin')}</div>
            </div>
            <div class="table-container">
                <table class="report-table">
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Teacher ID</th>
                            <th>Name</th>
                            <th>Department</th>
                            <th>Designation</th>
                            <th>Account Number</th>
                            <th>Salary</th>
                            <th>Allowances</th>
                            <th>Deductions</th>
                            <th>Bonus</th>
                            <th>Net Salary</th>
                            <th>Final Payable</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(rows)}
                    </tbody>
                </table>
            </div>
            <div class="no-print">
                <button class="print-btn" onclick="window.print()">🖨 Print Salary Report</button>
            </div>
        </div>
    </div>
    <script>window.onload = function() {{ setTimeout(function() {{ window.print(); }}, 350); }};</script>
    """


def create_salary_slip_html(payment_record, teacher):

    teacher_name = teacher.get("name", "") if teacher else ""
    teacher_id = teacher.get("teacher_id", "") if teacher else ""
    department = teacher.get("department") or teacher.get("subject") or ""
    designation = teacher.get("designation") or "Teacher"
    account_number = get_teacher_account_number(teacher)

    salary_month = payment_record.get("salary_month", "")
    payment_date = payment_record.get("payment_date", str(date.today()))
    payment_method = payment_record.get("payment_method", "")
    reference_no = payment_record.get("transaction_id", payment_record.get("reference_no", ""))
    allowances = float(payment_record.get("allowances", 0) or 0)
    deductions = float(payment_record.get("deductions", 0) or 0)
    bonus = float(payment_record.get("bonus", 0) or 0)
    net_salary = float(payment_record.get("net_salary", 0) or 0)
    final_payable = float(payment_record.get("final_payable_amount", 0) or 0)

    return """
    <style>
    @page {{ size: A4; margin: 8mm; }}
    body {{ background: #f8fafc; margin: 0; padding: 12px; }}
    .slip-card {{ font-family: Arial, sans-serif; max-width: 720px; margin: 0 auto; background: #ffffff; color: #111827; border: 2px solid #0f172a; border-radius: 12px; padding: 18px 22px; box-shadow: 0 10px 30px rgba(0,0,0,0.15); page-break-inside: avoid; break-inside: avoid; }}
    .slip-header {{ background: linear-gradient(90deg, #0f172a 0%, #1d4ed8 100%); color: white; padding: 14px 16px; border-radius: 10px; text-align: center; }}
    .slip-title {{ font-size: 20px; font-weight: bold; margin: 0; }}
    .slip-subtitle {{ font-size: 12px; margin-top: 4px; opacity: 0.92; }}
    .slip-meta {{ display: flex; justify-content: space-between; margin: 12px 0 8px; font-size: 13px; }}
    .slip-table {{ width: 100%; border-collapse: collapse; margin-top: 8px; }}
    .slip-table td {{ padding: 7px 8px; border-bottom: 1px solid #e5e7eb; }}
    .slip-label {{ font-weight: bold; color: #374151; }}
    .slip-footer {{ margin-top: 16px; display: flex; justify-content: space-between; font-size: 13px; }}
    .print-btn {{ display:inline-block; margin-top: 12px; padding:10px 16px; background:#2563eb; color:white; border:none; border-radius:8px; cursor:pointer; font-size:14px; }}
    @media print {{ body {{ background:white !important; padding: 0; }} .no-print {{ display:none !important; }} .slip-card {{ box-shadow:none; border:1px solid #111827; margin: 0; }} }}
    </style>
    <div class="slip-card">
        <div class="slip-header">
            <div class="slip-title">Shree Janta Secondary School</div>
            <div class="slip-subtitle">Teacher Salary Slip</div>
        </div>
        <div class="slip-meta">
            <div><b>Teacher ID:</b> {teacher_id}</div>
            <div><b>Payment Date:</b> {payment_date}</div>
        </div>
        <p style="margin: 4px 0;"><b>Name:</b> {teacher_name}</p>
        <p style="margin: 4px 0;"><b>Department:</b> {department}</p>
        <p style="margin: 4px 0;"><b>Designation:</b> {designation}</p>
        <p style="margin: 4px 0;"><b>Bank Account Number:</b> {account_number}</p>
        <p style="margin: 4px 0;"><b>Salary Month:</b> {salary_month}</p>
        <p style="margin: 4px 0;"><b>Payment Method:</b> {payment_method}</p>
        <p style="margin: 4px 0;"><b>Reference No:</b> {reference_no}</p>
        <table class="slip-table">
            <tr><td class="slip-label">Net Salary</td><td>Rs. {net_salary:,.2f}</td></tr>
            <tr><td class="slip-label">Allowances</td><td>Rs. {allowances:,.2f}</td></tr>
            <tr><td class="slip-label">Deductions</td><td>Rs. {deductions:,.2f}</td></tr>
            <tr><td class="slip-label">Bonus</td><td>Rs. {bonus:,.2f}</td></tr>
            <tr><td class="slip-label">Final Payable Amount</td><td>Rs. {final_payable:,.2f}</td></tr>
        </table>
        <div class="slip-footer">
            <div>Prepared by<br><strong>{prepared_by}</strong></div>
            <div>Payment Status<br><strong>Paid</strong></div>
        </div>
        <div class="no-print" style="margin-top: 12px;">
            <button class="print-btn" onclick="window.print()">🖨 Print Salary Slip</button>
        </div>
    </div>
    <script>window.onload = function() {{ setTimeout(function() {{ window.print(); }}, 350); }};</script>
    """.format(
        teacher_id=teacher_id,
        payment_date=payment_date,
        teacher_name=teacher_name,
        department=department,
        designation=designation,
        account_number=account_number,
        salary_month=salary_month,
        payment_method=payment_method,
        reference_no=reference_no or "N/A",
        net_salary=net_salary,
        allowances=allowances,
        deductions=deductions,
        bonus=bonus,
        final_payable=final_payable,
        prepared_by=st.session_state.get("username", "Admin"),
    )


def render_salary_management_section(title, caption, teacher_id_key, submit_label, show_history):

    st.title(title)
    st.caption(caption)

    teacher_id_input = st.text_input(
        "Teacher ID",
        key=teacher_id_key
    )

    teacher = None

    all_teachers = get_all_teachers()

    if all_teachers:
        st.subheader("📋 Teacher Salary Overview")
        overview_rows = []
        for record in all_teachers:
            summary = get_teacher_salary_summary(record)
            overview_rows.append({
                "Teacher ID": summary["teacher_id"],
                "Name": summary["teacher_name"],
                "Department": summary["department"],
                "Designation": summary["designation"],
                "Account Number": summary["account_number"],
                "Net Salary": f"Rs. {summary['net_salary']:,.2f}",
                "Allowances": f"Rs. {summary['allowances']:,.2f}",
                "Deductions": f"Rs. {summary['deductions']:,.2f}",
                "Bonus": f"Rs. {summary['bonus']:,.2f}",
                "Final Payable Amount": f"Rs. {summary['final_payable_amount']:,.2f}",
            })
        st.dataframe(pd.DataFrame(overview_rows), use_container_width=True, hide_index=True)

    if teacher_id_input:
        teacher = get_teacher_by_id(teacher_id_input)

        if teacher:
            st.success("Teacher found.")

            c1, c2, c3 = st.columns(3)

            with c1:
                st.write(f"**Name:** {teacher.get('name', '')}")

            with c2:
                st.write(f"**Department:** {teacher.get('department') or teacher.get('subject') or ''}")

            with c3:
                st.write(f"**Designation:** {teacher.get('designation') or 'Teacher'}")

            st.write(f"**Bank Account Number:** {get_teacher_account_number(teacher)}")

            base_salary = float(teacher.get("salary", 0) or 0)
            allowances_default = float(teacher.get("allowances", teacher.get("allowance", 0)) or 0)
            deductions_default = float(teacher.get("deductions", teacher.get("deduction", 0)) or 0)
            bonus_default = float(teacher.get("bonus", 0) or 0)
            net_salary = float(teacher.get("net_salary", base_salary + allowances_default - deductions_default) or 0)

            st.metric("Net Salary", f"Rs. {net_salary:,.2f}")

        else:
            st.warning("No teacher found with this Teacher ID.")

    if st.button("🖨 Print All Teacher Salary Receipts", key=f"{teacher_id_key}_print_all", use_container_width=True):
        if all_teachers:
            st.components.v1.html(
                create_all_salary_receipts_html(all_teachers),
                height=2200,
                scrolling=True
            )
        else:
            st.info("No teacher records found to print.")

    with st.form(f"{teacher_id_key}_form"):

        c1, c2 = st.columns(2)

        with c1:
            allowances = st.number_input(
                "Allowances",
                min_value=0.0,
                value=0.0,
                step=100.0
            )

            deductions = st.number_input(
                "Deductions",
                min_value=0.0,
                value=0.0,
                step=100.0
            )

            bonus = st.number_input(
                "Bonus",
                min_value=0.0,
                value=0.0,
                step=100.0
            )

        with c2:
            payment_method = st.selectbox(
                "Payment Method",
                [
                    "Cash",
                    "Bank Transfer",
                    "Cheque",
                    "Online Payment",
                    "Other"
                ]
            )

            payment_date = st.date_input(
                "Payment Date",
                value=date.today()
            )

            salary_month = st.text_input(
                "Salary Month",
                value=date.today().strftime("%B %Y")
            )

            reference_no = st.text_input(
                "Transaction ID / Reference Number"
            )

        if teacher:
            final_payable = net_salary + bonus
            st.metric("Final Payable Amount", f"Rs. {final_payable:,.2f}")
        else:
            st.info("Enter a valid Teacher ID to calculate the final payable amount.")

        submitted = st.form_submit_button(submit_label, use_container_width=True)

        if submitted:

            if not teacher_id_input:
                st.error("Teacher ID is required.")

            elif not teacher:
                st.error("Teacher not found. Please enter a valid Teacher ID.")

            else:

                payment_payload = {
                    "teacher_id": teacher.get("teacher_id"),
                    "teacher_name": teacher.get("name"),
                    "department": teacher.get("department") or teacher.get("subject") or "",
                    "designation": teacher.get("designation") or "Teacher",
                    "account_number": get_teacher_account_number(teacher),
                    "salary_month": salary_month.strip(),
                    "payment_date": str(payment_date),
                    "payment_method": payment_method,
                    "allowances": float(allowances),
                    "deductions": float(deductions),
                    "bonus": float(bonus),
                    "net_salary": float(net_salary),
                    "final_payable_amount": float(net_salary + bonus),
                    "payment_status": "Paid",
                    "transaction_id": (reference_no or f"SLR-{uuid.uuid4().hex[:8].upper()}"),
                    "generated_by": st.session_state.get("username", "Admin")
                }

                try:
                    response = (
                        supabase
                        .table("salary_payments")
                        .insert(payment_payload)
                        .execute()
                    )

                    if response.data:
                        st.success("Salary payment saved successfully.")
                    else:
                        st.warning("Salary payment submitted, but the response did not return a record.")

                except Exception as save_error:

                    fallback_path = save_salary_payment_fallback(payment_payload)
                    st.warning(
                        f"Salary payment could not be written to the Supabase table yet. It was saved locally to {fallback_path}."
                    )
                    st.caption(f"Supabase error: {save_error}")

                slip_html = create_salary_slip_html(payment_payload, teacher)
                st.components.v1.html(
                    slip_html,
                    height=980,
                    scrolling=True
                )

    if show_history:
        st.divider()
        st.subheader("🧾 Salary Payment History")

        try:
            history_result = (
                supabase
                .table("salary_payments")
                .select("*")
                .order("id", desc=True)
                .execute()
            )

            history = history_result.data or []

            if history:
                history_df = pd.DataFrame(history)
                history_df = history_df[[
                    "teacher_id",
                    "teacher_name",
                    "salary_month",
                    "payment_date",
                    "payment_method",
                    "payment_status",
                    "transaction_id",
                    "allowances",
                    "deductions",
                    "bonus",
                    "final_payable_amount"
                ]].copy()
                history_df = history_df.rename(columns={
                    "teacher_id": "Teacher ID",
                    "teacher_name": "Teacher Name",
                    "salary_month": "Salary Month",
                    "payment_date": "Payment Date",
                    "payment_method": "Payment Method",
                    "payment_status": "Payment Status",
                    "transaction_id": "Transaction ID",
                    "allowances": "Allowances",
                    "deductions": "Deductions",
                    "bonus": "Bonus",
                    "final_payable_amount": "Final Payable Amount"
                })
                st.dataframe(history_df, use_container_width=True, hide_index=True)
            else:
                st.info("No salary payments have been recorded yet.")

        except Exception as history_error:
            st.error(f"Salary payment history could not be loaded: {history_error}")


def save_fee_receipt(payload):

    current_payload = dict(payload)

    while True:
        try:
            return (
                supabase
                .table("fee_receipts")
                .insert(current_payload)
                .execute()
            )
        except Exception as exc:
            message = str(exc)
            match = re.search(r"Could not find the '([^']+)' column", message)

            if not match:
                raise

            missing_column = match.group(1)

            if missing_column not in current_payload:
                raise

            current_payload.pop(missing_column, None)

            if not current_payload:
                raise


# =========================================================
# LOGIN PAGE
# =========================================================

def login_page():

    if LOGIN_IMAGE_PATH:
        st.image(LOGIN_IMAGE_PATH, use_container_width=True)
    else:
        st.warning("Login image not found. Place s.png inside an assets folder beside the app.")

    st.markdown(
        """
        <div class="hero-card">
            <div class="hero-badge">Premium Access Portal</div>
            <h1>School Management Experience</h1>
            <p>Secure, elegant, and fast access for administrators, students, and principals in one vibrant control center.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="school-card login-panel">
            <h2 style="margin:0 0 8px 0;">Choose your secure login</h2>
            <p style="margin:0;">A polished portal designed for modern school operations, with highlighted actions and a premium feel.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "🔐 Admin Login",
            "👨‍🎓 Student Login",
            "📝 Student Register",
            "👨‍🏫 Principal Login"
        ]
    )


    # =====================================================
    # ADMIN LOGIN
    # =====================================================



    with tab1:

        st.subheader("🔐 Admin Login")

        username = st.text_input(
        "Username",
        key="admin_username"
    )

        password = st.text_input(
        "Password",
        type="password",
        key="admin_password"
    )

        if st.button(
        "🔐 Login as Admin",
        key="admin_login_button",
        use_container_width=True
    ):

            username = username.strip()
            password = password.strip()

            if not username or not password:

                st.error(
                "Username and password are required."
            )

            else:

                try:

                # Find the admin by username
                    result = (
                    supabase
                    .table("admins")
                    .select("*")
                    .eq(
                        "username",
                        username
                    )
                    .execute()
                )

                # Username check
                    if not result.data:

                        st.error(
                        "❌ Invalid Username or Password."
                    )

                    else:

                        admin = result.data[0]

                    # Database password
                        db_password = str(
                        admin.get(
                            "password",
                            ""
                        )
                    ).strip()

                    # Password check
                        if db_password == password:

                            st.session_state.logged_in = True

                            st.session_state.role = "admin"

                            st.session_state.username = (
                            admin["username"]
                        )

                            st.success(
                            "✅ Admin Login Successful!"
                        )

                            st.rerun()

                        else:

                            st.error(
                            "❌ Invalid Username or Password."
                        )

                except Exception as e:

                    st.error(f"❌ Login Error: {e}")
   
    # =====================================================
    # STUDENT LOGIN
    # =====================================================

    with tab2:

        st.subheader(
            "👨‍🎓 Student Login"
        )

        admission_no = st.text_input(
            "Admission Number",
            key="student_login_admission"
        )

        password = st.text_input(
            "Password",
            type="password",
            key="student_login_password"
        )

        if st.button(
            "👨‍🎓 Login as Student",
            use_container_width=True
        ):

            if not admission_no or not password:

                st.error(
                    "Admission number and password are required."
                )

            else:

                try:

                    result = (
                        supabase
                        .table("students")
                        .select("*")
                        .eq(
                            "admission_no",
                            admission_no.strip()
                        )
                        .eq(
                            "password",
                            password.strip()
                        )
                        .execute()
                    )

                    if result.data:

                        student = result.data[0]

                        st.session_state.logged_in = True

                        st.session_state.role = "student"

                        st.session_state.username = (
                            student["name"]
                        )

                        st.session_state.admission_no = (
                            student["admission_no"]
                        )

                        st.success(
                            "Student Login Successful!"
                        )

                        st.rerun()

                    else:

                        st.error(
                            "Invalid Admission Number or Password."
                        )

                except Exception as e:

                    st.error(
                        f"Login Error: {e}"
                    )


    # =====================================================
    # STUDENT REGISTER
    # =====================================================

    with tab3:

        st.subheader(
            "📝 Student Registration"
        )

        st.info(
            "After an admin adds the student record, register using the admission number."
        )

        admission_no = st.text_input(
            "Admission Number",
            key="register_admission"
        )

        password = st.text_input(
            "New Password",
            type="password",
            key="register_password"
        )

        confirm_password = st.text_input(
            "Confirm Password",
            type="password",
            key="register_confirm_password"
        )

        if st.button(
            "📝 Register",
            use_container_width=True
        ):

            if not admission_no:

                st.error(
                    "Admission Number required."
                )

            elif not password:

                st.error(
                    "Password required."
                )

            elif password != confirm_password:

                st.error(
                    "Passwords do not match."
                )

            else:

                try:

                    result = (
                        supabase
                        .table("students")
                        .select("*")
                        .eq(
                            "admission_no",
                            admission_no.strip()
                        )
                        .execute()
                    )

                    if not result.data:

                        st.error(
                            "Admission number not found. "
                            "Please ask the admin to add the student first."
                        )

                    else:

                        (
                            supabase
                            .table("students")
                            .update({
                                "password": password
                            })
                            .eq(
                                "admission_no",
                                admission_no.strip()
                            )
                            .execute()
                        )

                        st.success(
                            "Registration successful! "
                            "You can now log in as a student."
                        )

                except Exception as e:

                    st.error(
                        f"Registration Error: {e}"
                    )

    with tab4:

        st.subheader("👨‍🏫 Principal Login")

        st.info(
            "Principal portal is separate from Admin and Student access."
        )

        principal_username = st.text_input(
            "Principal Username",
            key="principal_login_username"
        )

        principal_password = st.text_input(
            "Password",
            type="password",
            key="principal_login_password"
        )

        if st.button(
            "👨‍🏫 Login as Principal",
            use_container_width=True
        ):

            if not principal_username or not principal_password:

                st.error("Principal Username and Password are required.")

            else:

                try:

                    principal_user = None

                    for table_name in ["principals", "admins"]:

                        try:

                            result = (
                                supabase
                                .table(table_name)
                                .select("*")
                                .eq(
                                    "username",
                                    principal_username.strip()
                                )
                                .eq(
                                    "password",
                                    principal_password.strip()
                                )
                                .execute()
                            )

                            if result.data:

                                principal_user = result.data[0]
                                break

                        except Exception:

                            continue

                    if principal_user:

                        st.session_state.logged_in = True
                        st.session_state.role = "principal"
                        st.session_state.username = (
                            principal_user.get(
                                "name",
                                principal_user.get(
                                    "username",
                                    principal_username.strip()
                                )
                            )
                        )
                        st.session_state.admission_no = ""
                        st.session_state.principal_logged_in = True
                        st.success("✅ Principal Login Successful!")
                        st.rerun()

                    else:

                        st.error("❌ Invalid Principal Username or Password.")

                except Exception as e:

                    st.error(f"❌ Principal Login Error: {e}")


# =========================================================
# ADMIN DASHBOARD
# =========================================================

def admin_dashboard():

    st.sidebar.title(
        "🏫 ADMIN PANEL"
    )

    st.sidebar.write(
        f"Welcome, {st.session_state.username}"
    )

    menu = st.sidebar.radio(
        "Navigation",
        [
            "🏠 Dashboard",
            "👨‍🎓 Students",
            "👨‍🏫 Teachers",
            "👥 Faculty",
            "💰 Fees",
            "💳 Payment Approval",
            "🧾 Fee Receipts",
            "🧾 Payroll",
            "💼 Salary Management",
            "📅 Student Attendance",
            "📅 Teacher Attendance",
            "📝 Student Marks",
            "📊 Financial",
            "🏫 About School"
        ]
    )

    if st.sidebar.button(
        "🚪 Logout",
        use_container_width=True
    ):

        logout()


    # =====================================================
    # DASHBOARD
    # =====================================================

    if menu == "🏠 Dashboard":

        st.markdown(
            """
            <div class="hero-card">
                <div class="hero-badge">Live Operations Center</div>
                <h2>Administrative Overview</h2>
                <p>Monitor students, faculty, fees, approvals, and school activity from a colorful and premium dashboard.</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.title(
            "🏠 Admin Dashboard"
        )

        students = (
            supabase
            .table("students")
            .select("id")
            .execute()
        )

        teachers = (
            supabase
            .table("teachers")
            .select("id")
            .execute()
        )

        faculty = (
            supabase
            .table("faculty")
            .select("id")
            .execute()
        )

        payments = (
            supabase
            .table("payment_requests")
            .select("id")
            .eq(
                "status",
                "Pending"
            )
            .execute()
        )

        fees = (
            supabase
            .table("fees")
            .select(
                "total_fee,paid_amount,due_amount"
            )
            .execute()
        )

        total_fee = sum(
            float(x["total_fee"] or 0)
            for x in fees.data
        )

        paid = sum(
            float(x["paid_amount"] or 0)
            for x in fees.data
        )

        due = sum(
            float(x["due_amount"] or 0)
            for x in fees.data
        )

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "👨‍🎓 Students",
            len(students.data)
        )

        c2.metric(
            "👨‍🏫 Teachers",
            len(teachers.data)
        )

        c3.metric(
            "👥 Faculty",
            len(faculty.data)
        )

        c4.metric(
            "⏳ Pending Payments",
            len(payments.data)
        )

        st.divider()

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "💰 Total Fee",
            f"Rs. {total_fee:,.2f}"
        )

        c2.metric(
            "✅ Total Paid",
            f"Rs. {paid:,.2f}"
        )

        c3.metric(
            "📌 Total Due",
            f"Rs. {due:,.2f}"
        )


    # =====================================================
    # STUDENT MANAGEMENT
    # =====================================================

    elif menu == "👨‍🎓 Students":

        st.title(
            "👨‍🎓 Student Management"
        )

        tab1, tab2 = st.tabs(
            [
                "➕ Add Student",
                "📋 Student Records"
            ]
        )


        with tab1:

            with st.form(
                "add_student_form"
            ):

                c1, c2 = st.columns(2)

                with c1:

                    admission_no = st.text_input(
                        "Admission Number *"
                    )

                    name = st.text_input(
                        "Student Name *"
                    )

                    father_name = st.text_input(
                        "Father Name"
                    )

                    mother_name = st.text_input(
                        "Mother Name"
                    )

                    dob = st.date_input(
                        "Date of Birth",
                        min_value=datetime(1900, 1, 1)
                    )

                    gender = st.selectbox(
                        "Gender",
                        [
                            "Male",
                            "Female",
                            "Other"
                        ]
                    )

                with c2:

                    class_name = st.text_input(
                        "Class"
                    )

                    section = st.text_input(
                        "Section"
                    )

                    roll_no = st.text_input(
                        "Roll Number"
                    )

                    phone = st.text_input(
                        "Phone"
                    )

                    email = st.text_input(
                        "Email"
                    )

                    address = st.text_area(
                        "Address"
                    )

                submitted = st.form_submit_button(
                    "💾 Save Student",
                    use_container_width=True
                )

                if submitted:

                    if not admission_no or not name:

                        st.error(
                            "Admission number and name are required."
                        )

                    else:

                        try:

                            (
                                supabase
                                .table("students")
                                .insert({

                                    "admission_no":
                                        admission_no.strip(),

                                    "name":
                                        name.strip(),

                                    "father_name":
                                        father_name,

                                    "mother_name":
                                        mother_name,

                                    "dob":
                                        str(dob),

                                    "gender":
                                        gender,

                                    "class_name":
                                        class_name,

                                    "section":
                                        section,

                                    "roll_no":
                                        roll_no,

                                    "phone":
                                        phone,

                                    "email":
                                        email,

                                    "address":
                                        address

                                })
                                .execute()
                            )

                            st.success(
                                "Student Added Successfully!"
                            )

                        except Exception as e:

                            st.error(
                                f"Error: {e}"
                            )


        with tab2:

            result = (
                supabase
                .table("students")
                .select(
                    "admission_no,name,father_name,"
                    "class_name,section,roll_no,"
                    "phone,email,address"
                )
                .order(
                    "id",
                    desc=True
                )
                .execute()
            )

            if result.data:

                st.dataframe(
                    result.data,
                    use_container_width=True
                )

            else:

                st.info(
                    "No Student Records Found."
                )


    # =====================================================
    # TEACHERS
    # =====================================================
    elif menu == "👨‍🏫 Teachers":

        st.title("👨‍🏫 Teacher Management System")

    # =====================================================
    # ADD / UPDATE TEACHER
    # =====================================================

        st.subheader("➕ Add New Teacher")

        with st.form("teacher_form", clear_on_submit=False):

            c1, c2 = st.columns(2)

            with c1:

                teacher_id = st.text_input(
                "Teacher ID *",
                placeholder="T001"
            )

                name = st.text_input(
                "Teacher Name *",
                placeholder="Enter teacher name"
            )

                subject = st.text_input(
                "Subject",
                placeholder="Mathematics"
            )

                qualification = st.text_input(
                "Qualification",
                placeholder="M.Ed / M.Sc / B.Ed"
            )

                joining_date = st.date_input(
                "Joining Date",
                min_value=datetime(1900, 1, 1)
            )

            with c2:

                phone = st.text_input(
                "Phone",
                placeholder="98XXXXXXXX"
            )

                email = st.text_input(
                "Email",
                placeholder="teacher@gmail.com"
            )

                address = st.text_area(
                "Address",
                placeholder="Enter teacher address"
            )

                salary = st.number_input(
                "Monthly Salary",
                min_value=0.0,
                step=1000.0
            )

            submitted = st.form_submit_button(
            "💾 Save Teacher",
            use_container_width=True
        )

            if submitted:

                teacher_id = teacher_id.strip()
                name = name.strip()

                if not teacher_id:

                    st.error(
                    "❌ Teacher ID is required."
                )

                elif not name:

                    st.error(
                    "❌ Teacher name is required."
                )

                else:

                    try:

                    # =====================================
                    # CHECK DUPLICATE TEACHER ID
                    # =====================================

                        check = (
                            supabase
                        .table("teachers")
                        .select("id")
                        .eq(
                            "teacher_id",
                            teacher_id
                        )
                        .execute()
                    )

                        if check.data:

                            st.error(
                            "❌ This teacher ID already exists."
                        )

                        else:

                        # =================================
                        # INSERT TEACHER
                        # =================================

                            teacher_data = {

                                "teacher_id":
                                teacher_id,

                                "name":
                                name,

                                "subject":
                                subject.strip(),

                                "qualification":
                                qualification.strip(),

                                "phone":
                                phone.strip(),

                                "email":
                                email.strip(),

                                "address":
                                address.strip(),

                                "joining_date":
                                str(joining_date),

                                "salary":
                                float(salary)

                        }

                            response = (
                            supabase
                            .table("teachers")
                            .insert(
                                teacher_data
                            )
                            .execute()
                        )

                            if response.data:

                                st.success(
                                "✅ Teacher Added Successfully!"
                            )

                                st.rerun()

                            else:

                                st.error(
                                "❌ Teacher could not be added."
                            )

                    except Exception as e:

                        st.error(
                        f"❌ Teacher Add Error: {e}"
                    )


    # =====================================================
    # SEARCH TEACHER
    # =====================================================

        st.divider()

        st.subheader("🔍 Search Teacher")

        search = st.text_input(
        "Search by Teacher ID, Name or Subject",
            placeholder="Enter search..."
    )


    # =====================================================
    # GET TEACHERS
    # =====================================================

        try:

            result = (
            supabase
            .table("teachers")
            .select("*")
            .order(
                "id",
                desc=True
            )
            .execute()
        )

            teachers = result.data or []


        # =================================================
        # SEARCH FILTER
        # =================================================

            if search:

                search_text = (
                    search
                    .strip()
                    .lower()
            )

                teachers = [

                    teacher

                    for teacher in teachers

                    if (

                        search_text
                        in str(
                        teacher.get(
                            "teacher_id",
                            ""
                        )
                    ).lower()

                        or

                        search_text
                        in str(
                        teacher.get(
                            "name",
                            ""
                        )
                    ).lower()

                        or

                        search_text
                        in str(
                            teacher.get(
                            "subject",
                            ""
                        )
                    ).lower()

                )

            ]


        # =================================================
        # DISPLAY RECORDS
        # =================================================

            st.subheader(
                f"📋 Teacher Records ({len(teachers)})"
        )

            if teachers:

                for teacher in teachers:

                    teacher_db_id = teacher.get(
                    "id"
                )

                    teacher_id_value = teacher.get(
                    "teacher_id",
                    ""
                )

                    teacher_name = teacher.get(
                    "name",
                    ""
                )

                    with st.expander(
                        f"👨‍🏫 {teacher_id_value} - {teacher_name}"
                ):

                        c1, c2 = st.columns(2)

                        with c1:

                            st.write(
                            f"**Teacher ID:** "
                            f"{teacher_id_value}"
                        )

                            st.write(
                            f"**Name:** "
                            f"{teacher_name}"
                        )

                            st.write(
                            f"**Subject:** "
                            f"{teacher.get('subject', '')}"
                        )

                            st.write(
                            f"**Qualification:** "
                            f"{teacher.get('qualification', '')}"
                        )

                            st.write(
                            f"**Joining Date:** "
                            f"{teacher.get('joining_date', '')}"
                        )

                        with c2:

                            st.write(
                            f"**Phone:** "
                            f"{teacher.get('phone', '')}"
                        )

                            st.write(
                            f"**Email:** "
                            f"{teacher.get('email', '')}"
                        )

                            st.write(
                            f"**Address:** "
                            f"{teacher.get('address', '')}"
                        )

                            st.write(
                            f"**Salary:** "
                            f"${float(teacher.get('salary', 0) or 0):,.2f}"
                        )


                    # =====================================
                    # DELETE TEACHER
                    # =====================================

                        if st.button(
                        "🗑️ Delete Teacher",
                        key=f"delete_teacher_{teacher_db_id}",
                        use_container_width=True
                    ):

                            try:

                                (
                                supabase
                                .table("teachers")
                                .delete()
                                .eq(
                                    "id",
                                    teacher_db_id
                                )
                                .execute()
                            )

                                st.success(
                                "✅ Teacher Deleted Successfully!"
                            )

                                st.rerun()

                            except Exception as e:

                                st.error(
                                f"❌ Delete Error: {e}"
                            )

            else:

                st.info(
                "ℹ️ No teacher records were found."
            )


        except Exception as e:

            st.error(
            f"❌ Teacher Records Load Error: {e}"
        )


    # =========================================
    # TEACHER RECORDS
    # =========================================

            st.divider()

            st.subheader("📋 Teachers Records")

            try:

                result = (
                supabase
            .table("teachers")
            .select("*")
            .order(
                "id",
                desc=True
            )
            .execute()
        )

                teachers = result.data

                if teachers:

                    st.dataframe(
                teachers,
                use_container_width=True,
                hide_index=True
            )

                    st.success(
                f"Total Teachers: {len(teachers)}"
            )

                else:

                    st.info(
                "ℹ️ No teacher records are available yet."
            )

            except Exception as e:

                st.error(
            f"❌ Records Load Error: {e}"
        )    
    

    # =====================================================
    # FACULTY
    # =====================================================

    elif menu == "👥 Faculty":

        st.title(
            "👥 Faculty Management"
        )

        with st.form(
            "faculty_form"
        ):

            c1, c2 = st.columns(2)

            with c1:

                faculty_id = st.text_input(
                    "Faculty ID *"
                )

                name = st.text_input(
                    "Faculty Name *"
                )

                department = st.text_input(
                    "Department"
                )

                designation = st.text_input(
                    "Designation"
                )

                qualification = st.text_input(
                    "Qualification"
                )

            with c2:

                phone = st.text_input(
                    "Phone"
                )

                email = st.text_input(
                    "Email"
                )

                address = st.text_area(
                    "Address"
                )

                joining_date = st.date_input(
                    "Joining Date",
                    min_value=datetime(1900, 1, 1)
                )

                salary = st.number_input(
                    "Salary",
                    min_value=0.0
                )

            submitted = st.form_submit_button(
                "💾 Save Faculty",
                use_container_width=True
            )

            if submitted:

                try:

                    (
                        supabase
                        .table("faculty")
                        .insert({

                            "faculty_id":
                                faculty_id,

                            "name":
                                name,

                            "department":
                                department,

                            "designation":
                                designation,

                            "qualification":
                                qualification,

                            "phone":
                                phone,

                            "email":
                                email,

                            "address":
                                address,

                            "joining_date":
                                str(joining_date),

                            "salary":
                                salary

                        })
                        .execute()
                    )

                    st.success(
                        "Faculty Added Successfully!"
                    )

                except Exception as e:

                    st.error(
                        f"Error: {e}"
                    )

        result = (
            supabase
            .table("faculty")
            .select("*")
            .order(
                "id",
                desc=True
            )
            .execute()
        )

        st.dataframe(
            result.data,
            use_container_width=True
        )


    # =====================================================
    # FEES
    # =====================================================

    elif menu == "💰 Fees":

        st.title(
            "💰 Fee Management"
        )

        students = (
            supabase
            .table("students")
            .select(
                "admission_no,name,class_name"
            )
            .execute()
        )

        if not students.data:

            st.warning(
                "Please add a student first."
            )

        else:

            student_map = {

                f"{x['admission_no']} | "
                f"{x['name']} | "
                f"Class {x['class_name']}":
                x

                for x in students.data

            }

            selected = st.selectbox(
                "Select Student",
                list(
                    student_map.keys()
                )
            )

            student = student_map[selected]

            fee_type = st.selectbox(
                "Fee Type",
                [
                    "Admission Fee",
                    "Monthly Fee",
                    "Exam Fee",
                    "Transport Fee",
                    "Hostel Fee",
                    "Library Fee",
                    "Computer Fee",
                    "Other"
                ]
            )

            total_fee = st.number_input(
                "Total Fee",
                min_value=0.0
            )

            paid_amount = st.number_input(
                "Paid Amount",
                min_value=0.0
            )

            due_amount = max(
                total_fee - paid_amount,
                0
            )

            st.metric(
                "Due Amount",
                f"Rs. {due_amount:,.2f}"
            )

            payment_method = st.selectbox(
                "Payment Method",
                [
                    "Cash",
                    "eSewa",
                    "Khalti",
                    "Bank Transfer",
                    "Cheque"
                ]
            )

            remarks = st.text_area(
                "Remarks"
            )

            if st.button(
                "💾 Save Fee",
                use_container_width=True
            ):

                if paid_amount > total_fee:

                    st.error(
                        "Paid amount cannot be greater than total fee."
                    )

                else:

                    receipt_no = (
                        "REC-"
                        +
                        str(
                            uuid.uuid4()
                        )[:8].upper()
                    )

                    try:

                        (
                            supabase
                            .table("fees")
                            .insert({

                                "receipt_no":
                                    receipt_no,

                                "admission_no":
                                    student[
                                        "admission_no"
                                    ],

                                "student_name":
                                    student[
                                        "name"
                                    ],

                                "class_name":
                                    student[
                                        "class_name"
                                    ],

                                "fee_type":
                                    fee_type,

                                "total_fee":
                                    total_fee,

                                "paid_amount":
                                    paid_amount,

                                "due_amount":
                                    due_amount,

                                "payment_method":
                                    payment_method,

                                "payment_date":
                                    str(
                                        date.today()
                                    ),

                                "remarks":
                                    remarks

                            })
                            .execute()
                        )

                        if paid_amount > 0:

                            (
                                supabase
                                .table("finances")
                                .insert({

                                    "transaction_type":
                                        "Income",

                                    "category":
                                        fee_type,

                                    "amount":
                                        paid_amount,

                                    "description":
                                        f"Fee received from "
                                        f"{student['name']}",

                                    "transaction_date":
                                        str(
                                            date.today()
                                        )

                                })
                                .execute()
                            )

                        st.success(
                            f"Fee Saved Successfully! "
                            f"Receipt: {receipt_no}"
                        )

                    except Exception as e:

                        st.error(
                            f"Error: {e}"
                        )


    # =====================================================
    # PAYMENT APPROVAL
    # =====================================================

    elif menu == "💳 Payment Approval":

        st.title(
            "💳 Student Payment Approval"
        )

        result = (
            supabase
            .table("payment_requests")
            .select("*")
            .eq(
                "status",
                "Pending"
            )
            .order(
                "id",
                desc=True
            )
            .execute()
        )

        if not result.data:

            st.success(
                "No Pending Payment Requests."
            )

        for payment in result.data:

            with st.expander(
                f"💳 {payment['payment_id']} | "
                f"{payment['student_name']} | "
                f"Rs. {payment['amount']}"
            ):

                st.write(
                    f"Admission No: "
                    f"{payment['admission_no']}"
                )

                st.write(
                    f"Payment Method: "
                    f"{payment['payment_method']}"
                )

                st.write(
                    f"Transaction ID: "
                    f"{payment['transaction_id']}"
                )

                c1, c2 = st.columns(2)

                with c1:

                    if st.button(
                        "✅ Approve",
                        key=f"approve_{payment['id']}"
                    ):

                        fees = (
                            supabase
                            .table("fees")
                            .select("*")
                            .eq(
                                "admission_no",
                                payment[
                                    "admission_no"
                                ]
                            )
                            .gt(
                                "due_amount",
                                0
                            )
                            .order(
                                "id"
                            )
                            .limit(1)
                            .execute()
                        )

                        if fees.data:

                            fee = fees.data[0]

                            new_paid = (
                                float(
                                    fee[
                                        "paid_amount"
                                    ] or 0
                                )
                                +
                                float(
                                    payment[
                                        "amount"
                                    ]
                                )
                            )

                            new_due = max(
                                float(
                                    fee[
                                        "total_fee"
                                    ]
                                )
                                -
                                new_paid,
                                0
                            )

                            (
                                supabase
                                .table("fees")
                                .update({

                                    "paid_amount":
                                        new_paid,

                                    "due_amount":
                                        new_due

                                })
                                .eq(
                                    "id",
                                    fee["id"]
                                )
                                .execute()
                            )

                            (
                                supabase
                                .table(
                                    "payment_requests"
                                )
                                .update({

                                    "status":
                                        "Approved"

                                })
                                .eq(
                                    "id",
                                    payment["id"]
                                )
                                .execute()
                            )

                            (
                                supabase
                                .table("finances")
                                .insert({

                                    "transaction_type":
                                        "Income",

                                    "category":
                                        "Online Fee Payment",

                                    "amount":
                                        payment[
                                            "amount"
                                        ],

                                    "description":
                                        f"Online payment "
                                        f"from "
                                        f"{payment['student_name']}",

                                    "transaction_date":
                                        str(
                                            date.today()
                                        )

                                })
                                .execute()
                            )

                            st.success(
                                "Payment Approved!"
                            )

                            st.rerun()

                        else:

                            st.error(
                                "Student due fee record not found."
                            )

                with c2:

                    if st.button(
                        "❌ Reject",
                        key=f"reject_{payment['id']}"
                    ):

                        (
                            supabase
                            .table(
                                "payment_requests"
                            )
                            .update({

                                "status":
                                    "Rejected"

                            })
                            .eq(
                                "id",
                                payment["id"]
                            )
                            .execute()
                        )

                        st.warning(
                            "Payment Rejected."
                        )

                        st.rerun()


   



    # =====================================================
    # FEE RECEIPTS
    # =====================================================

    elif menu == "🧾 Fee Receipts":

        st.title("🧾 Fee Receipts")
        st.caption(
            "View all fee records and generate a printable receipt for any selected student."
        )

        try:

            fee_result = (
                supabase
                .table("fees")
                .select("*")
                .order("id", desc=True)
                .execute()
            )

            fee_records = fee_result.data or []

            if not fee_records:

                st.info("No fee records found yet.")

            else:

                fee_df = pd.DataFrame(fee_records)

                fee_df["total_fee"] = pd.to_numeric(
                    fee_df.get("total_fee", 0),
                    errors="coerce"
                ).fillna(0)

                fee_df["paid_amount"] = pd.to_numeric(
                    fee_df.get("paid_amount", 0),
                    errors="coerce"
                ).fillna(0)

                fee_df["due_amount"] = pd.to_numeric(
                    fee_df.get("due_amount", 0),
                    errors="coerce"
                ).fillna(0)

                fee_df["payment_status"] = fee_df["due_amount"].apply(
                    lambda value: "Paid"
                    if float(value or 0) <= 0 else "Due"
                )

                display_df = fee_df[[
                    "receipt_no",
                    "admission_no",
                    "student_name",
                    "class_name",
                    "fee_type",
                    "total_fee",
                    "paid_amount",
                    "due_amount",
                    "payment_status",
                    "payment_method",
                    "payment_date",
                    "remarks"
                ]].copy()

                display_df = display_df.rename(columns={
                    "receipt_no": "Receipt No",
                    "admission_no": "Admission No",
                    "student_name": "Student Name",
                    "class_name": "Class",
                    "fee_type": "Fee Type",
                    "total_fee": "Total Fee",
                    "paid_amount": "Paid Amount",
                    "due_amount": "Due Amount",
                    "payment_status": "Payment Status",
                    "payment_method": "Payment Method",
                    "payment_date": "Payment Date",
                    "remarks": "Remarks"
                })

                st.dataframe(
                    display_df,
                    use_container_width=True,
                    hide_index=True
                )

                options = {
                    f"{row['Receipt No']} | {row['Student Name']} | {row['Fee Type']} | {row['Payment Status']}": idx
                    for idx, row in display_df.iterrows()
                }

                selected_label = st.selectbox(
                    "Select a student fee record",
                    list(options.keys())
                )

                selected_index = options[selected_label]
                selected_fee = fee_df.iloc[selected_index].to_dict()

                st.info(
                    f"Selected receipt: {selected_fee.get('receipt_no', 'N/A')}"
                )

                if st.button(
                    "🖨 Generate Printable Receipt",
                    use_container_width=True
                ):

                    selected_fee["payment_status"] = (
                        "Paid"
                        if float(selected_fee.get("due_amount", 0) or 0) <= 0
                        else "Due"
                    )

                    selected_fee["generated_at"] = (
                        datetime.now().strftime(
                            "%d-%m-%Y %H:%M:%S"
                        )
                    )

                    selected_fee["receipt_date"] = (
                        selected_fee.get("payment_date")
                        or str(date.today())
                    )

                    selected_fee["receipt_time"] = (
                        datetime.now().strftime(
                            "%H:%M:%S"
                        )
                    )

                    selected_fee["accountant_name"] = (
                        st.session_state.get(
                            "username",
                            "Accountant"
                        )
                    )

                    receipt_bytes = create_receipt_pdf(
                        selected_fee,
                        {
                            "school_name": "Shree Janta Seconadry School "
                        }
                    )

                    receipt_payload = {
                        "receipt_no": selected_fee.get("receipt_no"),
                        "admission_no": selected_fee.get("admission_no"),
                        "student_name": selected_fee.get("student_name"),
                        "class_name": selected_fee.get("class_name"),
                        "fee_type": selected_fee.get("fee_type"),
                        "total_fee": float(selected_fee.get("total_fee") or 0),
                        "paid_amount": float(selected_fee.get("paid_amount") or 0),
                        "due_amount": float(selected_fee.get("due_amount") or 0),
                        "payment_method": selected_fee.get("payment_method"),
                        "payment_status": selected_fee.get("payment_status"),
                        "payment_date": selected_fee.get("payment_date") or str(date.today()),
                        "receipt_time": selected_fee.get("receipt_time"),
                        "remarks": selected_fee.get("remarks"),
                        "generated_at": selected_fee.get("generated_at"),
                        "generated_by": selected_fee.get("accountant_name")
                    }

                    try:

                        save_fee_receipt(receipt_payload)
                        st.success("Receipt saved to fee_receipts table.")

                    except Exception as insert_error:

                        st.warning(
                            f"Receipt preview is ready, but saving to fee_receipts failed: {insert_error}"
                        )

                    st.download_button(
                        label="📄 Download PDF Receipt",
                        data=receipt_bytes,
                        file_name=f"fee_receipt_{selected_fee.get('receipt_no', 'student')}.pdf",
                        mime="application/pdf"
                    )

                    receipt_html = f"""
                    <style>
                    .receipt-card {{
                        font-family: Arial, sans-serif;
                        max-width: 760px;
                        margin: 20px auto;
                        background: #ffffff;
                        color: #111827;
                        border: 2px solid #0f172a;
                        border-radius: 12px;
                        padding: 24px;
                        box-shadow: 0 10px 30px rgba(0,0,0,0.15);
                    }}
                    .receipt-header {{
                        background: linear-gradient(90deg, #0f172a 0%, #1d4ed8 100%);
                        color: white;
                        padding: 18px 20px;
                        border-radius: 10px;
                        text-align: center;
                    }}
                    .receipt-title {{ font-size: 24px; font-weight: bold; margin: 0; }}
                    .receipt-subtitle {{ font-size: 13px; margin-top: 4px; opacity: 0.92; }}
                    .receipt-meta {{ display: flex; justify-content: space-between; margin: 16px 0 10px; font-size: 13px; }}
                    .receipt-table {{ width: 100%; border-collapse: collapse; margin-top: 12px; }}
                    .receipt-table td {{ padding: 8px 10px; border-bottom: 1px solid #e5e7eb; vertical-align: top; }}
                    .receipt-label {{ font-weight: bold; color: #374151; }}
                    .receipt-total {{ background: #f8fafc; font-weight: bold; }}
                    .receipt-footer {{ display: flex; justify-content: space-between; margin-top: 26px; font-size: 13px; }}
                    .print-btn {{
                        display: inline-block;
                        margin-top: 14px;
                        padding: 10px 16px;
                        background: #2563eb;
                        color: white;
                        border: none;
                        border-radius: 8px;
                        cursor: pointer;
                        font-size: 14px;
                    }}
                    @media print {{
                        body {{ background: white !important; }}
                        .no-print {{ display: none !important; }}
                        .receipt-card {{ box-shadow: none; border: 1px solid #111827; margin: 0; }}
                    }}
                    </style>

                    <div class="receipt-card">
                        <div class="receipt-header">
                            <div class="receipt-title">Shree Janta Secondary School</div>
                            <div class="receipt-subtitle">Official Fee Payment Receipt</div>
                        </div>

                        <div class="receipt-meta">
                            <div><b>Receipt No:</b> {selected_fee.get('receipt_no', 'N/A')}</div>
                            <div><b>Date:</b> {selected_fee.get('payment_date') or str(date.today())}</div>
                        </div>

                        <p style="margin: 8px 0 14px; font-size: 14px;"><b>Student:</b> {selected_fee.get('student_name', '')} &nbsp;|&nbsp; <b>Admission No:</b> {selected_fee.get('admission_no', '')}</p>

                        <table class="receipt-table">
                            <tr><td class="receipt-label">Class</td><td>{selected_fee.get('class_name', '')}</td></tr>
                            <tr><td class="receipt-label">Fee Type</td><td>{selected_fee.get('fee_type', '')}</td></tr>
                            <tr><td class="receipt-label">Payment Method</td><td>{selected_fee.get('payment_method', '')}</td></tr>
                            <tr><td class="receipt-label">Payment Status</td><td>{selected_fee.get('payment_status', 'Due')}</td></tr>
                            <tr><td class="receipt-label">Payment Date</td><td>{selected_fee.get('payment_date') or str(date.today())}</td></tr>
                            <tr><td class="receipt-label">Remarks</td><td>{selected_fee.get('remarks') or 'N/A'}</td></tr>
                            <tr class="receipt-total"><td class="receipt-label">Total Fee</td><td>Rs. {float(selected_fee.get('total_fee') or 0):,.2f}</td></tr>
                            <tr class="receipt-total"><td class="receipt-label">Paid Amount</td><td>Rs. {float(selected_fee.get('paid_amount') or 0):,.2f}</td></tr>
                            <tr class="receipt-total"><td class="receipt-label">Due Amount</td><td>Rs. {float(selected_fee.get('due_amount') or 0):,.2f}</td></tr>
                        </table>

                        <div class="receipt-footer">
                            <div>
                                <div>Prepared by</div>
                                <div style="margin-top: 10px; font-weight: bold;">{selected_fee.get('accountant_name', 'Accountant')}</div>
                            </div>
                            <div style="text-align: right;">
                                <div>Generated at</div>
                                <div style="margin-top: 10px; font-weight: bold;">{selected_fee.get('generated_at', '')}</div>
                            </div>
                        </div>

                        <div style="margin-top: 28px; display:flex; justify-content:space-between; font-size:13px;">
                            <div>__________________________<br>Accountant Signature</div>
                            <div>__________________________<br>Student Signature</div>
                        </div>
                    </div>

                    <div class="no-print" style="margin-top: 12px;">
                        <button class="print-btn" onclick="window.print()">🖨 Print Receipt</button>
                    </div>
                    """

                    st.components.v1.html(
                        receipt_html,
                        height=950,
                        scrolling=True
                    )

        except Exception as e:

            st.error(f"❌ Fee Receipt Error: {e}")

    # =====================================================
    # PAYROLL
    # =====================================================

    elif menu == "🧾 Payroll":

        render_salary_management_section(
            title="🧾 Payroll",
            caption="Review teacher salary details and print a single teacher salary receipt.",
            teacher_id_key="payroll_teacher_id",
            submit_label="🖨 Print Salary Receipt",
            show_history=False
        )

    # =====================================================
    # SALARY MANAGEMENT
    # =====================================================

    elif menu == "💼 Salary Management":

        render_salary_management_section(
            title="💼 Salary Management",
            caption="Pay salaries to teachers, save payment records, and print salary slips.",
            teacher_id_key="salary_teacher_id",
            submit_label="💸 Pay Salary",
            show_history=True
        )

    # =====================================================
    # STUDENT ATTENDANCE
    # =====================================================

    elif menu == "📅 Student Attendance":

        st.title(
            "📅 Student Attendance"
        )

        students = (
            supabase
            .table("students")
            .select(
                "admission_no,name,class_name,section"
            )
            .execute()
        )

        if students.data:
            student_map = {
                f"{x['admission_no']} | {x['name']} | {x.get('class_name', '')} | {x.get('section', '')}": x
                for x in students.data
            }

            student = student_map[st.selectbox(
                "Select Student",
                list(student_map.keys())
            )]

            with st.form("student_attendance_form"):
                attendance_date = st.date_input(
                    "Attendance Date",
                    value=date.today()
                )

                status = st.selectbox(
                    "Attendance Status",
                    [
                        "Present",
                        "Absent",
                        "Late",
                        "Leave"
                    ]
                )

                remarks = st.text_input(
                    "Remarks"
                )

                submit_attendance = st.form_submit_button(
                    "💾 Save Student Attendance"
                )

            if submit_attendance:
                try:
                    (
                        supabase
                        .table("student_attendance")
                        .insert({
                            "admission_no": student["admission_no"],
                            "student_name": student["name"],
                            "class_name": student.get("class_name", ""),
                            "section": student.get("section", ""),
                            "attendance_date": str(attendance_date),
                            "status": status,
                            "remarks": remarks
                        })
                        .execute()
                    )
                    st.success("Student attendance saved successfully.")
                except Exception as e:
                    st.error(f"Error saving student attendance: {e}")

            try:
                attendance_history = (
                    supabase
                    .table("student_attendance")
                    .select("admission_no,student_name,class_name,section,attendance_date,status,remarks")
                    .eq("admission_no", student["admission_no"])
                    .order("id", desc=True)
                    .limit(20)
                    .execute()
                )

                if attendance_history.data:
                    st.markdown("#### Recent Attendance Records")
                    st.dataframe(
                        pd.DataFrame(attendance_history.data),
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.info("No attendance records found for this student yet.")
            except Exception as e:
                st.error(f"Error loading attendance history: {e}")
        else:
            st.info("Please add students first before recording attendance.")


    # =====================================================
    # TEACHER ATTENDANCE
    # =====================================================

    elif menu == "📅 Teacher Attendance":

        st.title(
            "📅 Teacher Attendance"
        )

        teachers = (
            supabase
            .table("teachers")
            .select(
                "teacher_id,name"
            )
            .execute()
        )

        if teachers.data:
            teacher_map = {
                f"{x['teacher_id']} | {x['name']}": x
                for x in teachers.data
            }

            teacher = teacher_map[st.selectbox(
                "Select Teacher",
                list(teacher_map.keys())
            )]

            with st.form("teacher_attendance_form"):
                attendance_date = st.date_input(
                    "Attendance Date",
                    value=date.today()
                )

                status = st.selectbox(
                    "Status",
                    [
                        "Present",
                        "Absent",
                        "Late",
                        "Leave"
                    ]
                )

                remarks = st.text_input(
                    "Remarks"
                )

                submit_teacher_attendance = st.form_submit_button(
                    "💾 Save Teacher Attendance"
                )

            if submit_teacher_attendance:
                try:
                    (
                        supabase
                        .table("teacher_attendance")
                        .insert({
                            "teacher_id": teacher["teacher_id"],
                            "teacher_name": teacher["name"],
                            "attendance_date": str(attendance_date),
                            "status": status,
                            "remarks": remarks
                        })
                        .execute()
                    )
                    st.success("Teacher attendance saved successfully.")
                except Exception as e:
                    st.error(f"Error saving teacher attendance: {e}")

            try:
                attendance_history = (
                    supabase
                    .table("teacher_attendance")
                    .select("teacher_id,teacher_name,attendance_date,status,remarks")
                    .eq("teacher_id", teacher["teacher_id"])
                    .order("id", desc=True)
                    .limit(20)
                    .execute()
                )

                if attendance_history.data:
                    st.markdown("#### Recent Attendance Records")
                    st.dataframe(
                        pd.DataFrame(attendance_history.data),
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.info("No attendance records found for this teacher yet.")
            except Exception as e:
                st.error(f"Error loading attendance history: {e}")
        else:
            st.info("Please add teachers first before recording attendance.")


    # =====================================================
    # STUDENT MARKS
    # =====================================================

    elif menu == "📝 Student Marks":

        st.title(
            "📝 Student Marks Management"
        )

        students = (
            supabase
            .table("students")
            .select(
                "admission_no,name,class_name"
            )
            .execute()
        )

        if students.data:

            student_map = {

                f"{x['admission_no']} | "
                f"{x['name']}":
                x

                for x in students.data

            }

            selected = st.selectbox(
                "Select Student",
                list(
                    student_map.keys()
                )
            )

            student = student_map[selected]

            exam_name = st.text_input(
                "Exam Name"
            )

            subject = st.text_input(
                "Subject"
            )

            c1, c2, c3 = st.columns(3)

            with c1:

                full_marks = st.number_input(
                    "Full Marks",
                    min_value=1.0,
                    value=100.0
                )

            with c2:

                pass_marks = st.number_input(
                    "Pass Marks",
                    min_value=0.0,
                    value=40.0
                )

            with c3:

                obtained_marks = st.number_input(
                    "Obtained Marks",
                    min_value=0.0,
                    max_value=full_marks
                )

            percentage = (
                obtained_marks
                /
                full_marks
                *
                100
            )

            grade = get_grade(
                percentage
            )

            st.info(
                f"Percentage: {percentage:.2f}% | "
                f"Grade: {grade}"
            )

            remarks = st.text_input(
                "Remarks"
            )

            if st.button(
                "💾 Save Marks"
            ):

                try:

                    (
                        supabase
                        .table("marks")
                        .insert({

                            "admission_no":
                                student[
                                    "admission_no"
                                ],

                            "student_name":
                                student[
                                    "name"
                                ],

                            "class_name":
                                student[
                                    "class_name"
                                ],

                            "exam_name":
                                exam_name,

                            "subject":
                                subject,

                            "full_marks":
                                full_marks,

                            "pass_marks":
                                pass_marks,

                            "obtained_marks":
                                obtained_marks,

                            "grade":
                                grade,

                            "remarks":
                                remarks

                        })
                        .execute()
                    )

                    st.success(
                        "Marks Saved Successfully!"
                    )

                except Exception as e:

                    st.error(
                        f"Error: {e}"
                    )


    # =====================================================
    # FINANCIAL
    # =====================================================

    elif menu == "📊 Financial":

        st.title(
            "📊 Financial Management"
        )

        transaction_type = st.selectbox(
            "Transaction Type",
            [
                "Income",
                "Expense"
            ]
        )

        category = st.text_input(
            "Category"
        )

        amount = st.number_input(
            "Amount",
            min_value=0.0
        )

        description = st.text_area(
            "Description"
        )

        if st.button(
            "💾 Save Transaction"
        ):

            try:

                (
                    supabase
                    .table("finances")
                    .insert({

                        "transaction_type":
                            transaction_type,

                        "category":
                            category,

                        "amount":
                            amount,

                        "description":
                            description,

                        "transaction_date":
                            str(
                                date.today()
                            )

                    })
                    .execute()
                )

                st.success(
                    "Transaction Saved!"
                )

            except Exception as e:

                st.error(
                    f"Error: {e}"
                )

        result = (
            supabase
            .table("finances")
            .select("*")
            .order(
                "id",
                desc=True
            )
            .execute()
        )

        st.dataframe(
            result.data,
            use_container_width=True
        )


    # =====================================================
    # SCHOOL INFORMATION
    # =====================================================

    elif menu == "🏫 About School":

        st.title(
            "🏫 About School"
        )

        result = (
            supabase
            .table("school_info")
            .select("*")
            .limit(1)
            .execute()
        )

        old = (
            result.data[0]
            if result.data
            else {}
        )

        school_name = st.text_input(
            "School Name",
            value=old.get(
                "school_name",
                ""
            )
        )

        address = st.text_input(
            "Address",
            value=old.get(
                "address",
                ""
            )
        )

        phone = st.text_input(
            "Phone",
            value=old.get(
                "phone",
                ""
            )
        )

        email = st.text_input(
            "Email",
            value=old.get(
                "email",
                ""
            )
        )

        principal_name = st.text_input(
            "Principal Name",
            value=old.get(
                "principal_name",
                ""
            )
        )

        about = st.text_area(
            "About School",
            value=old.get(
                "about",
                ""
            )
        )

        if st.button(
            "💾 Save School Information"
        ):

            try:

                data = {

                    "school_name":
                        school_name,

                    "address":
                        address,

                    "phone":
                        phone,

                    "email":
                        email,

                    "principal_name":
                        principal_name,

                    "about":
                        about

                }

                if old:

                    (
                        supabase
                        .table("school_info")
                        .update(data)
                        .eq(
                            "id",
                            old["id"]
                        )
                        .execute()
                    )

                else:

                    (
                        supabase
                        .table("school_info")
                        .insert(data)
                        .execute()
                    )

                st.success(
                    "School Information Saved!"
                )

            except Exception as e:

                st.error(
                    f"Error: {e}"
                )


# =========================================================
# PRINCIPAL DASHBOARD
# =========================================================

def principal_dashboard():

    st.sidebar.title(
        "🏛️ PRINCIPAL PORTAL"
    )

    st.sidebar.write(
        f"Welcome, {st.session_state.username}"
    )

    menu = st.sidebar.radio(
        "Navigation",
        [
            "🏠 Dashboard",
            "👨‍🎓 Students",
            "👨‍🏫 Teachers",
            "💰 Fees",
            "🧾 Receipts",
            "📊 Finance"
        ]
    )

    if st.sidebar.button(
        "🚪 Logout",
        use_container_width=True
    ):

        logout()

    if menu == "🏠 Dashboard":

        st.markdown(
            """
            <div class="school-card">
                <h2 style="margin:0 0 8px 0;">👨‍🏫 Principal Overview</h2>
                <p style="margin:0; color:#d1d5db;">A secure view of the school’s academic, financial, and student activity.</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.title("🏛️ Principal Dashboard")

        try:

            students = supabase.table("students").select("id").execute()
            teachers = supabase.table("teachers").select("id").execute()
            fees = supabase.table("fees").select("total_fee,paid_amount,due_amount").execute()
            receipts = supabase.table("fee_receipts").select("id").execute()

            total_fee = sum(float(x.get("total_fee") or 0) for x in fees.data or [])
            paid = sum(float(x.get("paid_amount") or 0) for x in fees.data or [])
            due = sum(float(x.get("due_amount") or 0) for x in fees.data or [])

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("👨‍🎓 Students", len(students.data or []))
            c2.metric("👨‍🏫 Teachers", len(teachers.data or []))
            c3.metric("🧾 Receipts", len(receipts.data or []))
            c4.metric("📌 Due Fee", f"Rs. {due:,.2f}")

            st.divider()

            c1, c2, c3 = st.columns(3)
            c1.metric("💰 Total Fee", f"Rs. {total_fee:,.2f}")
            c2.metric("✅ Paid", f"Rs. {paid:,.2f}")
            c3.metric("📈 Outstanding", f"Rs. {due:,.2f}")

        except Exception as e:
            st.error(f"Principal dashboard error: {e}")

    elif menu == "👨‍🎓 Students":

        st.title("👨‍🎓 Student Records")

        try:
            students = supabase.table("students").select("*").execute()
            if students.data:
                st.dataframe(pd.DataFrame(students.data), use_container_width=True)
            else:
                st.info("No student records found.")
        except Exception as e:
            st.error(f"Error: {e}")

    elif menu == "👨‍🏫 Teachers":

        st.title("👨‍🏫 Teacher Records")

        try:
            teachers = supabase.table("teachers").select("*").execute()
            if teachers.data:
                st.dataframe(pd.DataFrame(teachers.data), use_container_width=True)
            else:
                st.info("No teacher records found.")
        except Exception as e:
            st.error(f"Error: {e}")

    elif menu == "💰 Fees":

        st.title("💰 Fee Records")

        try:
            fees = supabase.table("fees").select("*").execute()
            if fees.data:
                st.dataframe(pd.DataFrame(fees.data), use_container_width=True)
            else:
                st.info("No fee records found.")
        except Exception as e:
            st.error(f"Error: {e}")

    elif menu == "🧾 Receipts":

        st.title("🧾 Fee Receipts")

        try:
            receipts = supabase.table("fee_receipts").select("*").execute()
            if receipts.data:
                st.dataframe(pd.DataFrame(receipts.data), use_container_width=True)
            else:
                st.info("No receipt records found.")
        except Exception as e:
            st.error(f"Error: {e}")

    elif menu == "📊 Finance":

        st.title("📊 Finance Records")

        try:
            finance = supabase.table("finances").select("*").execute()
            if finance.data:
                st.dataframe(pd.DataFrame(finance.data), use_container_width=True)
            else:
                st.info("No finance records found.")
        except Exception as e:
            st.error(f"Error: {e}")


# =========================================================
# STUDENT DASHBOARD
# =========================================================

def student_dashboard():

    admission_no = (
        st.session_state.admission_no
    )

    result = (
        supabase
        .table("students")
        .select("*")
        .eq(
            "admission_no",
            admission_no
        )
        .execute()
    )

    if not result.data:

        st.error(
            "Student Record Not Found."
        )

        return

    student = result.data[0]

    st.sidebar.title(
        "👨‍🎓 STUDENT PORTAL"
    )

    st.sidebar.write(
        f"Welcome, {student['name']}"
    )

    menu = st.sidebar.radio(
        "Navigation",
        [
            "🏠 Dashboard",
            "👤 My Profile",
            "💰 My Fees",
            "💳 Pay Fee",
            "🧾 My Receipts",
            "📊 My Marks",
            "📅 My Attendance"
        ]
    )

    if st.sidebar.button(
        "🚪 Logout",
        use_container_width=True
    ):

        logout()


    # =====================================================
    # STUDENT DASHBOARD HOME
    # =====================================================

    if menu == "🏠 Dashboard":

        st.markdown(
            f"""
            <div class="school-card login-panel">
                <h2 style="margin:0 0 8px 0;">🎓 Student Portal</h2>
                <p style="margin:0; color:#d1d5db;">Welcome back, {student['name']}. Your academic and fee information is organized here.</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.title(
            f"🏠 Welcome, {student['name']}"
        )

        fees = (
            supabase
            .table("fees")
            .select(
                "total_fee,paid_amount,due_amount"
            )
            .eq(
                "admission_no",
                admission_no
            )
            .execute()
        )

        total = sum(
            float(
                x["total_fee"] or 0
            )
            for x in fees.data
        )

        paid = sum(
            float(
                x["paid_amount"] or 0
            )
            for x in fees.data
        )

        due = sum(
            float(
                x["due_amount"] or 0
            )
            for x in fees.data
        )

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "💰 Total Fee",
            f"Rs. {total:,.2f}"
        )

        c2.metric(
            "✅ Paid",
            f"Rs. {paid:,.2f}"
        )

        c3.metric(
            "📌 Due",
            f"Rs. {due:,.2f}"
        )


    # =====================================================
    # PROFILE
    # =====================================================

    elif menu == "👤 My Profile":

        st.title(
            "👤 My Profile"
        )

        for key, value in student.items():

            if key not in [
                "id",
                "password"
            ]:

                st.write(
                    f"**{key.replace('_', ' ').title()}:** "
                    f"{value}"
                )


    # =====================================================
    # MY FEES
    # =====================================================

    elif menu == "💰 My Fees":

        st.title(
            "💰 My Fee Details"
        )

        result = (
            supabase
            .table("fees")
            .select("*")
            .eq(
                "admission_no",
                admission_no
            )
            .order(
                "id",
                desc=True
            )
            .execute()
        )

        if result.data:

            st.dataframe(
                result.data,
                use_container_width=True
            )

        else:

            st.info(
                "No Fee Records Found."
            )


    # =====================================================
    # PAY FEE
    # =====================================================

    elif menu == "💳 Pay Fee":

        st.title(
            "💳 Pay School Fee"
        )

        fees = (
            supabase
            .table("fees")
            .select(
                "due_amount"
            )
            .eq(
                "admission_no",
                admission_no
            )
            .execute()
        )

        due = sum(
            float(
                x["due_amount"] or 0
            )
            for x in fees.data
        )

        st.metric(
            "Current Due Amount",
            f"Rs. {due:,.2f}"
        )

        if due > 0:

            amount = st.number_input(
                "Payment Amount",
                min_value=1.0,
                max_value=due
            )

            payment_method = st.selectbox(
                "Payment Method",
                [
                    "eSewa",
                    "Khalti",
                    "Bank Transfer"
                ]
            )

            transaction_id = st.text_input(
                "Transaction ID"
            )

            remarks = st.text_area(
                "Remarks"
            )

            if st.button(
                "💳 Submit Payment Request",
                use_container_width=True
            ):

                if not transaction_id:

                    st.error(
                        "Transaction ID required."
                    )

                else:

                    payment_id = (
                        "PAY-"
                        +
                        str(
                            uuid.uuid4()
                        )[:8].upper()
                    )

                    try:

                        (
                            supabase
                            .table(
                                "payment_requests"
                            )
                            .insert({

                                "payment_id":
                                    payment_id,

                                "admission_no":
                                    admission_no,

                                "student_name":
                                    student[
                                        "name"
                                    ],

                                "amount":
                                    amount,

                                "payment_method":
                                    payment_method,

                                "transaction_id":
                                    transaction_id,

                                "payment_date":
                                    str(
                                        date.today()
                                    ),

                                "status":
                                    "Pending",

                                "remarks":
                                    remarks

                            })
                            .execute()
                        )

                        st.success(
                            "Payment Request Submitted Successfully!"
                        )

                        st.info(
                            f"Payment ID: {payment_id}"
                        )

                    except Exception as e:

                        st.error(
                            f"Payment Error: {e}"
                        )

        else:

            st.success(
                "🎉 You have no fee due."
            )

    # =====================================================
    #   MY Receipts 
    #====================================================

    elif menu == "🧾 My Receipts":

        st.title(
            "🧾 My Fee Receipts"
        )

        result = (
            supabase
            .table("fees")
            .select("*")
            .eq(
                "admission_no",
                admission_no
            )
            .order(
                "id",
                desc=True
            )
            .execute()
        )

        if not result.data:

            st.info(
                "No Receipts Found."
            )

        else:

            receipt_names = [

                x["receipt_no"]

                for x in result.data

            ]

            selected = st.selectbox(
                "Select Receipt",
                receipt_names
            )

            receipt = next(

                x

                for x in result.data

                if x["receipt_no"]
                ==
                selected

            )

            st.subheader(
                "🏫 FEE RECEIPT"
            )

            st.write(
                f"Receipt No: "
                f"{receipt['receipt_no']}"
            )

            st.write(
                f"Student: "
                f"{receipt['student_name']}"
            )

            st.write(
                f"Admission No: "
                f"{receipt['admission_no']}"
            )

            st.write(
                f"Class: "
                f"{receipt['class_name']}"
            )

            st.write(
                f"Total Fee: "
                f"Rs. {receipt['total_fee']}"
            )

            st.write(
                f"Paid: "
                f"Rs. {receipt['paid_amount']}"
            )

            st.write(
                f"Due: "
                f"Rs. {receipt['due_amount']}"
            )

            school_result = (
                supabase
                .table("school_info")
                .select("*")
                .limit(1)
                .execute()
            )

            school = (
                school_result.data[0]
                if school_result.data
                else {}
            )

            pdf_data = create_receipt_pdf(
                receipt,
                school
            )

            st.download_button(
                label="📄 Download PDF Receipt",
                data=pdf_data,
                file_name=f"fee_receipt_{receipt.get('receipt_no', 'student')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )

           

    # =====================================================
    # MY MARKS
    # =====================================================

    elif menu == "📊 My Marks":

        st.title(
            "📊 My Marks"
        )

        result = (
            supabase
            .table("marks")
            .select("*")
            .eq(
                "admission_no",
                admission_no
            )
            .order(
                "id",
                desc=True
            )
            .execute()
        )

        if result.data:

            st.dataframe(
                result.data,
                use_container_width=True
            )

        else:

            st.info(
                "No Marks Records Found."
            )


    # =====================================================
    # MY ATTENDANCE
    # =====================================================

    elif menu == "📅 My Attendance":

        st.title(
            "📅 My Attendance"
        )

        result = (
            supabase
            .table(
                "student_attendance"
            )
            .select("*")
            .eq(
                "admission_no",
                admission_no
            )
            .order(
                "attendance_date",
                desc=True
            )
            .execute()
        )

        if result.data:

            st.dataframe(
                result.data,
                use_container_width=True
            )

        else:

            st.info(
                "No Attendance Records Found."
            )


# =========================================================
# MAIN APPLICATION
# =========================================================

if st.session_state.logged_in:

    if st.session_state.role == "admin":

        admin_dashboard()

    elif st.session_state.role == "student":

        student_dashboard()

    elif st.session_state.role == "principal":

        principal_dashboard()

else:

    login_page()
