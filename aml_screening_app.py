import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="AML Screening Dashboard",
    page_icon="🛡️",
    layout="wide"
)

# ─────────────────────────────────────────────
# CONSTANTS  ← easy to update as your project grows
# ─────────────────────────────────────────────
SANCTIONED_COUNTRIES = [
    "North Korea", "Iran", "Syria", "Russia",
    "Belarus", "Cuba", "Myanmar", "Venezuela"
]

REQUIRED_COLUMNS = {
    "name":               "Client name (text)",
    "age":                "Client age (number)",
    "country":            "Country of residence (text)",
    "is_verified":        "KYC verified? (True/False)",
    "transaction_amount": "Transaction amount in £ (number)",
    "risk_score":         "Risk score 1–4 (number)",
}

MIN_AGE          = 20      # regulatory minimum
DEFAULT_TX_LIMIT = 50_000  # £ default block threshold
DEFAULT_MIN_AGE  = 18

# ─────────────────────────────────────────────
# SIDEBAR — configurable compliance thresholds
# ─────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Compliance Settings")
    st.caption("Adjust thresholds without changing the code")

    st.subheader("Transaction Limits")
    tx_limit = st.slider(
        "Block transactions above (£)",
        min_value=1_000,
        max_value=200_000,
        value=DEFAULT_TX_LIMIT,
        step=1_000,
        help="Any transaction amount above this value will be flagged and blocked."
    )
    st.caption(f"Current limit: **£{tx_limit:,}**")

    st.divider()

    st.subheader("Age Policy")
    min_age = st.slider(
        "Minimum client age",
        min_value=16,
        max_value=21,
        value=DEFAULT_MIN_AGE,
        step=1,
        help="Clients below this age are blocked as underage."
    )
    st.caption(f"Current minimum: **{min_age} years**")

    st.divider()

    st.subheader("Sanctioned Countries")
    st.caption("Currently blocked countries:")
    for country in SANCTIONED_COUNTRIES:
        st.markdown(f"🚫 {country}")

    st.divider()
    st.caption("AML Screening Dashboard v1.0")
    st.caption("Built with Python · Streamlit · Pandas")

# ─────────────────────────────────────────────
# SCREENING LOGIC  ← pure function, easy to test
# ─────────────────────────────────────────────
def screen_client(row, tx_limit, min_age):
    """
    Apply AML screening rules to a single client row.
    Returns (decision_string, status) where status is 'APPROVED' or 'BLOCKED'.

    Rules applied in priority order:
    1. Sanctioned country
    2. KYC not verified
    3. Underage
    4. Transaction limit exceeded
    5. All checks passed → Approved
    """
    country    = str(row["country"]).strip()
    is_verified = str(row["is_verified"]).strip().lower() in ("true", "1", "yes")
    age        = int(row["age"])
    amount     = float(row["transaction_amount"])

    if country in SANCTIONED_COUNTRIES:
        return f"🚨 BLOCKED: Sanctioned country ({country})", "BLOCKED"
    if not is_verified:
        return "🚨 BLOCKED: KYC not verified", "BLOCKED"
    if age < min_age:
        return f"🚨 BLOCKED: Underage (age {age}, minimum {min_age})", "BLOCKED"
    if amount > tx_limit:
        return f"🚨 BLOCKED: Transaction limit crossed (£{amount:,.0f} > £{tx_limit:,})", "BLOCKED"

    return "✅ APPROVED", "APPROVED"


def run_screening(df, tx_limit, min_age):
    """Run screening across the whole DataFrame. Returns enriched DataFrame."""
    results = df.apply(
        lambda row: pd.Series(screen_client(row, tx_limit, min_age),
                              index=["decision", "status"]),
        axis=1
    )
    return pd.concat([df, results], axis=1)

# ─────────────────────────────────────────────
# VALIDATION  ← the part that makes it look production-aware
# ─────────────────────────────────────────────
def validate_csv(df):
    """
    Validate uploaded CSV against required schema.
    Returns (is_valid, list_of_error_messages).
    """
    errors = []

    # 1. Check all required columns exist
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        errors.append(f"Missing columns: **{', '.join(missing)}**")
        return False, errors   # can't continue without columns

    # 2. Check no completely empty rows
    blank_rows = df[df.isnull().all(axis=1)]
    if not blank_rows.empty:
        errors.append(f"Found {len(blank_rows)} completely empty row(s) — please clean your file.")

    # 3. Check age is numeric
    if not pd.to_numeric(df["age"], errors="coerce").notna().all():
        errors.append("Column **age** contains non-numeric values.")

    # 4. Check transaction_amount is numeric
    if not pd.to_numeric(df["transaction_amount"], errors="coerce").notna().all():
        errors.append("Column **transaction_amount** contains non-numeric values.")

    # 5. Check risk_score is 1–4
    valid_scores = pd.to_numeric(df["risk_score"], errors="coerce")
    if not valid_scores.between(1, 4).all():
        errors.append("Column **risk_score** must contain values between 1 and 4.")

    # 6. Check is_verified has sensible values
    valid_verified = df["is_verified"].astype(str).str.lower().isin(
        ["true", "false", "1", "0", "yes", "no"]
    )
    if not valid_verified.all():
        errors.append("Column **is_verified** must be True/False, Yes/No, or 1/0.")

    # 7. Check no duplicate client names
    dupes = df[df["name"].duplicated(keep=False)]
    if not dupes.empty:
        names = dupes["name"].unique().tolist()
        errors.append(f"Duplicate client name(s) found: **{', '.join(names)}**. Each row must be unique.")

    return len(errors) == 0, errors

# ─────────────────────────────────────────────
# MAIN PAGE HEADER
# ─────────────────────────────────────────────
st.title("🛡️ AML Screening Dashboard")
st.caption(
    "Anti-Money Laundering client screening tool · "
    "Aligned to JMLSG guidance and FCA AML requirements"
)
st.divider()

# ─────────────────────────────────────────────
# FILE UPLOAD SECTION
# ─────────────────────────────────────────────
st.subheader("📂 Upload Client Data")

col_upload, col_info = st.columns([2, 1])

with col_upload:
    uploaded_file = st.file_uploader(
        "Upload a CSV file of clients to screen",
        type=["csv"],
        help="Your CSV must contain: name, age, country, is_verified, transaction_amount, risk_score"
    )

with col_info:
    with st.expander("📋 Required CSV format"):
        st.markdown("Your file must have these columns:")
        for col, desc in REQUIRED_COLUMNS.items():
            st.markdown(f"- `{col}` — {desc}")
        st.download_button(
            label="⬇️ Download sample CSV",
            data="""name,age,country,is_verified,transaction_amount,risk_score\nSam,25,India,True,5000,1\nFu,20,North Korea,False,15000,2\nKun,12,Japan,True,35000,3\nAli Khan,30,Iran,True,60000,4\nJohn Smith,28,United Kingdom,True,25000,2\nMary,17,United Kingdom,True,8000,1\nHassan,35,Iran,True,45000,3\nPriya,28,India,True,75000,4\n""",
            file_name="sample_clients.csv",
            mime="text/csv"
        )

# ─────────────────────────────────────────────
# PROCESS UPLOADED FILE
# ─────────────────────────────────────────────
if uploaded_file is not None:

    # ── Read file ──────────────────────────────
    try:
        df_raw = pd.read_csv(uploaded_file)
    except Exception as e:
        st.error(f"Could not read file: {e}")
        st.stop()

    # ── Validate ───────────────────────────────
    st.subheader("🔍 Validation Check")
    is_valid, errors = validate_csv(df_raw)

    if not is_valid:
        st.error("**Your file failed validation. Please fix the issues below and re-upload.**")
        for err in errors:
            st.markdown(f"- {err}")
        st.stop()   # do not proceed with broken data
    else:
        st.success(
            f"✅ File validated successfully — "
            f"{len(df_raw)} client records loaded, all columns verified."
        )

    st.divider()

    # ── Run screening ──────────────────────────
    df_screened = run_screening(df_raw.copy(), tx_limit, min_age)

    # ── Summary metrics ────────────────────────
    st.subheader("📊 Screening Summary")

    total    = len(df_screened)
    approved = (df_screened["status"] == "APPROVED").sum()
    blocked  = (df_screened["status"] == "BLOCKED").sum()
    block_pct = round((blocked / total) * 100, 1) if total > 0 else 0

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total clients screened", total)
    m2.metric("Approved",  approved, delta=None)
    m3.metric("Blocked",   blocked,  delta=None)
    m4.metric("Block rate", f"{block_pct}%")

    st.divider()

    # ── Results table ──────────────────────────
    st.subheader("📋 Screening Results")

    # Filter controls — full width for reliable interaction
    status_filter = st.selectbox(
        "Filter by status",
        options=["All", "APPROVED", "BLOCKED"]
    )
    search_name = st.text_input("Search by client name", placeholder="Type a name...")

    df_display = df_screened.copy()
    if status_filter != "All":
        df_display = df_display[df_display["status"] == status_filter]
    if search_name:
        df_display = df_display[
            df_display["name"].str.contains(search_name, case=False, na=False)
        ]

    # Colour rows by status
    def colour_status(val):
        if "APPROVED" in str(val):
            return "background-color: #d4edda; color: #155724;"
        elif "BLOCKED" in str(val):
            return "background-color: #f8d7da; color: #721c24;"
        return ""

    styled = df_display[[
        "name", "age", "country", "is_verified",
        "transaction_amount", "risk_score", "decision"
    ]].style.map(colour_status, subset=["decision"])

    st.dataframe(styled, use_container_width=True, hide_index=True)

    st.divider()

    # ── Chart ──────────────────────────────────
    st.subheader("📈 Screening Results Overview")

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        fig_bar = px.bar(
            df_screened["status"].value_counts().reset_index(),
            x="status", y="count",
            color="status",
            color_discrete_map={"APPROVED": "#28a745", "BLOCKED": "#dc3545"},
            labels={"status": "Decision", "count": "Number of clients"},
            title="Approved vs Blocked"
        )
        fig_bar.update_layout(showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)

    with chart_col2:
        # Breakdown of block reasons
        blocked_df = df_screened[df_screened["status"] == "BLOCKED"].copy()
        if not blocked_df.empty:
            # Extract clean reason
            blocked_df["reason"] = blocked_df["decision"].str.replace(
                r"🚨 BLOCKED: ", "", regex=True
            ).str.split("(").str[0].str.strip()
            reason_counts = blocked_df["reason"].value_counts().reset_index()
            reason_counts.columns = ["Reason", "Count"]
            fig_pie = px.pie(
                reason_counts,
                names="Reason",
                values="Count",
                title="Block reasons breakdown",
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No blocked clients — nothing to break down.")

    st.divider()

    # ── Download ───────────────────────────────
    st.subheader("⬇️ Export Results")

    export_df = df_screened[[
        "name", "country", "risk_score", "decision"
    ]].copy()
    # Clean emoji for export
    export_df["decision"] = export_df["decision"].str.replace(
        r"[✅🚨]", "", regex=True
    ).str.strip()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_bytes  = export_df.to_csv(index=False).encode("utf-8")

    dl1, dl2 = st.columns(2)
    with dl1:
        st.download_button(
            label="📥 Download all results as CSV",
            data=csv_bytes,
            file_name=f"aml_screening_results_{timestamp}.csv",
            mime="text/csv"
        )
    with dl2:
        blocked_only = export_df[export_df["decision"].str.contains("BLOCKED")]
        st.download_button(
            label="📥 Download blocked clients only",
            data=blocked_only.to_csv(index=False).encode("utf-8"),
            file_name=f"aml_blocked_clients_{timestamp}.csv",
            mime="text/csv"
        )

else:
    # ── Empty state — shown before any file is uploaded ──
    st.info(
        "👆 Upload a CSV file above to begin screening. "
        "Use the sidebar on the left to configure your compliance thresholds before running."
    )

    st.subheader("How this tool works")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown("**1. Configure**")
        st.caption("Set transaction limits and minimum age in the sidebar")
    with c2:
        st.markdown("**2. Upload**")
        st.caption("Upload your client CSV file — validated automatically")
    with c3:
        st.markdown("**3. Screen**")
        st.caption("Each client is checked against AML rules instantly")
    with c4:
        st.markdown("**4. Export**")
        st.caption("Download full results or blocked clients only as CSV")