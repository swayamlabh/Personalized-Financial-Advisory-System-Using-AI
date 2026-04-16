import re

def parse_indian_amount(amount_str: str) -> float:
    if not amount_str:
        return 0.0
    s = str(amount_str).lower().replace(",", "").replace(" ", "")
    if not s:
        return 0.0
    
    multiplier = 1.0
    if 'lakh' in s or 'lac' in s or 'l' in s:
        multiplier = 100000.0
        s = re.sub(r'lakh|lac|l', '', s)
    elif 'crore' in s or 'cr' in s:
        multiplier = 10000000.0
        s = re.sub(r'crore|cr', '', s)
    elif 'k' in s or 'thousand' in s:
        multiplier = 1000.0
        s = re.sub(r'k|thousand', '', s)
        
    try:
        num = float(re.findall(r'-?\d+\.?\d*', s)[0])
        return num * multiplier
    except IndexError:
        return 0.0

def calculate_financials(income_str: str, expenses_str: str):
    income = parse_indian_amount(income_str)
    expenses = parse_indian_amount(expenses_str)
    
    savings = income - expenses
    savings_rate = (savings / income * 100) if income > 0 else 0
    
    needs = income * 0.50
    wants = income * 0.30
    ideal_savings = income * 0.20
    
    health = "Good"
    if savings_rate < 10:
        health = "Critical (High Overspending)"
    elif savings_rate < 20:
        health = "Needs Improvement"
        
    return {
        "income": income,
        "expenses": expenses,
        "savings": savings,
        "savings_rate_percent": round(savings_rate, 2),
        "rule_50_30_20": {
            "needs": needs,
            "wants": wants,
            "targets_savings": ideal_savings
        },
        "health": health
    }

def calculate_goal_feasibility(goal_amount_str: str, years: float, savings_per_month: float):
    goal_amount = parse_indian_amount(goal_amount_str)
    if years <= 0:
        return {"feasible": False, "monthly_required": 0, "message": "Invalid timeframe"}
        
    monthly_required = goal_amount / (years * 12)
    feasible = monthly_required <= savings_per_month
    
    return {
        "goal_amount": goal_amount,
        "monthly_required": monthly_required,
        "feasible": feasible,
        "message": "Goal is achievable with current savings." if feasible else f"Shortfall. You need extra INR {monthly_required - savings_per_month:,.2f}/mo."
    }

def generate_recommendations(fin, goal, risk_appetite, ml_category, goal_years=0):
    recs = []
    
    if fin['savings_rate_percent'] < 20:
        recs.append("Reduce discretionary spending to hit the 20% savings target.")
    if fin['expenses'] > (fin['rule_50_30_20']['needs'] + fin['rule_50_30_20']['wants']):
        recs.append("You are overspending compared to the 50/30/20 rule. Review your 'wants'.")
        
    if ml_category == 'High Spender':
        recs.append("Your spending profile is 'High Spender'. Track your daily expenses closely.")
    elif ml_category == 'Balanced User':
        recs.append("You maintain a 'Balanced' profile. Keep up the consistent habits!")
    elif ml_category == 'High Saver':
        recs.append("Great job! You're a 'High Saver'. Ensure your cash is invested, not idle.")

    # Goal specific and shortfall suggestions
    if goal['monthly_required'] > 0:
        if goal['feasible']:
            recs.append(f"To achieve your goal, start a SIP/Investment of INR {goal['monthly_required']:,.0f}/month.")
        else:
            shortfall = goal['monthly_required'] - fin['savings']
            recs.append(f"Goal Shortfall: You need an extra INR {shortfall:,.0f}/month to reach your goal on time.")
            recs.append(f"To improve savings: Try adhering strictly to the 50/30/20 rule, cutting down on the 'wants' category, or looking into passive income streams.")
            
        # Target based investment advice
        if goal_years < 3:
            recs.append(f"For a short-term goal ({goal_years} years), preserve capital by investing your savings in Liquid Funds, Arbitrage Funds, or High-Yield FDs.")
        elif goal_years < 7:
            if risk_appetite.lower() == 'high':
                recs.append(f"For a medium-term goal ({goal_years} years) with high risk appetite, consider Flexi-cap Mutual Funds or Index Funds.")
            else:
                recs.append(f"For a medium-term goal ({goal_years} years), consider Balanced Advantage Funds or Corporate Bond Funds.")
        else:
            if risk_appetite.lower() == 'low':
                recs.append(f"For a long-term goal ({goal_years} years), consider PPF (Public Provident Fund) or Debt Mutual Funds to build steady wealth.")
            else:
                recs.append(f"For a long-term goal ({goal_years} years), equity is your best friend. Start SIPs in Mid-Cap or Small-Cap Mutual Funds to easily beat inflation.")
    else:
        # Generic risk-based advice if no goal is set or timeframe is 0
        if risk_appetite.lower() == 'high':
            recs.append("General Investment: With a High risk appetite, consider Equity Mutual Funds, Direct Stocks, or smallcases.")
        elif risk_appetite.lower() == 'medium':
            recs.append("General Investment: For Medium risk, Balanced Advantage Funds, Index Funds, or Corporate Bonds are recommended.")
        else:
            recs.append("General Investment: For Low risk, consider Fixed Deposits, Recurring Deposits, or Debt Mutual Funds.")
    return recs
