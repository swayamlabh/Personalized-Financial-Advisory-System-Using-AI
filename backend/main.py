from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import engine
import ml_model
import auth
from chat_api import chat_engine

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- AUTHENTICATION MODELS ----
class SignupReq(BaseModel):
    name: str
    email: str
    password: str

class LoginReq(BaseModel):
    email: str
    password: str
    
# ---- FINANCIAL MODELS ----
class ExpenseCategories(BaseModel):
    rent: float = 0
    food: float = 0
    subscriptions: float = 0
    outings: float = 0
    transport: float = 0
    car: float = 0
    children: float = 0
    other: float = 0

class GoalInput(BaseModel):
    name: str
    amount: str
    years: str

class AnalyzeRequest(BaseModel):
    income: str
    expenses: Optional[str] = None          # legacy fallback
    expense_categories: Optional[ExpenseCategories] = None
    risk_appetite: str
    goal_name: Optional[str] = None         # legacy single goal
    goal_amount: Optional[str] = None
    goal_years: Optional[str] = None
    goals: Optional[list] = None            # new: list of GoalInput dicts
    
class ChatReq(BaseModel):
    message: str

# ---- AUTH ROUTES ----
@app.post("/api/signup")
def signup(req: SignupReq):
    res = auth.signup(req.name, req.email, req.password)
    if not res["success"]:
        raise HTTPException(status_code=400, detail=res["error"])
    return res

@app.post("/api/login")
def login(req: LoginReq):
    res = auth.login(req.email, req.password)
    if not res["success"]:
        raise HTTPException(status_code=400, detail=res["error"])
    return res

# ---- API ROUTES ----
@app.post("/api/analyze")
def analyze_financials(req: AnalyzeRequest, Authorization: Optional[str] = Header(None)):
    user = None
    if Authorization:
        token = Authorization.replace("Bearer ", "")
        user = auth.get_user_from_token(token)

    try:
        # --- Resolve total expenses ---
        cat_data = {}
        if req.expense_categories:
            c = req.expense_categories
            cat_data = {
                "House Rent": c.rent,
                "Food & Groceries": c.food,
                "Subscriptions": c.subscriptions,
                "Outings/Entertainment": c.outings,
                "Transportation": c.transport,
                "Car Expenses": c.car,
                "Children": c.children,
                "Other": c.other,
            }
            total_expenses = sum(cat_data.values())
            expenses_str = str(total_expenses)
        else:
            expenses_str = req.expenses or "0"

        # 1. Base Financials
        fin = engine.calculate_financials(req.income, expenses_str)

        # Attach category breakdown to financials for frontend
        fin['expense_categories'] = cat_data

        # 2. ML Category
        category = ml_model.predict_category(fin['income'], fin['expenses'])

        # 3. Emergency Fund
        emergency = engine.calculate_emergency_fund(fin['expenses'], fin['savings'])

        # 4. Savings Improvement
        savings_imp = engine.calculate_savings_improvement(fin['expenses'], fin['income'])

        # 5. Goals — support multiple goals
        goals_input = []
        if req.goals:
            # Normalize: could be dicts or Pydantic objects
            for g in req.goals:
                if isinstance(g, dict):
                    goals_input.append(g)
                else:
                    goals_input.append({'name': g.name, 'amount': g.amount, 'years': g.years})
        elif req.goal_name:
            goals_input = [{'name': req.goal_name, 'amount': req.goal_amount, 'years': req.goal_years}]

        all_goals = []
        primary_goal = None
        for g in goals_input:
            yrs = float(g.get('years', 0)) if g.get('years') else 0
            gd = engine.calculate_goal_feasibility(g.get('amount', '0'), yrs, fin['savings'])
            gd['name'] = g.get('name', 'Goal')
            all_goals.append(gd)
            if primary_goal is None:
                primary_goal = gd

        if not primary_goal:
            primary_goal = {'goal_amount': 0, 'monthly_required': 0, 'message': 'No goal set', 'feasible': True}
            years = 0
        else:
            years = float(goals_input[0].get('years', 0)) if goals_input else 0

        # 6. Action Plan & Recommendations
        action_plan = engine.generate_action_plan(fin, primary_goal, emergency)
        recs = engine.generate_recommendations(fin, primary_goal, req.risk_appetite, category, years)

        # 7. Investment Comparisons
        inv_comparisons = engine.generate_investment_comparisons(years, primary_goal['monthly_required'])

        result_payload = {
            "status": "success",
            "financials": fin,
            "category": category,
            "emergency": emergency,
            "savings_improvement": savings_imp,
            "goal": primary_goal,
            "goals": all_goals,
            "recommendations": recs,
            "action_plan": action_plan,
            "investments": inv_comparisons
        }

        if user:
            chat_engine.update_context(user["email"], result_payload)

        return result_payload

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/chat")
def chat_with_ai(req: ChatReq, Authorization: Optional[str] = Header(None)):
    if not Authorization:
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    token = Authorization.replace("Bearer ", "")
    user = auth.get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid Session")
        
    reply = chat_engine.respond(user["email"], req.message)
    return {"status": "success", "reply": reply}
