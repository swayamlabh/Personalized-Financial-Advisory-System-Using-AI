import re

def parse_indian_amount(amount_str: str, base_income: float = 0.0) -> float:
    if not amount_str:
        return 0.0
    s = str(amount_str).lower().replace(",", "").replace(" ", "")
    if not s:
        return 0.0
    
    # Handle percentage explicitly
    if '%' in s:
        try:
            pct = float(re.findall(r'-?\d+\.?\d*', s)[0])
            return base_income * (pct / 100.0)
        except:
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
    # Parse income first to use as base for expenses if percentage is given
    income = parse_indian_amount(income_str)
    expenses = parse_indian_amount(expenses_str, base_income=income)
    
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

def calculate_emergency_fund(expenses: float, savings: float):
    target = expenses * 6
    months_saved = (savings * 12) / target if target > 0 else 0 # simple metric: current yearly savings vs target
    
    status = "Adequate" if target > 0 and savings > (target/12) else "Needs Attention" # Simplification for demo
    return {
        "target_amount": target,
        "message": f"You should maintain around INR {target:,.0f} in an emergency fund (6 months of expenses).",
        "status": status
    }

def calculate_savings_improvement(expenses: float, income: float):
    # Suggest 10% cut on expenses
    potential_cut = expenses * 0.10
    new_savings = (income - expenses) + potential_cut
    
    return {
        "suggested_cut": potential_cut,
        "new_estimated_savings": new_savings,
        "message": f"By reducing your discretionary expenses by just 10%, you can save an additional INR {potential_cut:,.0f} per month."
    }

def calculate_goal_feasibility(goal_amount_str: str, years: float, savings_per_month: float):
    goal_amount = parse_indian_amount(goal_amount_str)
    if years <= 0:
        return {"feasible": False, "monthly_required": 0, "message": "Invalid timeframe"}
        
    monthly_required = goal_amount / (years * 12)
    feasible = monthly_required <= savings_per_month
    
    alt_years = 0
    if not feasible and savings_per_month > 0:
        alt_years = goal_amount / (savings_per_month * 12)
        
    return {
        "goal_amount": goal_amount,
        "monthly_required": monthly_required,
        "feasible": feasible,
        "alternative_years": round(alt_years, 1) if alt_years > 0 else 0,
        "message": "Goal is perfectly achievable with your current savings." if feasible else f"Shortfall. You need extra INR {monthly_required - savings_per_month:,.0f}/mo. Alternatively, it will take {round(alt_years, 1)} years at your current savings rate."
    }

def generate_investment_comparisons(goal_years: float, monthly_amount: float):
    # Generates a comparison table for frontend
    if monthly_amount <= 0:
        monthly_amount = 5000 # default proxy
        
    term_type = "Medium-term" 
    if goal_years < 3:
        term_type = "Short-term"
    elif goal_years >= 7:
        term_type = "Long-term"
        
    comparisons = [
        {"name": "Mutual Funds (SIP)", "risk": "Moderate/High", "return": "10-14% (Expected)", "suitable": term_type in ["Medium-term", "Long-term"]},
        {"name": "Fixed Deposits (FD)", "risk": "Low", "return": "6-7% (Guaranteed)", "suitable": term_type == "Short-term"},
        {"name": "Recurring Deposits (RD)", "risk": "Low", "return": "5-6.5% (Guaranteed)", "suitable": True},
        {"name": "Public Provident Fund (PPF)", "risk": "Lowest", "return": "7.1% (Tax Free)", "suitable": term_type == "Long-term"}
    ]
    return comparisons

def generate_action_plan(fin, goal, emergency):
    plan = []
    
    # Step 1: Expense Check
    if fin['savings_rate_percent'] < 20:
        plan.append(f"Expense Optimization: Review your spending. Try to cut down discretionary purchases to reach a minimum 20% savings rate (currently {fin['savings_rate_percent']}%).")
    else:
        plan.append(f"Expense Optimization: Excellent! Your savings rate is {fin['savings_rate_percent']}%, which gives you a strong foundation. Keep tracking your expenses.")
        
    # Step 2: Emergency Fund
    plan.append(f"Financial Safety Net: Build an emergency fund of INR {emergency['target_amount']:,.0f} in a liquid asset (like a high-yield savings account) before aggressive investing.")
    
    # Step 3: Investment
    req = goal['monthly_required']
    if req > 0:
        if goal['feasible']:
            plan.append(f"Goal Investment: Automate a monthly SIP of INR {req:,.0f} towards your goal. Ensure you select the right asset class for your timeline.")
        else:
            plan.append(f"Goal Investment: Since you have a monthly shortfall of INR {req - fin['savings']:,.0f}, consider extending your timeline or focus heavily on Step 1 to free up capital.")
    
    return plan

def generate_recommendations(fin, goal, risk_appetite, ml_category, goal_years=0):
    # Returns AI-like explainable text paragraphs instead of generic strings
    recs = []
    
    # 1. Savings AI Analysis
    sv_rate = fin['savings_rate_percent']
    if sv_rate < 20:
        recs.append(f"Based on your profile, you are saving {sv_rate}% of your income. The golden rule of personal finance (50-30-20) suggests pushing this to at least 20%. Consider analyzing your monthly subscriptions and dining out habits to bridge this gap.")
    else:
        recs.append(f"Since you are saving an impressive {sv_rate}% of your income, you have a strong financial base! This gives you leverage to invest in wealth-building assets rather than just preserving capital.")

    # 2. ML Spending AI Analysis
    if ml_category == 'High Spender':
        recs.append("Our ML models classify your spending behavior as a 'High Spender' relative to your income cohort. Implementing a strict budget tracker for your discretionary expenses ('wants') is highly recommended to prevent lifestyle inflation.")
    elif ml_category == 'Balanced User':
        recs.append("Your spending profile is 'Balanced'. You are maintaining a healthy equilibrium between your needs, wants, and savings. Consistency here is key to long-term wealth.")
    elif ml_category == 'High Saver':
        recs.append("You fall into the 'High Saver' category! While this is excellent, ensure your hard-earned cash isn't losing value to inflation in a normal bank account. Put those savings to work.")

    # 3. Investment Strategy
    if goal_years > 0:
        if goal_years >= 5 and risk_appetite.lower() in ['high', 'medium']:
            recs.append(f"Since your goal timeline is {goal_years} years and you have a {risk_appetite} risk appetite, markets are your best option. I strongly recommend starting SIPs in diversified Equity Mutual Funds to easily beat inflation.")
        else:
            recs.append(f"For a shorter-term goal of {goal_years} years, capital preservation is more important than massive returns. Focus on Debt Mutual Funds, Fixed Deposits, or Arbitrage funds.")
            
    return recs
