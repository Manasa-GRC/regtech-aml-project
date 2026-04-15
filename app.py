# Day 6 - RegTech Screening Dashboard
# Day 7 - RegTech Screening Dashboard Pro
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="RegTech AML Screening", page_icon="🏦")
st.title("🏦 RegTech AML Screening System")
st.write("Upload your client list to begin screening")

def screen_client(name, age, country, is_verified, transaction_amount):
    if is_verified == False:
        return "🚨 BLOCKED: KYC not verified"
    elif age < 18:
        return "🚨 BLOCKED: Underage"
    elif country in ["Iran", "North Korea"]:
        return "🚨 BLOCKED: Sanctioned country"
    elif transaction_amount >= 50000:
        return "🚨 BLOCKED: Transaction limit crossed"
    else:
        return "✅ APPROVED"

st.sidebar.title("⚙️ Settings")
filter_option = st.sidebar.selectbox(
    "Filter Results:",
    ["All", "Approved Only", "Blocked Only"]
)

uploaded_file = st.file_uploader("Upload Client CSV", type="csv")

if uploaded_file is not None:
    clients = pd.read_csv(uploaded_file)
    st.write("### 📋 Clients Loaded:")
    st.dataframe(clients)

    if st.button("🔍 Screen All Clients"):
        results = []
        for index, client in clients.iterrows():
            result = screen_client(
                client["name"],
                client["age"],
                client["country"],
                client["is_verified"],
                client["transaction_amount"]
            )
            results.append({
                "Name": client["name"],
                "Country": client["country"],
                "Decision": result
            })

        results_df = pd.DataFrame(results)

        if filter_option == "Approved Only":
            display_df = results_df[results_df["Decision"] == "✅ APPROVED"]
        elif filter_option == "Blocked Only":
            display_df = results_df[results_df["Decision"] != "✅ APPROVED"]
        else:
            display_df = results_df

        st.write("### 📊 Screening Results:")
        st.dataframe(display_df)

        approved = len(results_df[results_df["Decision"] == "✅ APPROVED"])
        blocked = len(results_df) - approved

        st.write("### 📈 Summary")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Clients", len(results_df))
        col2.metric("✅ Approved", approved)
        col3.metric("🚨 Blocked", blocked)

        chart_data = pd.DataFrame({
            "Status": ["Approved", "Blocked"],
            "Count": [approved, blocked]
        })
        fig = px.bar(
            chart_data,
            x="Status",
            y="Count",
            color="Status",
            color_discrete_map={
                "Approved": "green",
                "Blocked": "red"
            },
            title="Screening Results Overview"
        )
        st.plotly_chart(fig)

        csv = results_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Results as CSV",
            data=csv,
            file_name="screening_results.csv",
            mime="text/csv"
        )