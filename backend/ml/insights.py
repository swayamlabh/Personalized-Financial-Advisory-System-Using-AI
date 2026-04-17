import pandas as pd
import numpy as np

class InsightGenerator:
    """
    Generates human-readable insights and advisory suggestions based on 
    financial data and model predictions.
    """

    def generate_advisory(self, df: pd.DataFrame, stats: dict, predictions: dict) -> list:
        advisory = []
        
        health_score = predictions.get('predicted_health_score', 0)
        profit_margin = stats.get('avg_profit_margin', 0)
        growth_rate = stats.get('avg_growth_rate', 0)
        revenue = stats.get('total_revenue', 0)
        expenses = stats.get('total_expenses', 0)

        # 1. Overall Health Analysis
        if health_score < 45:
            advisory.append({
                "category": "Financial Health",
                "status": "Critical",
                "reason": "Health score is below 45 due to high debt-to-equity or consistently negative margins.",
                "action": "Liquidate non-core assets and renegotiate short-term debt immediately."
            })
        elif health_score < 75:
            advisory.append({
                "category": "Financial Health",
                "status": "Warning",
                "reason": "Moderate health score indicates stability but limited cash padding for market volatility.",
                "action": "Increase cash reserves to cover at least 6 months of operating expenses."
            })
        else:
            advisory.append({
                "category": "Financial Health",
                "status": "Good",
                "reason": "Strong balance sheet with healthy margins and sustainable growth metrics.",
                "action": "Maintain current strategy and consider reinvesting surplus into R&D or expansion."
            })

        # 2. Profit & Margin Analysis
        if profit_margin < 0:
            advisory.append({
                "category": "Profitability",
                "status": "Critical",
                "reason": f"Operational loss detected (Margin: {profit_margin}%). Expenses are exceeding revenue.",
                "action": "Conduct a bottom-up cost audit and eliminate underperforming product lines."
            })
        elif profit_margin < 15:
            advisory.append({
                "category": "Profitability",
                "status": "Warning",
                "reason": "Lean margins provide little room for unexpected cost spikes in the supply chain.",
                "action": "Optimize vendor contracts and explore premium pricing tiers to improve unit economics."
            })
        
        # 3. Growth & Scaling Analysis
        if growth_rate > 50:
            advisory.append({
                "category": "Growth",
                "status": "Warning",
                "reason": "Hypergrowth detected. Rapid scaling often leads to operational debt and quality decay.",
                "action": "Standardize internal processes and focus on customer retention to ensure growth is sustainable."
            })
        elif growth_rate < 5:
            advisory.append({
                "category": "Growth",
                "status": "Warning",
                "reason": "Stagnant growth may lead to market share loss against more aggressive competitors.",
                "action": "Refresh marketing strategy and analyze untapped customer segments for expansion."
            })

        return advisory

    def generate_summary_text(self, stats: dict, predictions: dict) -> str:
        health = predictions.get('predicted_health_score', 0)
        risk = predictions.get('predicted_risk_level', 'Unknown')
        margin = stats.get('avg_profit_margin', 0)
        
        status = "Robust" if health > 75 else "Stable" if health > 50 else "Vulnerable"
        
        summary = (
            f"The organization is currently in a {status} state with a financial health score of {health}/100. "
            f"Financial risk is currently rated as '{risk}'. "
        )
        
        if margin < 0:
            summary += "The business is currently operating at a loss, requiring immediate capital injection or cost restructuring."
        elif margin < 10:
            summary += "Profitability is thin; focus on operational efficiency is recommended."
        else:
            summary += "Strong profitability supports long-term sustainability."
            
        return summary
