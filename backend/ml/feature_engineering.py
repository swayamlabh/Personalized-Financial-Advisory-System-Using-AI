import pandas as pd
import numpy as np

class FeatureEngineer:
    """Generates derived features and structured dashboard summaries from cleaned data."""

    def enrich_features(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        # Core derived metrics
        df['expense_ratio']   = (df['total_cost'] / df['revenue'].replace(0, np.nan)).fillna(0)
        df['profit_margin']   = (df['profit'] / df['revenue'].replace(0, np.nan)).fillna(0)
        df['net_burn']        = df['burn_rate'].fillna(0)
        df['ltv_cac_ratio']   = (df['ltv'] / df['cac'].replace(0, np.nan)).fillna(0)

        return df

    def generate_overview(self, df: pd.DataFrame) -> dict:
        latest = df.iloc[-1]
        
        return {
            "total_revenue":     round(float(latest['revenue']), 2),
            "total_expenses":    round(float(latest['total_cost']), 2),
            "total_profit":      round(float(latest['profit']), 2),
            "avg_profit_margin": round(float(latest['profit_margin']) * 100, 2),
            "avg_health_score":  round(float(latest.get('health_score', 0)), 1),
            "avg_growth_rate":   round(float(latest.get('growth_rate', 0)), 2),
            "record_count":      1,
        }

    def generate_category_insights(self, df: pd.DataFrame) -> dict:
        latest = df.iloc[-1]
        
        # Unit Economics
        cac = latest.get('cac', 0)
        ltv = latest.get('ltv', 0)
        ltv_cac = (ltv / cac) if cac > 0 else 0
        
        # Burn & Runway
        revenue = latest.get('revenue', 0)
        total_cost = latest.get('total_cost', 0)
        cash_reserves = latest.get('cash_reserve', 0)
        
        monthly_burn = max(0, total_cost - revenue)
        monthly_surplus = max(0, revenue - total_cost)
        runway = (cash_reserves / monthly_burn) if monthly_burn > 0 else 99 # 99 = infinity/safe
        
        # We'll hijack the 'by_industry' key to send these metrics as a specialized list 
        # to minimize breakage in main.py, but app.js will be updated to render them differently.
        metrics = [
            {"label": "LTV / CAC Ratio", "value": round(ltv_cac, 2), "status": "Good" if ltv_cac >= 3 else "Needs Work"},
            {"label": "Cash Runway", "value": f"{round(runway, 1)} Months", "status": "Secure" if runway > 12 else "Urgent"},
        ]
        
        # Dynamic label for Monthly Burn vs Surplus
        if monthly_surplus > 0:
            metrics.insert(1, {"label": "Monthly Surplus", "value": f"₹{round(monthly_surplus, 2)}", "status": "Profitable"})
        else:
            metrics.insert(1, {"label": "Monthly Burn", "value": f"₹{round(monthly_burn, 2)}", "status": "High" if monthly_burn > revenue * 0.5 else "Low"})

        return {
            "unit_economics": {
                "ltv_cac_ratio": round(ltv_cac, 2),
                "monthly_burn": round(monthly_burn, 2),
                "monthly_surplus": round(monthly_surplus, 2),
                "runway_months": round(runway, 1),
                "efficiency_score": round(min(100, ltv_cac * 20), 1) # simple score based on LTV/CAC
            },
            "metrics": metrics,
            "highest_cost_industry": latest.get('industry', 'N/A'),
            "best_margin_industry": latest.get('industry', 'N/A'),
            "by_industry": [] # Clear old industry grouping to avoid confusion
        }

    def detect_anomalies(self, df: pd.DataFrame) -> list:
        anomalies = []

        # Only check if we have data
        if len(df) == 0:
            return anomalies

        # Check for latest record or aggregated state
        latest = df.iloc[-1]

        # Profit margin worse than -50%
        if latest['profit_margin'] < -0.5:
            anomalies.append({
                "type":        "Critical Loss",
                "description": "The organization's profit margin is currently worse than -50%, indicating a critical financial state.",
                "severity":    "high"
            })

        # Runway < 3 months
        if latest.get('runway_months', 99) < 3:
            anomalies.append({
                "type":        "Cash Crisis Risk",
                "description": "Current cash reserves suggest less than 3 months of runway remaining.",
                "severity":    "high"
            })

        # High debt ratio >0.8
        if latest.get('debt_ratio', 0) > 0.8:
            anomalies.append({
                "type":        "Debt Overload",
                "description": "The organization carries a debt ratio above 80%, which may impact liquidity.",
                "severity":    "medium"
            })

        # Negative growth rate
        if latest['growth_rate'] < 0:
            anomalies.append({
                "type":        "Declining Revenue",
                "description": "Growth rate is currently negative, suggesting a contraction in revenue.",
                "severity":    "medium"
            })

        return anomalies

    def generate_trends(self, df: pd.DataFrame) -> dict:
        """Uses growth_rate to simulate forward-looking trend values per industry."""
        industry_trends = {}
        for industry, grp in df.groupby('industry'):
            avg_rev    = float(grp['revenue'].mean())
            avg_cost   = float(grp['total_cost'].mean())
            avg_growth = float(grp['growth_rate'].mean())

            # Project 6 periods forward (monthly simulation)
            rev_trend  = [round(avg_rev  * ((1 + avg_growth) ** i), 2) for i in range(7)]
            cost_trend = [round(avg_cost * ((1 + avg_growth * 0.9) ** i), 2) for i in range(7)]
            prof_trend = [round(r - c, 2) for r, c in zip(rev_trend, cost_trend)]

            industry_trends[industry] = {
                "avg_growth_rate": round(avg_growth * 100, 2),
                "projected_revenue":  rev_trend,
                "projected_cost":     cost_trend,
                "projected_profit":   prof_trend,
                "labels": ["Now", "M+1", "M+2", "M+3", "M+4", "M+5", "M+6"],
            }
        return industry_trends
