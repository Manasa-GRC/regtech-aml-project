#List, Loop and Risk

clients = [
    {"name": "Ali Khan", "age": 25, "country": "India", "is_verified": True, "transaction_amount": 40000},
    {"name": "John", "age": 20, "country": "UK", "is_verified": True, "transaction_amount":65000},
    {"name": "Sam", "age":22, "country": "Saudi", "is_verified":False, "transaction_amount":40000},
    {"name": "Ved", "age": 15, "country": "China", "is_verified": True, "transaction_amount":28000},
]

print("Total clients to screen:", len(clients))

for client in clients:
    
    print("-----------")
    print("Checking client:", client["name"])

    

    if client ["is_verified"] == False:
        print("Blocked: KYC not verified")
    elif client ["age"] < 18:
        print("Blocked: Client is Minor")
    elif client ["country"] in ["Iran", "North Korea"]:
        print("Blocked: Sanction Country")
    elif client ["transaction_amount"] >= 50000:
        print("Blocked: Transaction Limit Crossed")
    else:
        print("Transaction Approved")

print("===========")
print("Screening Completed")