import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os
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
# LOAD SANCTIONS CONFIG  ← from external JSON, not hardcoded
# ─────────────────────────────────────────────
@st.cache_data
def load_sanctions_config():
    """
    Load sanctioned and high-risk countries from config file.
    Using a JSON config means compliance teams can update the list
    without touching the Python code — mirrors real AML platforms.
    """
    config_path = os.path.join(os.path.dirname(__file__), "sanctioned_countries.json")
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
        sanctioned = [c["country"] for c in config["sanctioned_countries"]]
        high_risk  = [c["country"] for c in config["high_risk_countries"]]
        return sanctioned, high_risk, config
    except FileNotFoundError:
        st.warning("sanctioned_countries.json not found — using built-in defaults.")
        sanctioned = ["North Korea", "Iran", "Syria", "Russia",
                      "Belarus", "Cuba", "Myanmar", "Venezuela"]
        high_risk  = ["Afghanistan", "Pakistan", "Nigeria", "South Sudan"]
        return sanctioned, high_risk, {}

SANCTIONED_COUNTRIES, HIGH_RISK_COUNTRIES, SANCTIONS_CONFIG = load_sanctions_config()

# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────
REQUIRED_COLUMNS = {
    "name":               "Client name (text)",
    "age":                "Client age (number)",
    "country":            "Country of residence (text)",
    "is_verified":        "KYC verified? (True/False)",
    "transaction_amount": "Transaction amount in £ (number)",
    "risk_score":         "Risk score 1–4 (number)",
}

DEFAULT_TX_LIMIT = 50_000
DEFAULT_MIN_AGE  = 18

# ─────────────────────────────────────────────
# WEIGHTED RISK SCORING MODEL
# ─────────────────────────────────────────────
# Aligned to JMLSG Part I, Chapter 4 — Risk-based approach to CDD.
# Each factor scored 0-100, then multiplied by its weight.
# Final score = weighted sum, range 0-100.

RISK_WEIGHTS = {
    "country_risk":       0.40,   # 40% — jurisdiction is the #1 AML risk factor
    "transaction_amount": 0.30,   # 30% — large transactions are key ML indicator
    "kyc_status":         0.20,   # 20% — unverified identity is a direct red flag
    "age_risk":           0.10,   # 10% — underage clients carry regulatory risk
}

RAG_THRESHOLDS = {
    "Low":      (0,  35),
    "Medium":   (36, 60),
    "High":     (61, 80),
    "Critical": (81, 100),
}

RAG_COLOURS = {
    "Low":      "#28a745",
    "Medium":   "#fd7e14",
    "High":     "#dc3545",
    "Critical": "#6f0000",
}

RAG_BG = {
    "Low":      "#d4edda",
    "Medium":   "#fff3cd",
    "High":     "#f8d7da",
    "Critical": "#f5c6cb",
}


def calculate_weighted_risk(row, tx_limit, min_age):
    """
    Calculate weighted AML risk score (0-100) for one client.
    Returns a dict of factor scores, weighted total, and RAG rating.
    """
    country     = str(row["country"]).strip()
    is_verified = str(row["is_verified"]).strip().lower() in ("true", "1", "yes")
    age         = int(row["age"])
    amount      = float(row["transaction_amount"])

    # Factor 1: Country risk (JMLSG Ch 4.2)
    if country in SANCTIONED_COUNTRIES:
        country_score = 100
        country_note  = "Sanctioned jurisdiction"
    elif country in HIGH_RISK_COUNTRIES:
        country_score = 60
        country_note  = "FATF high-risk jurisdiction"
    else:
        country_score = 0
        country_note  = "Standard jurisdiction"

    # Factor 2: Transaction amount — scaled against 2x the configured limit
    tx_score = min(100, round((amount / (tx_limit * 2)) * 100))

    # Factor 3: KYC status (JMLSG Ch 4.4)
    kyc_score = 100 if not is_verified else 0

    # Factor 4: Age risk (JMLSG Ch 4.2)
    if age < min_age:
        age_score = 100
    elif age < 25:
        age_score = 30
    else:
        age_score = 0

    weighted_score = round(
        country_score * RISK_WEIGHTS["country_risk"]       +
        tx_score      * RISK_WEIGHTS["transaction_amount"]  +
        kyc_score     * RISK_WEIGHTS["kyc_status"]          +
        age_score     * RISK_WEIGHTS["age_risk"]
    )

    rag = "Low"
    for rating, (low, high) in RAG_THRESHOLDS.items():
        if low <= weighted_score <= high:
            rag = rating
            break

    return {
        "country_score":  country_score,
        "country_note":   country_note,
        "tx_score":       tx_score,
        "kyc_score":      kyc_score,
        "age_score":      age_score,
        "weighted_score": weighted_score,
        "rag_rating":     rag,
    }


# ─────────────────────────────────────────────
# SCREENING LOGIC (binary pass/fail — Phase 1)
# ─────────────────────────────────────────────
def screen_client(row, tx_limit, min_age):
    country     = str(row["country"]).strip()
    is_verified = str(row["is_verified"]).strip().lower() in ("true", "1", "yes")
    age         = int(row["age"])
    amount      = float(row["transaction_amount"])

    if country in SANCTIONED_COUNTRIES:
        return f"BLOCKED: Sanctioned country ({country})", "BLOCKED"
    if not is_verified:
        return "BLOCKED: KYC not verified", "BLOCKED"
    if age < min_age:
        return f"BLOCKED: Underage (age {age}, minimum {min_age})", "BLOCKED"
    if amount > tx_limit:
        return f"BLOCKED: Transaction limit crossed (£{amount:,.0f} > £{tx_limit:,})", "BLOCKED"
    return "APPROVED", "APPROVED"


def run_screening(df, tx_limit, min_age):
    binary = df.apply(
        lambda row: pd.Series(
            screen_client(row, tx_limit, min_age),
            index=["decision", "status"]
        ), axis=1
    )
    risk = df.apply(
        lambda row: pd.Series(calculate_weighted_risk(row, tx_limit, min_age)),
        axis=1
    )
    return pd.concat([df, binary, risk], axis=1)


# ─────────────────────────────────────────────
# VALIDATION
# ─────────────────────────────────────────────
def validate_csv(df):
    errors = []
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        errors.append(f"Missing columns: **{', '.join(missing)}**")
        return False, errors
    if not df[df.isnull().all(axis=1)].empty:
        errors.append("File contains completely empty rows — please clean your data.")
    if not pd.to_numeric(df["age"], errors="coerce").notna().all():
        errors.append("Column **age** contains non-numeric values.")
    if not pd.to_numeric(df["transaction_amount"], errors="coerce").notna().all():
        errors.append("Column **transaction_amount** contains non-numeric values.")
    if not pd.to_numeric(df["risk_score"], errors="coerce").between(1, 4).all():
        errors.append("Column **risk_score** must contain values between 1 and 4.")
    if not df["is_verified"].astype(str).str.lower().isin(
        ["true", "false", "1", "0", "yes", "no"]
    ).all():
        errors.append("Column **is_verified** must be True/False, Yes/No, or 1/0.")
    dupes = df[df["name"].duplicated(keep=False)]
    if not dupes.empty:
        errors.append(f"Duplicate names found: **{', '.join(dupes['name'].unique())}**")
    return len(errors) == 0, errors


# ─────────────────────────────────────────────
# STYLE HELPERS
# ─────────────────────────────────────────────
def style_rag(val):
    c = RAG_COLOURS.get(str(val), "#000")
    b = RAG_BG.get(str(val), "#fff")
    return f"background-color:{b};color:{c};font-weight:500;"

def style_score(val):
    try:
        v = int(val)
        if v >= 81: return "background-color:#f5c6cb;color:#6f0000;font-weight:500;"
        if v >= 61: return "background-color:#f8d7da;color:#721c24;font-weight:500;"
        if v >= 36: return "background-color:#fff3cd;color:#856404;font-weight:500;"
        return             "background-color:#d4edda;color:#155724;font-weight:500;"
    except:
        return ""

def style_decision(val):
    if "APPROVED" in str(val): return "background-color:#d4edda;color:#155724;"
    if "BLOCKED"  in str(val): return "background-color:#f8d7da;color:#721c24;"
    return ""


# ═══════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════
with st.sidebar:
    st.title("Compliance Settings")
    st.caption("Adjust thresholds without changing the code")

    st.subheader("Transaction Limits")
    tx_limit = st.slider(
        "Block transactions above (£)",
        min_value=1_000, max_value=200_000,
        value=DEFAULT_TX_LIMIT, step=1_000,
        help="Transactions above this value are flagged and blocked."
    )
    st.caption(f"Current limit: **£{tx_limit:,}**")
    st.divider()

    st.subheader("Age Policy")
    min_age = st.slider(
        "Minimum client age",
        min_value=16, max_value=21,
        value=DEFAULT_MIN_AGE, step=1,
        help="Clients below this age are blocked."
    )
    st.caption(f"Current minimum: **{min_age} years**")
    st.divider()

    st.subheader("Risk Weight Model")
    st.caption("JMLSG-aligned factor weights:")
    for factor, weight in RISK_WEIGHTS.items():
        st.markdown(f"- **{factor.replace('_',' ').title()}**: {int(weight*100)}%")
    st.divider()

    st.subheader("Watchlists")
    st.caption(f"Source: `sanctioned_countries.json`")
    st.caption(f"{len(SANCTIONED_COUNTRIES)} sanctioned · {len(HIGH_RISK_COUNTRIES)} high-risk")
    with st.expander("View country lists"):
        st.markdown("**Sanctioned:**")
        for c in SANCTIONED_COUNTRIES:
            st.markdown(f"🚫 {c}")
        st.markdown("**High-risk (FATF):**")
        for c in HIGH_RISK_COUNTRIES:
            st.markdown(f"⚠️ {c}")
    st.divider()
    st.caption("AML Screening Dashboard v2.0")
    st.caption("Python · Streamlit · Pandas · Plotly")


# ═══════════════════════════════════════════════
# MAIN — HEADER + TABS
# ═══════════════════════════════════════════════
st.title("🛡️ AML Screening Dashboard")
st.caption(
    "Anti-Money Laundering client screening tool · "
    "Aligned to JMLSG guidance and FCA AML requirements · v2.0"
)
st.divider()

tab_screen, tab_risk, tab_sanctions = st.tabs([
    "📋 Screening",
    "📊 Risk Matrix",
    "🌍 Sanctions Reference",
])


# ──────────────────────────────────────────────
# TAB 1: SCREENING
# ──────────────────────────────────────────────
with tab_screen:
    st.subheader("📂 Upload Client Data")
    col_up, col_info = st.columns([2, 1])

    with col_up:
        uploaded_file = st.file_uploader(
            "Upload a CSV file of clients to screen",
            type=["csv"],
            help="Must contain: name, age, country, is_verified, transaction_amount, risk_score"
        )

    with col_info:
        with st.expander("📋 Required CSV format"):
            st.markdown("Your file must have these columns:")
            for col, desc in REQUIRED_COLUMNS.items():
                st.markdown(f"- `{col}` — {desc}")
            st.download_button(
                label="⬇️ Download sample CSV",
                data=(
                    "name,age,country,is_verified,transaction_amount,risk_score\n"
                    "Sam,25,India,True,5000,1\n"
                    "Fu,20,North Korea,False,15000,2\n"
                    "Kun,12,Japan,True,35000,3\n"
                    "Ali Khan,30,Iran,True,60000,4\n"
                    "John Smith,28,United Kingdom,True,25000,2\n"
                    "Mary,17,United Kingdom,True,8000,1\n"
                    "Hassan,35,Iran,True,45000,3\n"
                    "Priya,28,India,True,75000,4\n"
                ),
                file_name="sample_clients.csv",
                mime="text/csv"
            )

    if uploaded_file is not None:
        try:
            df_raw = pd.read_csv(uploaded_file)
        except Exception as e:
            st.error(f"Could not read file: {e}")
            st.stop()

        st.subheader("🔍 Validation")
        is_valid, val_errors = validate_csv(df_raw)
        if not is_valid:
            st.error("File failed validation — fix issues below and re-upload.")
            for err in val_errors:
                st.markdown(f"- {err}")
            st.stop()
        else:
            st.success(f"✅ {len(df_raw)} client records loaded and validated.")

        st.divider()
        df_screened = run_screening(df_raw.copy(), tx_limit, min_age)
        st.session_state["df_screened"] = df_screened

        # Metrics row
        st.subheader("📊 Screening Summary")
        total     = len(df_screened)
        approved  = (df_screened["status"] == "APPROVED").sum()
        blocked   = (df_screened["status"] == "BLOCKED").sum()
        high_crit = df_screened["rag_rating"].isin(["High", "Critical"]).sum()
        block_pct = round((blocked / total) * 100, 1) if total > 0 else 0

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Total screened",    total)
        m2.metric("Approved",          approved)
        m3.metric("Blocked",           blocked)
        m4.metric("Block rate",        f"{block_pct}%")
        m5.metric("High/Critical risk",high_crit)
        st.divider()

        # Results table
        st.subheader("📋 Screening Results")
        status_filter = st.selectbox(
            "Filter by status", options=["All", "APPROVED", "BLOCKED"]
        )
        search_name = st.text_input(
            "Search by client name", placeholder="Type a name..."
        )

        df_disp = df_screened.copy()
        if status_filter != "All":
            df_disp = df_disp[df_disp["status"] == status_filter]
        if search_name:
            df_disp = df_disp[
                df_disp["name"].str.contains(search_name, case=False, na=False)
            ]

        cols_show = ["name", "age", "country", "transaction_amount",
                     "weighted_score", "rag_rating", "decision"]
        styled = (
            df_disp[cols_show].style
            .map(style_decision, subset=["decision"])
            .map(style_rag,      subset=["rag_rating"])
            .map(style_score,    subset=["weighted_score"])
        )
        st.dataframe(styled, use_container_width=True, hide_index=True)
        st.caption(
            "weighted_score = composite AML risk score (0–100)  |  "
            "rag_rating = Low / Medium / High / Critical"
        )
        st.divider()

        # Charts
        st.subheader("📈 Results Overview")
        c1, c2 = st.columns(2)
        with c1:
            fig_bar = px.bar(
                df_screened["status"].value_counts().reset_index(),
                x="status", y="count", color="status",
                color_discrete_map={"APPROVED": "#28a745", "BLOCKED": "#dc3545"},
                labels={"status": "Decision", "count": "Number of clients"},
                title="Approved vs Blocked"
            )
            fig_bar.update_layout(showlegend=False)
            st.plotly_chart(fig_bar, use_container_width=True)

        with c2:
            blocked_df = df_screened[df_screened["status"] == "BLOCKED"].copy()
            if not blocked_df.empty:
                blocked_df["reason"] = (
                    blocked_df["decision"]
                    .str.replace("BLOCKED: ", "", regex=False)
                    .str.split("(").str[0].str.strip()
                )
                rc = blocked_df["reason"].value_counts().reset_index()
                rc.columns = ["Reason", "Count"]
                fig_pie = px.pie(
                    rc, names="Reason", values="Count",
                    title="Block reasons breakdown",
                    color_discrete_sequence=px.colors.qualitative.Set2
                )
                st.plotly_chart(fig_pie, use_container_width=True)
        st.divider()

        # Export
        st.subheader("⬇️ Export Results")
        export_df = df_screened[
            ["name", "country", "weighted_score", "rag_rating", "decision"]
        ].copy()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dl1, dl2 = st.columns(2)
        with dl1:
            st.download_button(
                "📥 Download all results",
                data=export_df.to_csv(index=False).encode("utf-8"),
                file_name=f"aml_results_{timestamp}.csv",
                mime="text/csv"
            )
        with dl2:
            blocked_only = export_df[export_df["decision"].str.contains("BLOCKED")]
            st.download_button(
                "📥 Download blocked clients only",
                data=blocked_only.to_csv(index=False).encode("utf-8"),
                file_name=f"aml_blocked_{timestamp}.csv",
                mime="text/csv"
            )

    else:
        st.info("👆 Upload a CSV file to begin screening.")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown("**1. Configure**")
            st.caption("Set limits in the sidebar")
        with c2:
            st.markdown("**2. Upload**")
            st.caption("Upload your client CSV")
        with c3:
            st.markdown("**3. Screen**")
            st.caption("Clients scored by weighted AML model")
        with c4:
            st.markdown("**4. Export**")
            st.caption("Download results as CSV")


# ──────────────────────────────────────────────
# TAB 2: RISK MATRIX
# ──────────────────────────────────────────────
with tab_risk:
    st.subheader("📊 Weighted Risk Score Matrix")
    st.caption(
        "4-factor weighted model aligned to JMLSG Part I, Chapter 4. "
        "Scores run 0–100. RAG thresholds: Low 0–35 · Medium 36–60 · High 61–80 · Critical 81–100."
    )

    if "df_screened" not in st.session_state:
        st.info("Upload and screen a CSV on the Screening tab first.")
    else:
        df = st.session_state["df_screened"].copy()

        # RAG summary cards
        st.subheader("RAG Rating Summary")
        rag_counts = df["rag_rating"].value_counts()
        r1, r2, r3, r4 = st.columns(4)
        for col, rating in zip([r1, r2, r3, r4], ["Low", "Medium", "High", "Critical"]):
            count = int(rag_counts.get(rating, 0))
            col.markdown(
                f"<div style='background:{RAG_BG[rating]};padding:16px;"
                f"border-radius:8px;text-align:center;'>"
                f"<div style='font-size:11px;color:{RAG_COLOURS[rating]};"
                f"font-weight:500;text-transform:uppercase;letter-spacing:0.05em;'>{rating}</div>"
                f"<div style='font-size:28px;font-weight:500;color:{RAG_COLOURS[rating]};'>{count}</div>"
                f"<div style='font-size:11px;color:{RAG_COLOURS[rating]};'>client(s)</div>"
                f"</div>",
                unsafe_allow_html=True
            )
        st.divider()

        # Full breakdown table
        st.subheader("Full Risk Score Breakdown")
        st.caption(
            "Each factor scored 0–100 before weighting. "
            "Total = Country×40% + Transaction×30% + KYC×20% + Age×10%"
        )
        risk_table = df[[
            "name", "country", "country_score", "tx_score",
            "kyc_score", "age_score", "weighted_score", "rag_rating"
        ]].rename(columns={
            "name":           "Client",
            "country":        "Country",
            "country_score":  "Country risk (40%)",
            "tx_score":       "Transaction risk (30%)",
            "kyc_score":      "KYC risk (20%)",
            "age_score":      "Age risk (10%)",
            "weighted_score": "Total score",
            "rag_rating":     "RAG rating",
        })
        score_cols = [
            "Country risk (40%)", "Transaction risk (30%)",
            "KYC risk (20%)", "Age risk (10%)", "Total score"
        ]
        styled_risk = (
            risk_table.style
            .map(style_rag,   subset=["RAG rating"])
            .map(style_score, subset=score_cols)
        )
        st.dataframe(styled_risk, use_container_width=True, hide_index=True)
        st.divider()

        # Charts
        st.subheader("Risk Visualisations")
        ch1, ch2 = st.columns(2)

        with ch1:
            rag_order = ["Low", "Medium", "High", "Critical"]
            rag_df    = (
                df["rag_rating"]
                .value_counts()
                .reindex(rag_order, fill_value=0)
                .reset_index()
            )
            rag_df.columns = ["Rating", "Count"]
            fig_rag = px.bar(
                rag_df, x="Rating", y="Count", color="Rating",
                color_discrete_map=RAG_COLOURS,
                title="Clients by RAG rating",
                labels={"Count": "Number of clients"}
            )
            fig_rag.update_layout(showlegend=False)
            st.plotly_chart(fig_rag, use_container_width=True)

        with ch2:
            fig_sc = px.scatter(
                df, x="transaction_amount", y="weighted_score",
                color="rag_rating", hover_name="name",
                color_discrete_map=RAG_COLOURS,
                title="Transaction amount vs Risk score",
                labels={
                    "transaction_amount": "Transaction (£)",
                    "weighted_score":     "Risk score",
                    "rag_rating":         "RAG"
                }
            )
            fig_sc.add_hline(
                y=36, line_dash="dot", line_color="orange",
                annotation_text="Medium threshold"
            )
            fig_sc.add_hline(
                y=61, line_dash="dot", line_color="red",
                annotation_text="High threshold"
            )
            st.plotly_chart(fig_sc, use_container_width=True)

        st.divider()

        # Per-client factor breakdown
        st.subheader("Per-client Factor Breakdown")
        st.caption(
            "Select any client to see exactly how their score was calculated. "
            "Helps compliance officers explain decisions clearly."
        )
        selected = st.selectbox("Select a client", options=df["name"].tolist())
        row = df[df["name"] == selected].iloc[0]

        contributions = {
            "Country risk":     round(row["country_score"] * RISK_WEIGHTS["country_risk"],       1),
            "Transaction risk": round(row["tx_score"]      * RISK_WEIGHTS["transaction_amount"], 1),
            "KYC risk":         round(row["kyc_score"]     * RISK_WEIGHTS["kyc_status"],         1),
            "Age risk":         round(row["age_score"]     * RISK_WEIGHTS["age_risk"],           1),
        }

        inf1, inf2, inf3 = st.columns(3)
        inf1.metric("Client",      selected)
        inf2.metric("Total score", f"{row['weighted_score']} / 100")
        rag = row["rag_rating"]
        inf3.markdown(
            f"<div style='background:{RAG_BG[rag]};padding:12px;border-radius:8px;"
            f"text-align:center;margin-top:4px;'>"
            f"<div style='font-size:11px;color:{RAG_COLOURS[rag]};font-weight:500;'>RAG RATING</div>"
            f"<div style='font-size:22px;font-weight:500;color:{RAG_COLOURS[rag]};'>{rag}</div>"
            f"</div>",
            unsafe_allow_html=True
        )

        colours_list = ["#185FA5", "#fd7e14", "#dc3545", "#6f0000"]
        raw_scores   = [row["country_score"], row["tx_score"],
                        row["kyc_score"],      row["age_score"]]
        fig_bar2 = go.Figure()
        for (factor, contrib), colour, raw in zip(
            contributions.items(), colours_list, raw_scores
        ):
            fig_bar2.add_trace(go.Bar(
                name=f"{factor} (raw: {raw})",
                x=[contrib], y=["Score"],
                orientation="h",
                marker_color=colour,
                text=f"{factor}: {contrib} pts",
                textposition="inside",
            ))
        fig_bar2.update_layout(
            barmode="stack",
            title=f"{selected} — total score: {row['weighted_score']}/100",
            xaxis=dict(range=[0, 100], title="Points contributed"),
            height=200,
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.1)
        )
        st.plotly_chart(fig_bar2, use_container_width=True)

        st.markdown(f"""
**Why {selected} scored {row['weighted_score']}/100:**
- **Country risk** — {row['country_note']} → raw score {row['country_score']}/100 → **{contributions['Country risk']} points** (40% weight)
- **Transaction risk** — £{row['transaction_amount']:,.0f} vs £{tx_limit:,} limit → raw score {row['tx_score']}/100 → **{contributions['Transaction risk']} points** (30% weight)
- **KYC risk** — {'Not verified' if row['kyc_score'] == 100 else 'Verified'} → raw score {row['kyc_score']}/100 → **{contributions['KYC risk']} points** (20% weight)
- **Age risk** — Age {row['age']} → raw score {row['age_score']}/100 → **{contributions['Age risk']} points** (10% weight)
""")


# ──────────────────────────────────────────────
# TAB 3: SANCTIONS REFERENCE
# ──────────────────────────────────────────────
with tab_sanctions:
    st.subheader("🌍 Sanctions & Watchlist Reference")
    st.caption(
        "Loaded from `sanctioned_countries.json`. "
        "Update the file to refresh the lists without changing any Python code — "
        "this mirrors how real AML watchlist platforms (Refinitiv, Dow Jones) work."
    )

    if SANCTIONS_CONFIG:
        meta = SANCTIONS_CONFIG.get("metadata", {})
        st.info(
            f"**Version:** {meta.get('version', '—')}  |  "
            f"**Last updated:** {meta.get('last_updated', '—')}  |  "
            f"**Sources:** {', '.join(meta.get('sources', []))}"
        )

    st.divider()
    sc1, sc2 = st.columns(2)

    with sc1:
        st.markdown("#### 🚫 Sanctioned countries")
        st.caption("Clients from these countries are automatically BLOCKED")
        if SANCTIONS_CONFIG:
            s_data = SANCTIONS_CONFIG.get("sanctioned_countries", [])
            if s_data:
                st.dataframe(
                    pd.DataFrame(s_data),
                    use_container_width=True, hide_index=True
                )

    with sc2:
        st.markdown("#### ⚠️ High-risk countries (FATF)")
        st.caption("Clients from these countries receive elevated risk scores (+60 country score)")
        if SANCTIONS_CONFIG:
            h_data = SANCTIONS_CONFIG.get("high_risk_countries", [])
            if h_data:
                st.dataframe(
                    pd.DataFrame(h_data),
                    use_container_width=True, hide_index=True
                )

    st.divider()
    st.subheader("📐 Risk Weight Model — JMLSG Alignment")
    st.caption(
        "Weights aligned to JMLSG Part I, Chapter 4 "
        "(Risk-based approach to Customer Due Diligence)."
    )
    weight_data = pd.DataFrame({
        "Risk factor":     ["Country / jurisdiction", "Transaction amount",
                            "KYC / identity verification", "Client age"],
        "Weight":          ["40%", "30%", "20%", "10%"],
        "JMLSG reference": ["Ch 4.2 — Geographic risk", "Ch 4.3 — Transaction risk",
                            "Ch 4.4 — Customer due diligence", "Ch 4.2 — Customer risk"],
        "Scoring logic":   ["Sanctioned=100, FATF high-risk=60, other=0",
                            "Scaled 0–100 against configurable limit",
                            "Unverified=100, Verified=0",
                            "Underage=100, age 18–25=30, 25+=0"],
    })
    st.dataframe(weight_data, use_container_width=True, hide_index=True)