def screen_client(name, age, country, is_verified, transaction_amount):
    print("---------------------")
    print("Checking_client:", name)

    if is_verified == False:
        print("BLOCKED: KYC Not Updated")
        return "BLOCKED"
    elif age < 18:
        print("BLOCKED: Client is Underage")
        return "BLOCKED"
    elif country in ["Iran", "North Korea"]:
        print("BLOCKED:Sanctioned Country")
        return "BLOCKED"
    elif transaction_amount >= 50000:
        print("BLOCKED: Transactioned Limit Crossed")
        return "BLOCKED"
    else:
        print("Transaction Aprroved")
        return "APPROVED"

result1 = screen_client("Sam", 25,"India",True,25000)
result2 = screen_client("Rose",30,"Japan",False,45000)
result3 = screen_client("Mike",15,"United States",True,20000)
result4 = screen_client("Amy", 20, "North Korea",True,35000)

print("-------------------------------")
print("Screening Completed")
print("--------------------------------")
print("Sam Decision:", result1)
print("Rose Decision:", result2)
print("Mike Decision:", result3)
print("Amy Decision:", result4)

aprroved = (result1,result2,result3,result4).count("APPROVED")
blocked = (result1,result2,result3,result4).count("BLOCKED")

print("------------------------------")
print("Total Approved:", aprroved)
print("Total Blocked:", blocked)