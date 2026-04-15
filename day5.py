# Day 5 - Reading CSV Data
import pandas as pd

clients = pd.read_csv("clients.csv")
print(clients)


clients = pd.read_csv("clients.csv")

# How many clients?
print("Total Clients:", len(clients))

# See just the names
print(clients["name"])

# See just one client
print(clients.iloc[0])

# See only verified clients
print(clients[clients["is_verified"] == True])