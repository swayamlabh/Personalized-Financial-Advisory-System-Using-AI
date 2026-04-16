from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import engine
import ml_model

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalyzeRequest(BaseModel):
    income: str
    expenses: str
    risk_appetite: str
    goal_name: str
    goal_amount: str
    goal_years: str

@app.post("/api/analyze")
def analyze_financials(req: AnalyzeRequest):
    try:
        fin = engine.calculate_financials(req.income, req.expenses)
        category = ml_model.predict_category(fin['income'], fin['expenses'])
        
        years = float(req.goal_years) if req.goal_years else 0
        goal_data = engine.calculate_goal_feasibility(req.goal_amount, years, fin['savings'])
        
        recs = engine.generate_recommendations(fin, goal_data, req.risk_appetite, category, years)
        
        return {
            "status": "success",
            "financials": fin,
            "category": category,
            "goal": goal_data,
            "recommendations": recs
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
