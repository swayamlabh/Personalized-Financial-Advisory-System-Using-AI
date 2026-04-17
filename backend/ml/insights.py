import pandas as pd
import numpy as np

class InsightGenerator:
    """
    Generates human-readable insights and advisory suggestions based on 
    financial data and model predictions.
    """

    def generate_advisory(self, df: pd.DataFrame, stats: dict, predictions: dict) -> list:
        advisory = []
        
        # 1. Health-based advice
        health_score = predictions.get('predicted_health_score', 0)
        if health_score < 40:
            advisory.append({
                "category": "Urgent",
                "text": "Your financial health score is critical. Prioritize cost reduction and runway extension immediately."
            })
        elif health_score < 70:
            advisory.append({
                "category": "Strategic",
                "text": "Stable health score. Focus on optimizing customer acquisition costs (CAC) to improve long-term LTV/CAC ratio."
            })
        else:
            advisory.append({
                "category": "Growth",
                "text": "Excellent financial health. Consider aggressive expansion or reinvesting profits into R&D."
            })

        # 2. Margin-based advice
        profit_margin = stats.get('avg_profit_margin', 0)
        if profit_margin < 10:
            advisory.append({
                "category": "Operations",
                "text": "Profit margins are lean. Review variable costs and explore pricing strategy adjustments."
            })

        # 3. Growth-based advice
        growth_rate = stats.get('avg_growth_rate', 0)
        if growth_rate < 5:
            advisory.append({
                "category": "Marketing",
                "text": "Growth is stagnant. Analyze market penetration and customer retention strategies."
            })
            
        return advisory

    def generate_summary_text(self, stats: dict, predictions: dict) -> str:
        health = predictions.get('predicted_health_score', 0)
        risk = predictions.get('predicted_risk_level', 'Unknown')
        
        status = "Robust" if health > 75 else "Stable" if health > 50 else "Vulnerable"
        
        summary = (
            f"The organization is currently in a {status} state with a financial health score of {health}/100. "
            f"The risk profile is identified as {risk}. "
        )
        
        if stats.get('avg_growth_rate', 0) > 0:
            summary += f"Positive growth trends are observed at {stats['avg_growth_rate']}%."
        else:
            summary += "Current growth indicators suggest a period of consolidation or contraction."
            
        return summary
