# Day3 Transaction Risk Scorer
client_name = "John Smith"
age = 25
is_verified = True
transaction_Amount = 50000

print("Client Name:", client_name)
print("Age:", age)
print("KYC Verified:", is_verified)
print("Transaction Amount:", transaction_Amount)

if transaction_Amount > 50000:
    print("critical:immidiate review required!")
elif transaction_Amount >= 20000 and transaction_Amount <= 50000:
    print("High Senior complaince office review")
elif transaction_Amount > 10000 and transaction_Amount < 20000:
    print("Medium: Standard AML Review")
else: 
    print("Auto Approved")