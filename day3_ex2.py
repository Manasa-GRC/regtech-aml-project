# Day3 KYC Verification Check
client_name = "John Smith"
age = 25
is_verified = False
transaction_Amount = 15000

print("Client Name:", client_name)
print("Age:", age)
print("KYC Verified:", is_verified)
print("Transaction Amount:", transaction_Amount)

if is_verified == False:
    print("Blocked: KYC not Completed!")
elif is_verified == True and age < 18:
    print("Blocked: Minor")
else: 
    print("Approved")