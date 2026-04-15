# Day 2 - Learned variables, data types,
# if/else logic and transaction flagging
#Register Client Information
client_name = "John Smith"
client_age = 25
country = "United Kingdom"
is_verified = True
transaction_amount = 5000
print("Client Name:", client_name)
print("Client Age:", client_age)
print("KYC Verified:", is_verified)
print("Transaction Amount:", transaction_amount)
#Decision Making
if transaction_amount > 10000:
    print("SUSPICIOUS: Large Amount Flagged!")
else:
    print("Normal Transaction: Within Limits")