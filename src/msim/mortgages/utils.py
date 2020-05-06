def payment(interest_rate, period_count, principal):
    j = (interest_rate + 1) ** period_count

    return round(principal * ((interest_rate * j) / (j - 1)), 2)
