#Day 3 Country Risk Rating
client_name = "John Smith"
age = 25
is_varified = True
country = "Iran"
transaction_amount = 10000
print("Client Name:", client_name)
print("Age: ",age)
print("KYC Verified:", is_varified)
print("Country:",country)
print("Transaction Amount:", transaction_amount)

if country == "Iran"or country == "North Korea"or country == "Syria":
 print("High Risk:Sactioned Country")
elif country == "Nigeria" or country == "Pakistan":
 print("Medium Risk:Enhanced Check required")
else: 
 print("Low Risk:Standard check applied")