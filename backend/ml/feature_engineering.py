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
        total_rev  = float(df['revenue'].sum())
        total_cost = float(df['total_cost'].sum())
        total_prof = float(df['profit'].sum())
        avg_margin = float(df['profit_margin'].mean())
        avg_health = float(df['health_score'].mean())
        avg_growth = float(df['growth_rate'].mean())

        return {
            "total_revenue":     round(total_rev,  2),
            "total_expenses":    round(total_cost, 2),
            "total_profit":      round(total_prof, 2),
            "avg_profit_margin": round(avg_margin * 100, 2),
            "avg_health_score":  round(avg_health, 1),
            "avg_growth_rate":   round(avg_growth * 100, 2),
            "record_count":      len(df),
        }

    def generate_category_insights(self, df: pd.DataFrame) -> dict:
        # By industry
        by_industry = df.groupby('industry').agg(
            total_revenue=('revenue',   'sum'),
            total_cost=   ('total_cost','sum'),
            total_profit= ('profit',    'sum'),
            avg_margin=   ('profit_margin','mean'),
            avg_health=   ('health_score','mean'),
            count=        ('revenue',   'count'),
        ).reset_index()
        by_industry['avg_margin'] = (by_industry['avg_margin'] * 100).round(2)
        by_industry['avg_health'] = by_industry['avg_health'].round(1)
        industry_list = by_industry.to_dict(orient='records')

        # By stage
        by_stage = df.groupby('stage').agg(
            avg_revenue= ('revenue',       'mean'),
            avg_profit=  ('profit',        'mean'),
            avg_health=  ('health_score',  'mean'),
            count=       ('revenue',       'count'),
        ).reset_index()
        stage_list = by_stage.round(2).to_dict(orient='records')

        # By risk level
        risk_dist = df['risk_level'].value_counts().to_dict()

        # Highest cost industry
        top_cost_row = by_industry.loc[by_industry['total_cost'].idxmax()]

        # Best margin industry
        best_margin_row = by_industry.loc[by_industry['avg_margin'].idxmax()]

        return {
            "by_industry":           industry_list,
            "by_stage":              stage_list,
            "risk_distribution":     risk_dist,
            "highest_cost_industry": top_cost_row['industry'],
            "best_margin_industry":  best_margin_row['industry'],
        }

    def detect_anomalies(self, df: pd.DataFrame) -> list:
        anomalies = []

        # Companies with negative profit margin worse than -50%
        bad_margin = df[df['profit_margin'] < -0.5]
        if len(bad_margin) > 0:
            anomalies.append({
                "type":        "Critical Loss",
                "description": f"{len(bad_margin)} companies ({len(bad_margin)/len(df)*100:.1f}%) have profit margin worse than -50%.",
                "severity":    "high"
            })

        # Companies with runway < 3 months
        low_runway = df[df['runway_months'] < 3]
        if len(low_runway) > 0:
            anomalies.append({
                "type":        "Cash Crisis Risk",
                "description": f"{len(low_runway)} companies have less than 3 months of runway remaining.",
                "severity":    "high"
            })

        # High debt ratio >0.8
        high_debt = df[df['debt_ratio'] > 0.8]
        if len(high_debt) > 0:
            anomalies.append({
                "type":        "Debt Overload",
                "description": f"{len(high_debt)} companies carry a debt ratio above 80%.",
                "severity":    "medium"
            })

        # Negative growth rate
        neg_growth = df[df['growth_rate'] < 0]
        if len(neg_growth) > 0:
            anomalies.append({
                "type":        "Declining Revenue",
                "description": f"{len(neg_growth)} companies are reporting negative growth rates.",
                "severity":    "medium"
            })

        return anomalies

    def generate_trends(self, df: pd.DataFrame) -> dict:
        """
        Uses a Decaying Growth model for realistic forward-looking projections.
        Growth naturally slows down over time (5% decay per period).
        """
        industry_trends = {}
        for industry, grp in df.groupby('industry'):
            # Use the mean of the latest records for a stable baseline
            last_records = grp.tail(max(1, len(grp)//2))
            avg_rev    = float(last_records['revenue'].mean())
            avg_cost   = float(last_records['total_cost'].mean())
            avg_growth = float(last_records['growth_rate'].mean())
            
            # Capping growth rate for projections to a realistic peak (15% per period)
            peak_growth = min(0.15, max(-0.15, avg_growth))

            rev_trend = []
            cost_trend = []
            curr_rev = avg_rev
            curr_cost = avg_cost
            curr_growth = peak_growth

            # Project 6 periods forward
            for i in range(7):
                rev_trend.append(round(curr_rev, 2))
                cost_trend.append(round(curr_cost, 2))
                
                # Apply growth and then decay the growth rate for next period 
                curr_rev *= (1 + curr_growth)
                curr_cost *= (1 + curr_growth * 0.85) # Costs grow at ~85% of revenue rate
                curr_growth *= 0.95 # Growth decay: 5% lower each month

            prof_trend = [round(r - c, 2) for r, c in zip(rev_trend, cost_trend)]

            industry_trends[industry] = {
                "avg_growth_rate": round(avg_growth * 100, 2),
                "projected_revenue":  rev_trend,
                "projected_cost":     cost_trend,
                "projected_profit":   prof_trend,
                "labels": ["Now", "M+1", "M+2", "M+3", "M+4", "M+5", "M+6"],
            }
        return industry_trends
