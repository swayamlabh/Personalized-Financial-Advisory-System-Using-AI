from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import engine
import ml_model
import auth
from chat_api import chat_engine

from ml.data_loading import DataLoader
from ml.preprocessing import DataPreprocessor
from ml.feature_engineering import FeatureEngineer
from ml.ml_pipeline import MLPipeline
from ml.insights import InsightGenerator
import os as _os

import pandas as pd
from fastapi import UploadFile, File

# ---- ML DATASET STATE ----
_BACKEND_DIR = _os.path.dirname(_os.path.abspath(__file__))
# Note: Base dataset is used for pre-training or reference if needed, 
# but organizations now provide their own data.
_BASE_DATASET_PATH = _os.path.join(_BACKEND_DIR, "data", "financial_advisory_dataset.csv")

_GLOBAL_PIPELINE = None

def get_org_analysis(org_name: str):
    # Fetch data from DB
    rows = auth.get_org_data_rows_from_db(org_name)
    if not rows:
        return None

    df = pd.DataFrame(rows)
    df.columns = [c.lower() for c in df.columns]
    
    # Preprocessing
    preprocessor = DataPreprocessor()
    clean_df = preprocessor.clean_data(df)
    
    # Feature Engineering
    engineer = FeatureEngineer()
    enriched_df = engineer.enrich_features(clean_df)
    
    analysis = {}
    analysis["df"] = enriched_df
    analysis["overview"] = engineer.generate_overview(enriched_df)
    analysis["category_insights"] = engineer.generate_category_insights(enriched_df)
    analysis["anomalies"] = engineer.detect_anomalies(enriched_df)
    analysis["trends"] = engineer.generate_trends(enriched_df)
    
    # ML Pipeline Initialization (Global Pre-training)
    global _GLOBAL_PIPELINE
    if '_GLOBAL_PIPELINE' not in globals() or _GLOBAL_PIPELINE is None:
        _GLOBAL_PIPELINE = MLPipeline().train_global()
    
    pipeline = _GLOBAL_PIPELINE
    analysis["pipeline"] = pipeline
    
    # Predictions & Insights using Company Data as input to Global Model
    predictions = pipeline.predict_from_industry(enriched_df)
    analysis["predictions"] = predictions
    
    insight_gen = InsightGenerator()
    analysis["advisory"] = insight_gen.generate_advisory(enriched_df, analysis["overview"], predictions)
    analysis["summary"] = insight_gen.generate_summary_text(analysis["overview"], predictions)
    
    return analysis

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
    login_identifier: str
    password: str
    
class OrgSignupReq(BaseModel):
    orgName: str
    password: str
    country: Optional[str] = None
    bio: Optional[str] = None
    numberOfEmployees: Optional[int] = None
    ceo: Optional[str] = None
    goals: Optional[str] = None

class OrgLoginReq(BaseModel):
    orgName: str
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

class SecurityUpdateReq(BaseModel):
    current_password: str
    new_email: Optional[str] = None
    new_password: Optional[str] = None

# ---- AUTH ROUTES ----
@app.post("/api/signup")
def signup(req: SignupReq):
    res = auth.signup(req.name, req.email, req.password)
    if not res["success"]:
        raise HTTPException(status_code=400, detail=res["error"])
    return res

@app.post("/api/login")
def login(req: LoginReq):
    res = auth.login(req.login_identifier, req.password)
    if not res["success"]:
        raise HTTPException(status_code=400, detail=res["error"])
    return res

@app.post("/api/update_security")
def update_security(req: SecurityUpdateReq, Authorization: Optional[str] = Header(None)):
    if not Authorization:
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    token = Authorization.replace("Bearer ", "")
    user = auth.get_user_from_token(token)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid Session")
        
    res = auth.update_security(
        email=user["email"], 
        current_password=req.current_password, 
        new_email=req.new_email, 
        new_password=req.new_password
    )
    
    if not res["success"]:
        raise HTTPException(status_code=400, detail=res["error"])
        
    return res

@app.post("/api/org_signup")
def org_signup(req: OrgSignupReq):
    res = auth.org_signup(req.orgName, req.password, req.country, req.bio, req.numberOfEmployees, req.ceo, req.goals)
    if not res["success"]:
        raise HTTPException(status_code=400, detail=res["error"])
    return res

@app.post("/api/org_login")
def org_login(req: OrgLoginReq):
    res = auth.org_login(req.orgName, req.password)
    if not res["success"]:
        raise HTTPException(status_code=400, detail=res["error"])
    return res

class OrgManualInput(BaseModel):
    industry: Optional[str] = None
    stage: Optional[str] = None
    goal: Optional[str] = None
    revenue: float
    total_cost: float
    profit: Optional[float] = None
    fixed_cost: Optional[float] = 0
    variable_cost: Optional[float] = 0
    growth_rate: Optional[float] = 0
    health_score: Optional[float] = 0
    date: Optional[str] = None

@app.get("/api/org/dashboard")
def get_org_dashboard(Authorization: Optional[str] = Header(None)):
    if not Authorization:
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    token = Authorization.replace("Bearer ", "")
    user = auth.get_user_from_token(token)
    
    if not user or user.get("type") != "organization":
        raise HTTPException(status_code=401, detail="Unauthorized: Organization access only")
        
    try:
        analysis = get_org_analysis(user["org_name"])
        if not analysis:
            return {"success": True, "data": None, "message": "No data provided yet"}

        return {
            "success": True, 
            "data": {
                "overview": analysis["overview"],
                "category_insights": analysis["category_insights"],
                "anomalies": analysis["anomalies"],
                "trends": analysis["trends"],
                "predictions": analysis["predictions"],
                "advisory": analysis["advisory"],
                "summary": analysis["summary"]
            }
        }
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")

@app.get("/api/org/predictions")
def get_org_predictions(Authorization: Optional[str] = Header(None), industry: Optional[str] = None):
    # Same auth logic
    token = (Authorization or "").replace("Bearer ", "")
    user = auth.get_user_from_token(token)
    if not user or user.get("type") != "organization":
         raise HTTPException(status_code=401, detail="Unauthorized")

    analysis = get_org_analysis(user["org_name"])
    if not analysis:
        return {"success": True, "data": None}

    if industry:
        preds = analysis["pipeline"].predict_from_industry(analysis["df"], industry)
    else:
        preds = analysis["predictions"]
    return {"success": True, "data": preds}

@app.post("/api/org/reset_analysis")
def reset_org_analysis(Authorization: Optional[str] = Header(None)):
    token = (Authorization or "").replace("Bearer ", "")
    user = auth.get_user_from_token(token)
    if not user or user.get("type") != "organization":
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        success = auth.clear_org_data(user["org_name"])
        return {"success": success, "message": "Organization data reset completely."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/org/upload_csv")
async def upload_org_csv(file: UploadFile = File(...), Authorization: Optional[str] = Header(None)):
    token = (Authorization or "").replace("Bearer ", "")
    user = auth.get_user_from_token(token)
    if not user or user.get("type") != "organization":
        raise HTTPException(status_code=401, detail="Unauthorized")

    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files allowed")

    try:
        # Read content and parse
        content = await file.read()
        import io
        df = pd.read_csv(io.BytesIO(content))
        
        # Dynamically detect columns
        df.columns = [str(c).strip().lower().replace(' ', '_') for c in df.columns]
        
        # Map common aliases
        col_mappings = {
            'expenses': 'total_cost',
            'cost': 'total_cost',
            'category': 'industry'
        }
        df.rename(columns=col_mappings, inplace=True)
        
        # Basic validation ensures at least we have math parameters
        if 'revenue' not in df.columns:
            df['revenue'] = 0
        if 'total_cost' not in df.columns:
            df['total_cost'] = 0
            
        rows = df.to_dict(orient='records')
        auth.add_org_data_rows(user["org_name"], rows)
        
        return {"success": True, "message": f"Successfully uploaded {len(rows)} data points"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"CSV Error: {str(e)}")

@app.post("/api/org/input_manual")
def input_manual_data(req: OrgManualInput, Authorization: Optional[str] = Header(None)):
    token = (Authorization or "").replace("Bearer ", "")
    user = auth.get_user_from_token(token)
    if not user or user.get("type") != "organization":
        raise HTTPException(status_code=401, detail="Unauthorized")

    row = req.dict()
    if row.get('profit') is None:
        row['profit'] = row['revenue'] - row['total_cost']
        
    existing = auth.get_org_data_rows_from_db(user["org_name"])
    existing.append(row)
    auth.add_org_data_rows(user["org_name"], existing)
    
    return {"success": True, "message": "Data point added successfully"}

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
