# Day 6 - RegTech Screening Dashboard
import streamlit as st
import pandas as pd

st.title("🏦 RegTech AML Screening System")
st.write("Upload your client list to begin screening")

# Screening function
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

# Upload CSV
uploaded_file = st.file_uploader("Upload Client CSV", type="csv")

if uploaded_file is not None:
    clients = pd.read_csv(uploaded_file)
    st.write("### Clients Loaded:")
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
        st.write("### Screening Results:")
        st.dataframe(results_df)

        approved = len(results_df[results_df["Decision"] == "✅ APPROVED"])
        blocked = len(results_df) - approved

        st.write("### Summary")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Clients", len(results_df))
        col2.metric("✅ Approved", approved)
        col3.metric("🚨 Blocked", blocked)