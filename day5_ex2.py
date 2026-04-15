# Risk Clients
import pandas as pd

clients = pd.read_csv("clients.csv")

high_risk = clients[clients["risk_score"] > 2]
print("High Risk Clients:")
print(high_risk)
print("==============================")