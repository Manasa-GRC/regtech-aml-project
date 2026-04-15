def calculate_risk_score(transaction_amount):
    if transaction_amount <= 10000:
        return 1
    elif transaction_amount >= 10000 and transaction_amount <= 30000:   
         return 2
    else:
         return 3

def is_eligible(is_verified,age):
    print("--------------------------")

    if is_verified == True and age >= 18:
        return "Eligible"
    else:
        return "Ineligible"
   
def generate_report(name,age,country,is_verified,transaction_amount):
    print("Client Report:", name)    

    eligibility = is_eligible(is_verified, age)
    risk_score = calculate_risk_score(transaction_amount)    

    if country in ["Iran", "North Korea"]:
        country_status = "SANCTIONED"
    else:
        country_status = "CLEAR"
    
    print("Eligibility:", eligibility)
    print("Risk Score:", risk_score)
    print("Country Status:", country_status)

    if eligibility == "Eligible" and country_status == "CLEAR" and risk_score < 4:
        print("Final Decision: APPROVED")
    else:
        print("Final Decision: BLOCKED")
    print("=======================")
          
generate_report("Sam",25,"India",True,5000)
generate_report("Fu",20,"North Korea",False,15000)
generate_report("Kun",12,"Japan",True,35000)