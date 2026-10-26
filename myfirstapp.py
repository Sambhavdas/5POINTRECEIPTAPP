import streamlit as st
import sqlite3
from pathlib import Path
from datetime import date
from fpdf import FPDF
import pandas as pd
import html

# ==================================================
# APP SETTINGS
# ==================================================

st.set_page_config(
    page_title="5Point | Receipt Generator",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="expanded"
)

from pathlib import Path


APP_DIR = Path(__file__).resolve().parent

DB_PATH = APP_DIR / "receipt_history.db"

# Search for the logo in the root folder or assets folder
possible_paths = [
    APP_DIR / "5point_logo.jpeg",
    APP_DIR / "assets" / "5point_logo.jpeg",
]

LOGO = next(
    (p for p in possible_paths if p.is_file()),
    None
)


ADDRESS = "Sonarpur Milanpally, Kolkata - 700150"
PHONE_NUMBER = "8100567748"  # Add your phone number here later
# ==================================================
# PROFESSIONAL UI DESIGN
# ==================================================

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    .stApp {
        background-color: #F5F7FB;
        font-family: 'Inter', sans-serif;
    }

    [data-testid="stHeader"] {
        background: transparent;
    }

    [data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: none;
    }

    [data-testid="stSidebar"] hr {
        border-color: #EDF0F5;
    }

    h1, h2, h3 {
        color: #172554;
        font-family: 'Inter', sans-serif;
    }

    .main-header {
        background: linear-gradient(120deg, #172554, #1D4ED8);
        padding: 30px 32px;
        border-radius: 18px;
        margin-bottom: 25px;
        color: white;
    }

    .main-header h1 {
        color: white !important;
        font-size: 30px;
        font-weight: 800;
        margin: 0;
    }

    .main-header p {
        color: #DBEAFE;
        font-size: 14px;
        margin: 9px 0 0 0;
    }

    .section-title {
        color: #172554;
        font-size: 21px;
        font-weight: 700;
        margin: 10px 0 5px 0;
    }

    .section-subtitle {
        color: #64748B;
        font-size: 13px;
        margin-bottom: 20px;
    }

    .receipt-sheet {
        background: #FFFFFF;
        border-radius: 18px;
        padding: 30px;
        margin: 10px 0 20px 0;
        box-shadow: 0 5px 24px rgba(15, 23, 42, 0.055);
    }

    .receipt-brand {
        color: #172554;
        font-size: 27px;
        font-weight: 800;
        margin: 0;
    }

    .receipt-address {
        color: #64748B;
        font-size: 12px;
        margin-top: 5px;
    }

    .receipt-label {
        color: #1D4ED8;
        font-size: 12px;
        font-weight: 800;
        letter-spacing: 2px;
        margin-top: 12px;
    }

    .receipt-number {
        background: #EFF6FF;
        padding: 14px 18px;
        border-radius: 10px;
        color: #1E3A8A;
        font-size: 13px;
        margin: 20px 0;
    }

    .receipt-footer {
        color: #64748B;
        font-size: 12px;
        margin-top: 28px;
        padding-top: 15px;
        border-top: 1px solid #E2E8F0;
    }

    .brand-footer {
        text-align: right;
        color: #1D4ED8;
        font-weight: 700;
    }

    div[data-testid="stForm"] {
        background: #FFFFFF;
        border: none;
        border-radius: 16px;
        padding: 25px;
        box-shadow: 0 4px 22px rgba(15, 23, 42, 0.04);
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        border: none !important;
    }

    div[data-testid="stMetric"] {
        background: #FFFFFF;
        padding: 20px;
        border-radius: 14px;
        box-shadow: 0 3px 15px rgba(15, 23, 42, 0.035);
    }

    div[data-testid="stMetricLabel"] {
        color: #64748B;
    }

    div[data-testid="stMetricValue"] {
        color: #172554;
        font-weight: 800;
    }

    .stButton > button,
    .stDownloadButton > button {
        border-radius: 9px;
        font-weight: 600;
        min-height: 42px;
    }

    .stButton > button[kind="primary"] {
        background: #1D4ED8;
        border: none;
    }

    .stButton > button[kind="primary"]:hover {
        background: #1E40AF;
    }

    [data-testid="stDataFrame"] {
        background: white;
        border-radius: 12px;
    }

    .app-footer {
        text-align: center;
        color: #94A3B8;
        font-size: 12px;
        padding: 22px 0 8px 0;
    }

    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }
</style>
""", unsafe_allow_html=True)


# ==================================================
# DATABASE
# ==================================================

def connect():
    return sqlite3.connect(DB_PATH)


def initialize_database():
    with connect() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS receipts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                receipt_no TEXT UNIQUE,
                receipt_date TEXT,
                student_id TEXT,
                admission_year TEXT,
                name TEXT,
                student_class TEXT,
                board TEXT,
                month TEXT,
                year INTEGER,
                amount REAL,
                mode TEXT,
                due_status TEXT,
                due_amount REAL
            )
        """)
        con.commit()


initialize_database()


# ==================================================
# RECEIPT HELPERS
# ==================================================

def generate_receipt_number():
    today = date.today().strftime("%Y%m")

    with connect() as con:
        row = con.execute(
            """
            SELECT COUNT(*)
            FROM receipts
            WHERE receipt_no LIKE ?
            """,
            (f"5P-{today}-%",)
        ).fetchone()

    serial = row[0] + 1
    return f"5P-{today}-{serial:04d}"


def get_receipt(receipt_no):
    with connect() as con:
        con.row_factory = sqlite3.Row

        row = con.execute(
            "SELECT * FROM receipts WHERE receipt_no = ?",
            (receipt_no,)
        ).fetchone()

        return dict(row) if row else None


def save_receipt(r):
    with connect() as con:
        con.execute("""
            INSERT INTO receipts (
                receipt_no, receipt_date, student_id,
                admission_year, name, student_class,
                board, month, year, amount, mode,
                due_status, due_amount
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            r["receipt_no"],
            r["receipt_date"],
            r["student_id"],
            r["admission_year"],
            r["name"],
            r["student_class"],
            r["board"],
            r["month"],
            r["year"],
            r["amount"],
            r["mode"],
            r["due_status"],
            r["due_amount"]
        ))
        con.commit()


def format_money(amount):
    return f"Rs. {float(amount):,.2f}"


def get_help_line():
    return PHONE_NUMBER.strip() or "Help Line: __________________"


# ==================================================
# PDF GENERATOR
# ==================================================

def create_pdf(r):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Main brand colour
    navy = (23, 37, 84)
    blue = (29, 78, 216)
    grey = (100, 116, 139)
    light_blue = (239, 246, 255)
    light_grey = (226, 232, 240)

    # Logo
    if LOGO.exists():
        try:
            pdf.image(str(LOGO), x=12, y=12, w=28)
        except Exception:
            pass

    # Brand name and contact details
    pdf.set_xy(45, 12)
    pdf.set_text_color(*navy)
    pdf.set_font("Arial", "B", 19)
    pdf.cell(0, 9, "5Point Education Hub", ln=True)

    pdf.set_x(45)
    pdf.set_text_color(*grey)
    pdf.set_font("Arial", "", 9)
    pdf.cell(0, 5, ADDRESS, ln=True)

    pdf.set_x(45)
    pdf.cell(0, 5, get_help_line(), ln=True)

    # Divider
    pdf.set_draw_color(*blue)
    pdf.set_line_width(0.8)
    pdf.line(12, 44, 198, 44)

    # Receipt title
    pdf.set_y(50)
    pdf.set_text_color(*blue)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 9, "PAYMENT RECEIPT", ln=True, align="C")

    # Receipt number background
    pdf.set_fill_color(*light_blue)
    pdf.set_text_color(*navy)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(
        95, 10,
        f"Receipt No: {r['receipt_no']}",
        border=0, fill=True
    )

    pdf.set_font("Arial", "", 10)
    pdf.cell(
        91, 10,
        f"Date: {r['receipt_date']}",
        border=0, fill=True, ln=True, align="R"
    )

    pdf.ln(8)

    # Student and payment details
    fields = [
        ("Student ID", r["student_id"]),
        ("Admission Year", r["admission_year"]),
        ("Student Name", r["name"]),
        ("Class", r["student_class"]),
        ("Board", r["board"]),
        ("Payment Month", r["month"]),
        ("Payment Year", str(r["year"])),
        ("Amount Received", format_money(r["amount"])),
        ("Payment Mode", r["mode"]),
        ("Outstanding Due", r["due_status"])
    ]

    if r["due_status"] == "Yes":
        fields.append(
            ("Due Amount", format_money(r["due_amount"]))
        )

    for index, (label, value) in enumerate(fields):
        if index % 2 == 0:
            pdf.set_fill_color(248, 250, 252)
        else:
            pdf.set_fill_color(255, 255, 255)

        pdf.set_draw_color(*light_grey)
        pdf.set_text_color(*navy)
        pdf.set_font("Arial", "B", 10)

        pdf.cell(
            60, 10, label,
            border="B", fill=True
        )

        pdf.set_text_color(51, 65, 85)
        pdf.set_font("Arial", "", 10)

        pdf.cell(
            126, 10, str(value),
            border="B", fill=True, ln=True
        )

    # Amount highlight
    pdf.ln(8)
    pdf.set_fill_color(*light_blue)
    pdf.set_text_color(*blue)
    pdf.set_font("Arial", "B", 12)

    pdf.cell(
        186, 12,
        f"TOTAL RECEIVED: {format_money(r['amount'])}",
        border=0, fill=True, ln=True, align="C"
    )

    # Footer and signature area
    pdf.ln(24)
    pdf.set_draw_color(*light_grey)

    pdf.line(15, pdf.get_y(), 75, pdf.get_y())
    pdf.line(135, pdf.get_y(), 195, pdf.get_y())

    pdf.ln(3)
    pdf.set_text_color(*grey)
    pdf.set_font("Arial", "", 9)

    pdf.cell(93, 6, "Authorized Signature / Stamp")
    pdf.cell(93, 6, "Powered by 5Point", ln=True, align="R")

    pdf.ln(10)
    pdf.set_font("Arial", "I", 9)
    pdf.cell(
        0, 6,
        "Thank you for your payment.",
        align="C"
    )

    return bytes(pdf.output())


# ==================================================
# RECEIPT PREVIEW
# ==================================================

def show_receipt(r):
    st.markdown('<div class="receipt-sheet">', unsafe_allow_html=True)

    # Logo and contact information
    logo_col, details_col = st.columns([1, 4])

    with logo_col:
        if LOGO.exists():
            st.image(str(LOGO), width=125)
        else:
            st.warning("Logo file not found.")

    with details_col:
        st.markdown(
            '<p class="receipt-brand">5Point Education Hub</p>',
            unsafe_allow_html=True
        )

        st.markdown(
            f'<p class="receipt-address">'
            f'{html.escape(ADDRESS)}<br>'
            f'{html.escape(get_help_line())}'
            f'</p>',
            unsafe_allow_html=True
        )

        st.markdown(
            '<p class="receipt-label">PAYMENT RECEIPT</p>',
            unsafe_allow_html=True
        )

    st.divider()

    receipt_col, date_col = st.columns(2)

    with receipt_col:
        st.markdown(
            f'<div class="receipt-number">'
            f'<b>Receipt No.</b><br>'
            f'{html.escape(str(r["receipt_no"]))}</div>',
            unsafe_allow_html=True
        )

    with date_col:
        st.markdown(
            f'<div class="receipt-number">'
            f'<b>Receipt Date</b><br>'
            f'{html.escape(str(r["receipt_date"]))}</div>',
            unsafe_allow_html=True
        )

    fields = [
        ["Student ID", r["student_id"]],
        ["Admission Year", r["admission_year"]],
        ["Student Name", r["name"]],
        ["Class", r["student_class"]],
        ["Board", r["board"]],
        ["Payment Month", r["month"]],
        ["Payment Year", r["year"]],
        ["Amount Received", format_money(r["amount"])],
        ["Payment Mode", r["mode"]],
        ["Outstanding Due", r["due_status"]]
    ]

    if r["due_status"] == "Yes":
        fields.append(
            ["Due Amount", format_money(r["due_amount"])]
        )

    st.table(
        pd.DataFrame(fields, columns=["Payment Details", "Information"])
    )

    st.metric(
        "Total Amount Received",
        format_money(r["amount"])
    )

    st.markdown(
        '<div class="receipt-footer">'
        '<span>Authorized Signature / Stamp</span>'
        '<span style="float:right" class="brand-footer">'
        'Powered by 5Point</span>'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown('</div>', unsafe_allow_html=True)


# ==================================================
# SESSION STATE
# ==================================================

if "draft" not in st.session_state:
    st.session_state.draft = None

if "preview" not in st.session_state:
    st.session_state.preview = False


# ==================================================
# SIDEBAR
# ==================================================

with st.sidebar:
    if LOGO.exists():
        st.image(str(LOGO), width=155)
    else:
        st.markdown("## 5Point")

    st.markdown("---")
    st.markdown("### Navigation")

    page = st.radio(
        "Choose a workspace",
        ["Generate Receipt", "Receipt History"],
        label_visibility="collapsed"
    )

    st.markdown("---")
    st.caption("5Point Education Hub")
    st.caption(ADDRESS)
    st.caption(get_help_line())


# ==================================================
# MAIN HEADER
# ==================================================

st.markdown("""
<div class="main-header">
    <h1>5Point Education Hub</h1>
    <p>Student Payment Management · Receipt Generation · Payment History</p>
</div>
""", unsafe_allow_html=True)


# ==================================================
# GENERATE RECEIPT
# ==================================================

if page == "Generate Receipt":

    if not st.session_state.preview:

        st.markdown(
            '<div class="section-title">Create a Payment Receipt</div>'
            '<div class="section-subtitle">'
            'Enter the student and payment details below.'
            '</div>',
            unsafe_allow_html=True
        )

        with st.form("receipt_form"):

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("#### Student Information")

                student_id = st.text_input("Student ID *")

                admission_year = st.text_input(
                    "Admission Year *",
                    value=str(date.today().year)
                )

                name = st.text_input("Student Name *")
                student_class = st.text_input("Class *")

                board = st.selectbox(
                    "Board",
                    ["CBSE", "ICSE", "ISC", "WBSE", "Other"]
                )

            with col2:
                st.markdown("#### Payment Information")

                receipt_date = st.date_input(
                    "Receipt Date",
                    value=date.today()
                )

                months = [
                    "January", "February", "March",
                    "April", "May", "June", "July",
                    "August", "September", "October",
                    "November", "December"
                ]

                month = st.selectbox(
                    "Payment Month",
                    months,
                    index=date.today().month - 1
                )

                year = st.number_input(
                    "Payment Year",
                    min_value=2000,
                    max_value=2100,
                    value=date.today().year,
                    step=1
                )

                amount = st.number_input(
                    "Amount Received (INR) *",
                    min_value=0.0,
                    step=100.0,
                    format="%.2f"
                )

                mode = st.radio(
                    "Payment Mode",
                    ["Offline / Cash", "Online"],
                    horizontal=True
                )

            st.markdown("---")
            st.markdown("#### Outstanding Due Information")

            due_status = st.radio(
                "Is there any outstanding due?",
                ["No", "Yes"],
                horizontal=True
            )

            due_amount = 0.0

            if due_status == "Yes":
                due_amount = st.number_input(
                    "Due Amount (INR) *",
                    min_value=0.0,
                    step=100.0,
                    format="%.2f"
                )

            submitted = st.form_submit_button(
                "Preview Receipt",
                type="primary",
                use_container_width=True
            )

        if submitted:

            if not all([
                student_id.strip(),
                admission_year.strip(),
                name.strip(),
                student_class.strip()
            ]):
                st.error("Please fill in all required student details.")

            elif amount <= 0:
                st.error("Amount received must be greater than zero.")

            elif due_status == "Yes" and due_amount <= 0:
                st.error("Please enter a valid due amount.")

            else:
                st.session_state.draft = {
                    "receipt_no": generate_receipt_number(),
                    "receipt_date": str(receipt_date),
                    "student_id": student_id.strip(),
                    "admission_year": admission_year.strip(),
                    "name": name.strip(),
                    "student_class": student_class.strip(),
                    "board": board,
                    "month": month,
                    "year": int(year),
                    "amount": float(amount),
                    "mode": mode,
                    "due_status": due_status,
                    "due_amount": (
                        float(due_amount)
                        if due_status == "Yes"
                        else 0.0
                    )
                }

                st.session_state.preview = True
                st.rerun()

    else:

        r = st.session_state.draft

        st.markdown(
            '<div class="section-title">Review Your Receipt</div>'
            '<div class="section-subtitle">'
            'Check all details before confirming and saving.'
            '</div>',
            unsafe_allow_html=True
        )

        show_receipt(r)

        st.warning(
            "Please verify the student details and payment amount "
            "before saving this receipt."
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button(
                "Back / Edit Details",
                use_container_width=True
            ):
                st.session_state.preview = False
                st.rerun()

        with col2:
            st.download_button(
                "Download PDF",
                data=create_pdf(r),
                file_name=f"{r['receipt_no']}.pdf",
                mime="application/pdf",
                use_container_width=True
            )

        with col3:
            if st.button(
                "Print Instructions",
                use_container_width=True
            ):
                st.info(
                    "Download the PDF, open it and press Ctrl+P "
                    "on Windows to print."
                )

        if st.button(
            "Confirm and Save Receipt",
            type="primary",
            use_container_width=True
        ):
            try:
                save_receipt(r)

                st.success(
                    f"Receipt {r['receipt_no']} saved successfully."
                )

                st.session_state.draft = None
                st.session_state.preview = False
                st.rerun()

            except sqlite3.IntegrityError:
                st.error(
                    "This receipt number already exists. "
                    "Please go back and create the receipt again."
                )


# ==================================================
# RECEIPT HISTORY
# ==================================================

else:

    st.markdown(
        '<div class="section-title">Receipt History</div>'
        '<div class="section-subtitle">'
        'Search, review, download or delete saved receipts.'
        '</div>',
        unsafe_allow_html=True
    )

    with connect() as con:
        history = pd.read_sql_query(
            """
            SELECT
                id AS 'Database ID',
                receipt_no AS 'Receipt Number',
                receipt_date AS 'Date',
                student_id AS 'Student ID',
                name AS 'Student Name',
                student_class AS 'Class',
                month AS 'Month',
                year AS 'Year',
                amount AS 'Amount Received',
                mode AS 'Payment Mode',
                due_status AS 'Due Status'
            FROM receipts
            ORDER BY id DESC
            """,
            con
        )

    if history.empty:
        st.info("No receipts found. Create your first receipt.")

    else:
        total_receipts = len(history)
        total_collected = history["Amount Received"].sum()
        outstanding_count = (history["Due Status"] == "Yes").sum()

        metric1, metric2, metric3 = st.columns(3)

        metric1.metric("Total Receipts", total_receipts)
        metric2.metric("Total Amount Received", format_money(total_collected))
        metric3.metric("Receipts with Due", int(outstanding_count))

        st.markdown("---")

        search = st.text_input(
            "Search by Receipt Number, Student ID or Student Name",
            placeholder="Enter receipt number, student ID or name..."
        )

        if search.strip():
            mask = (
                history["Receipt Number"].astype(str).str.contains(
                    search, case=False, na=False, regex=False
                )
                |
                history["Student ID"].astype(str).str.contains(
                    search, case=False, na=False, regex=False
                )
                |
                history["Student Name"].astype(str).str.contains(
                    search, case=False, na=False, regex=False
                )
            )

            history = history[mask]

        st.dataframe(
            history.drop(columns=["Database ID"]),
            use_container_width=True,
            hide_index=True
        )

        if not history.empty:

            selected = st.selectbox(
                "Select a receipt to view",
                history["Receipt Number"].tolist()
            )

            old_receipt = get_receipt(selected)

            if old_receipt:

                st.markdown("---")
                st.markdown("#### Selected Receipt")

                show_receipt(old_receipt)

                col1, col2 = st.columns(2)

                with col1:
                    st.download_button(
                        "Download PDF",
                        data=create_pdf(old_receipt),
                        file_name=f"{old_receipt['receipt_no']}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                        key=f"download_{old_receipt['receipt_no']}"
                    )

                with col2:
                    with st.popover(
                        "Delete Receipt",
                        use_container_width=True
                    ):
                        st.warning(
                            f"Delete receipt {old_receipt['receipt_no']} "
                            "permanently?"
                        )

                        confirm_delete = st.checkbox(
                            "Yes, I want to delete this receipt",
                            key=f"confirm_{old_receipt['receipt_no']}"
                        )

                        if st.button(
                            "Confirm Delete",
                            key=f"delete_{old_receipt['receipt_no']}",
                            use_container_width=True
                        ):
                            if confirm_delete:
                                with connect() as con:
                                    con.execute(
                                        "DELETE FROM receipts "
                                        "WHERE receipt_no = ?",
                                        (old_receipt["receipt_no"],)
                                    )
                                    con.commit()

                                st.success("Receipt deleted successfully.")
                                st.rerun()

                            else:
                                st.error(
                                    "Please tick the confirmation checkbox first."
                                )

                st.info(
                    "To print, download the PDF, open it and press Ctrl+P."
                )


# ==================================================
# FOOTER
# ==================================================

st.markdown("""
<div class="app-footer">
    5Point Education Hub &nbsp; | &nbsp;
    Milanpally, Kolkata - 700150 &nbsp; | &nbsp;
    Powered by 5Point
</div>
""", unsafe_allow_html=True)