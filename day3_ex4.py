# ================================
# Client Risk Assessment System
# Built by: Manasa
# Date: 15032026
# Description: AML/KYC compliance
# checker using Python if/else logic
# ================================
# Full client risk profile
client_name = "Ali Khan"
age = 25
country = "India"
is_verified = True
transaction_amount = 40000

print("Client Name:", client_name)
print("Age:", age)
print("Country:", country)
print("KYC Verified:", is_verified)
print("Transaction Amount:", transaction_amount)


    
if is_verified != True:
    print("KYC not verified")
elif age < 18:
    print("Age is below 18")
elif country == "Iran" or country == "North Korea":
    print("Country not allowed")
elif transaction_amount >= 50000:
     print("Limit Crossed")
else:
    print("Fully Cleared Transaction Approved")
    