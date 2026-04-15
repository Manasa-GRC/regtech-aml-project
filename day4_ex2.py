#Risk Score

def calculate_risk_score(transaction_amount):
    print("---------------------")
  

    if transaction_amount <= 10000:
       
        return 1
    elif transaction_amount >= 10000 and transaction_amount <= 30000:
        
        return 2
    elif transaction_amount >= 30000 and transaction_amount <= 50000:
       
        return 3
    else:
      
        return 4
print("--------------")
print(calculate_risk_score(5000))   # should print 1
print(calculate_risk_score(15000))  # should print 2
print(calculate_risk_score(35000))  # should print 3
print(calculate_risk_score(60000))