# Day 5 - CSV + Screening Function
import pandas as pd
# Load clients
clients = pd.read_csv("clients.csv")

print("Total Clients:", len(clients))
print("==============================")

# Screening function
def screen_client(name, age, country, is_verified, transaction_amount):
    print("---------------------")
    print("Checking Client:", name)

    if is_verified == False:
        return "BLOCKED: KYC not verified"
    elif age < 18:
        return "BLOCKED: Underage"
    elif country in ["Iran", "North Korea"]:
        return "BLOCKED: Sanctioned country"
    elif transaction_amount >= 50000:
        return "BLOCKED: Transaction limit crossed"
    else:
        return "APPROVED"

# Loop through CSV and screen each client
results_list = []
approved_count = 0
blocked_count = 0
for index, client in clients.iterrows():
    result = screen_client(
        client["name"],
        client["age"],
        client["country"],
        client["is_verified"],
        client["transaction_amount"]
    )
    print("Decision:", result)

    if result == "APPROVED":
        approved_count += 1
    else:
        blocked_count += 1
    # Add each result to list
    results_list.append({
        "name": client["name"],
        "country": client["country"],
        "risk_score": client["risk_score"],
        "decision": result
    })

# Convert list to DataFrame
results_df = pd.DataFrame(results_list)

# Save to CSV
results_df.to_csv("results.csv", index=False)

print("Total Clients:", len(clients))
print("Total Approved", approved_count)
print("Total Blocked", blocked_count)
print("==============================")
print("✅ Results saved to results.csv!")
print("Screening Completed!")