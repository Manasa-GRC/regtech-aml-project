def is_eligible(is_verified,age):
    print("--------------------------")

    if is_verified == True and age >= 18:
        return "Eligible"
    else:
        return "Ineligible"
print(is_eligible(True,25))
print(is_eligible(False,20))
print(is_eligible(True,12))