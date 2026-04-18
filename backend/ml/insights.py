import pandas as pd
import numpy as np

class InsightGenerator:
    """
    Generates human-readable insights and advisory suggestions based on 
    financial data and model predictions.
    """

    def generate_advisory(self, df: pd.DataFrame, stats: dict, predictions: dict) -> list:
        advisory = []
        if df.empty: return advisory
        latest = df.iloc[-1]
        
        # 1. Health-based advice
        health_score = predictions.get('predicted_health_score', 0)
        risk = predictions.get('predicted_risk_level', 'Medium')
        
        if health_score < 40:
            advisory.append({
                "category": "Urgent", 
                "text": f"CRITICAL: Your health score of {health_score} indicates high operational risk. With a current net loss of ₹{abs(latest['profit']):,.0f}, you must reduce expenses by at least 20% to stabilize runway."
            })
        elif health_score < 70:
            advisory.append({
                "category": "Strategic", 
                "text": f"STABILITY: Your score of {health_score} is stable. To reach the 'Robust' tier (75+), focus on improving your current profit margin of {latest['profit_margin']*100:.1f}% toward a 20%+ benchmark."
            })
        else:
            advisory.append({
                "category": "Growth", 
                "text": f"OPTIMIZED: With a premier health score of {health_score}, your organization is primed for expansion. Consider a 15-20% increase in R&D or Marketing budget to capitalize on your {latest['growth_rate']:.1f}% growth trajectory."
            })

        # 2. Efficiency (CAC/LTV)
        cac = latest.get('cac', 0)
        ltv = latest.get('ltv', 0)
        if cac > 0 and ltv > 0:
            ratio = ltv / cac
            if ratio < 3:
                target_cac = round(ltv / 3, 2)
                advisory.append({
                    "category": "Efficiency", 
                    "text": f"ACQUISITION: Your LTV/CAC ratio is {ratio:.1f}. To achieve industry-standard scalability, you need to reduce per-customer acquisition cost from ₹{cac} to roughly ₹{target_cac}."
                })
            else:
                advisory.append({
                    "category": "Scalability", 
                    "text": f"UNIT ECONOMICS: Your LTV/CAC ratio of {ratio:.1f} is excellent. Every ₹1 invested in acquisition returns ₹{ratio:.1f} in lifetime value. Aggressive marketing spend is highly recommended."
                })

        # 3. Runway
        runway = latest.get('runway_months', 0)
        if runway < 6 and latest['profit'] < 0:
            advisory.append({
                "category": "Urgent",
                "text": f"CASH FLOW: You have only {runway:.1f} months of runway remaining. Immediate capital infusion or a 'default alive' pivot is required within the next 60 days."
            })
            
        return advisory

    def generate_summary_text(self, stats: dict, predictions: dict) -> str:
        health = predictions.get('predicted_health_score', 0)
        risk = predictions.get('predicted_risk_level', 'Unknown')
        growth = predictions.get('avg_growth_rate_pct', 0)
        
        status_map = {
            "EXPANSIVE": "characterized by aggressive fiscal velocity",
            "ROBUST": "maintaining a stabilized capital equilibrium",
            "TRANSITIONAL": "undergoing a strategic operational pivot",
            "VULNERABLE": "facing critical liquidity and margin compression"
        }
        
        tier = "EXPANSIVE" if health > 80 else "ROBUST" if health > 65 else "TRANSITIONAL" if health > 40 else "VULNERABLE"
        status_desc = status_map[tier]
        
        summary = (
            f"The organization is currently {status_desc}, with a proprietary financial health index of {health}/100. "
            f"This composite rating reflects the underlying risk architecture, which is currently tiered as {risk.upper()}. "
            f"Current fiscal performance suggests a high degree of correlation between capital efficiency and top-line velocity. "
        )
        
        if growth > 15:
            summary += f"Extraordinary market capitalization potential is evident with a {growth}% CAGR trajectory. "
        elif growth > 0:
            summary += f"Steady organic expansion of {growth}% demonstrates resilient unit economics. "
        else:
            summary += "The current fiscal mandate should prioritize margin protection and cost-containment as growth enters a cooling phase. "
            
        summary += f"Based on 6-month predictive modeling, we anticipate a stabilization of the cash deployment ratio provided the operational efficiencies identified are strictly adhered to."
            
        return summary
