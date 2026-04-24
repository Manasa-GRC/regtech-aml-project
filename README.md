# 🛡️ AML Screening Dashboard

> **Anti-Money Laundering client screening tool built in Python — aligned to JMLSG guidance and FCA AML requirements.**

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.x-red?logo=streamlit)](https://streamlit.io)
[![Pandas](https://img.shields.io/badge/Pandas-2.x-lightgrey?logo=pandas)](https://pandas.pydata.org)
[![Plotly](https://img.shields.io/badge/Plotly-5.x-3F4F75?logo=plotly)](https://plotly.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## 📌 What This Project Does

Most AML tools give you a binary answer: **blocked** or **approved**.

This dashboard goes further — it assigns every client a **weighted risk score (0–100)** across four regulatory factors, produces a **RAG rating** (Low / Medium / High / Critical), and explains exactly *why* each client scored what they did.

Built to demonstrate how Python can bridge the gap between **technical security controls** and **GRC governance frameworks** in UK financial services.

---

## 🎯 The Problem It Solves

UK banks and fintechs are under increasing regulatory pressure from the **FCA**, **PRA**, and **JMLSG** to demonstrate a *risk-based approach* to Anti-Money Laundering — not just binary pass/fail rules.

Manual spreadsheet-based screening:
- Cannot explain decisions to regulators
- Cannot adapt thresholds without IT involvement
- Has no audit trail
- Cannot score and prioritise risk across a client portfolio

This tool addresses all four.

---

## ✨ Features

### Phase 1 — Core Screening Engine
- 📂 **CSV file uploader** — screen any client dataset, not just hardcoded data
- ✅ **7-point input validation** — catches missing columns, wrong data types, duplicate names, invalid values before processing
- ⚙️ **Configurable thresholds** — transaction limit and minimum age set via sidebar sliders, no code changes needed
- 🎨 **Colour-coded results table** — green for approved, red for blocked, with filter and search
- 📊 **Interactive charts** — approved vs blocked bar chart, block reasons pie chart (Plotly)
- 📥 **Dual CSV export** — download all results or blocked clients only, timestamped

### Phase 2 — Weighted Risk Scoring Model *(JMLSG-aligned)*
- 🧮 **4-factor weighted scoring model** — each client scored 0–100 across Country risk (40%), Transaction risk (30%), KYC status (20%), and Age risk (10%)
- 🟢🟡🔴 **RAG rating system** — Low / Medium / High / Critical thresholds with colour-coded cards
- 📋 **Full risk breakdown table** — every factor score visible per client
- 🔍 **Per-client factor breakdown** — stacked bar chart and plain-English explanation of exactly why any client scored what they did
- 📈 **Scatter chart** — transaction amount vs risk score with RAG threshold lines
- 🌍 **External sanctions config** — sanctioned and FATF high-risk countries loaded from `sanctioned_countries.json`, no code changes needed to update watchlists
- 📚 **JMLSG alignment table** — maps every scoring weight to its regulatory chapter reference

---

## 🏗️ Architecture

```
regtech-aml-project/
│
├── aml_screening_app.py          # Main Streamlit application
├── sanctioned_countries.json     # Watchlist config (UK HMT · OFAC · EU · FATF)
├── clients.csv                   # Sample client dataset
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

**Key design decisions:**

- **Sanctions as config, not code** — `sanctioned_countries.json` separates compliance data from application logic. A compliance officer can update the watchlist without touching Python. This mirrors the architecture of enterprise AML platforms like Actimize and Oracle FCCM.
- **Pure functions for screening logic** — `screen_client()` and `calculate_weighted_risk()` are stateless functions, making them independently testable and easy to extend.
- **Streamlit session state** — screening results persist across tabs so the Risk Matrix tab always reflects the latest uploaded data.
- **Defensive validation** — the app validates before processing and stops cleanly on bad data, rather than crashing mid-run.

---

## 📐 Risk Scoring Model

The weighted scoring model is aligned to **JMLSG Part I, Chapter 4** — the UK Joint Money Laundering Steering Group guidance on risk-based Customer Due Diligence.

| Risk Factor | Weight | JMLSG Reference | Scoring Logic |
|---|---|---|---|
| Country / jurisdiction | **40%** | Ch 4.2 — Geographic risk | Sanctioned = 100, FATF high-risk = 60, other = 0 |
| Transaction amount | **30%** | Ch 4.3 — Transaction risk | Scaled 0–100 against configurable limit |
| KYC / identity verification | **20%** | Ch 4.4 — Customer due diligence | Unverified = 100, Verified = 0 |
| Client age | **10%** | Ch 4.2 — Customer risk | Underage = 100, age 18–25 = 30, 25+ = 0 |

**RAG thresholds:**

| Rating | Score range | Meaning |
|---|---|---|
| 🟢 Low | 0 – 35 | Standard CDD applies |
| 🟡 Medium | 36 – 60 | Enhanced monitoring recommended |
| 🔴 High | 61 – 80 | Enhanced Due Diligence required |
| 🔴 Critical | 81 – 100 | Escalate immediately — likely SAR filing required |

---

## 🌍 Regulatory Alignment

This tool is designed with UK regulatory requirements in mind:

| Requirement | How this tool addresses it |
|---|---|
| **FCA AML sourcebook (SYSC 6.3)** | Risk-based screening with documented decision logic |
| **JMLSG Part I, Chapter 4** | Weighted customer risk assessment across geographic, transaction, CDD and customer factors |
| **MLR 2017 (Reg 28)** | Customer Due Diligence checks: identity verification, sanctions screening, high-risk country flags |
| **DORA (EU/UK alignment)** | Configurable thresholds and external config files support operational resilience — no hard-coded compliance rules |
| **Audit trail principle** | Timestamped CSV exports for every screening run (Phase 3 in development) |

---

## 🚀 Getting Started

### Prerequisites
```
Python 3.8+
```

### Installation

```bash
# Clone the repository
git clone https://github.com/Manasa-GRC/regtech-aml-project.git
cd regtech-aml-project

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run aml_screening_app.py
```

### Dependencies
```
streamlit
pandas
plotly
```

---

## 📋 CSV Format

Your input file must contain these columns:

| Column | Type | Description |
|---|---|---|
| `name` | text | Client full name (must be unique) |
| `age` | integer | Client age |
| `country` | text | Country of residence |
| `is_verified` | boolean | KYC verified? (True/False) |
| `transaction_amount` | float | Transaction amount in £ |
| `risk_score` | integer | Risk score 1–4 |

A sample file (`clients.csv`) is included in this repository.

---

## 🗺️ Roadmap

- [x] **Phase 1** — CSV uploader, validation, configurable thresholds, basic screening
- [x] **Phase 2** — Weighted risk scoring, RAG matrix, JMLSG alignment, external sanctions config
- [ ] **Phase 3** — Audit trail logging, screening history tab, PDF compliance report generator
- [ ] **Phase 4** — Streamlit Cloud deployment, live demo link

---

## 👩‍💻 About the Author

**Manasa Pushparanjan**
Cybersecurity Specialist | 6 years PAM & CyberArk in Banking | Zero Trust Architecture Researcher | GRC & RegTech | ISC2 CC Candidate

This project documents the practical application of cybersecurity and compliance domain knowledge through Python — built as part of an active RegTech learning series.

- 🔗 [LinkedIn](https://www.linkedin.com/in/manasa-pushparanjan)
- 🐙 [GitHub](https://github.com/Manasa-GRC)

---

## 📄 License

This project is licensed under the MIT License.

---

*Built with Python · Streamlit · Pandas · Plotly*  
*Aligned to JMLSG · FCA · MLR 2017 · DORA*
