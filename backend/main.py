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
class AnalyzeRequest(BaseModel):
    income: str
    expenses: str
    risk_appetite: str
    goal_name: str
    goal_amount: str
    goal_years: str
    
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
        # 1. Base Financials
        fin = engine.calculate_financials(req.income, req.expenses)
        
        # 2. ML Category
        category = ml_model.predict_category(fin['income'], fin['expenses'])
        
        # 3. Emergency Fund
        emergency = engine.calculate_emergency_fund(fin['expenses'], fin['savings'])
        
        # 4. Savings Improvement
        savings_imp = engine.calculate_savings_improvement(fin['expenses'], fin['income'])
        
        # 5. Goal Feasibility
        years = float(req.goal_years) if req.goal_years else 0
        goal_data = engine.calculate_goal_feasibility(req.goal_amount, years, fin['savings'])
        
        # 6. Action Plan & Recommendations
        action_plan = engine.generate_action_plan(fin, goal_data, emergency)
        recs = engine.generate_recommendations(fin, goal_data, req.risk_appetite, category, years)
        
        # 7. Investment Comparisons
        inv_comparisons = engine.generate_investment_comparisons(years, goal_data['monthly_required'])
        
        result_payload = {
            "status": "success",
            "financials": fin,
            "category": category,
            "emergency": emergency,
            "savings_improvement": savings_imp,
            "goal": goal_data,
            "recommendations": recs,
            "action_plan": action_plan,
            "investments": inv_comparisons
        }
        
        # Save context to Chat Engine if authenticated
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
