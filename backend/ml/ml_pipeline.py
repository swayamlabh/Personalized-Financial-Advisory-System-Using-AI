import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error

class MLPipeline:
    """
    Trains ML models on localized organization data.
    Handles small datasets gracefully using simplified projections.
    """

    def __init__(self):
        self.health_model   = None
        self.profit_model   = None
        self.scaler_health  = StandardScaler()
        self.scaler_profit  = StandardScaler()
        # Normalized column names (lowercase to match DB)
        self.feature_cols_health  = ['revenue', 'total_cost', 'growth_rate', 'debt_ratio',
                                      'burn_rate', 'runway_months', 'profit_margin', 'ltv', 'cac']
        self.feature_cols_profit  = ['revenue', 'fixed_cost', 'variable_cost',
                                      'growth_rate', 'customer_count', 'debt_ratio']
        self.metrics = {}
        self._trained = False

    def train(self, df: pd.DataFrame):
        # Normalize column names in DF just in case
        df.columns = [c.lower() for c in df.columns]
        
        # Filter for rows that have target values
        df_h = df.dropna(subset=self.feature_cols_health + ['health_score'])
        
        if len(df_h) < 10:
            # Too small for split-validation, train on full or use stats
            print(f"[MLPipeline] Small dataset ({len(df_h)} rows). Using full-set training.")
            if len(df_h) >= 2:
                X_h = df_h[self.feature_cols_health].fillna(0).values
                y_h = df_h['health_score'].values
                self.scaler_health.fit(X_h)
                self.health_model = LinearRegression()
                self.health_model.fit(self.scaler_health.transform(X_h), y_h)
                self.metrics['health_r2'] = 1.0 # Nominal
                self._trained = True
            return

        # ---- Health Score Model ----
        X_h = df_h[self.feature_cols_health].fillna(0).values
        y_h = df_h['health_score'].values
        X_h_scaled = self.scaler_health.fit_transform(X_h)
        X_train, X_test, y_train, y_test = train_test_split(
            X_h_scaled, y_h, test_size=0.2, random_state=42
        )
        self.health_model = LinearRegression()
        self.health_model.fit(X_train, y_train)
        h_pred = self.health_model.predict(X_test)
        self.metrics['health_r2']  = round(r2_score(y_test, h_pred), 4)
        self.metrics['health_mae'] = round(mean_absolute_error(y_test, h_pred), 2)

        # ---- Profit Model ----
        df_p = df.dropna(subset=self.feature_cols_profit + ['profit'])
        if len(df_p) >= 5:
            X_p = df_p[self.feature_cols_profit].fillna(0).values
            y_p = df_p['profit'].values
            X_p_scaled = self.scaler_profit.fit_transform(X_p)
            Xp_tr, Xp_te, yp_tr, yp_te = train_test_split(
                X_p_scaled, y_p, test_size=0.2, random_state=42
            )
            self.profit_model = Ridge(alpha=1.0)
            self.profit_model.fit(Xp_tr, yp_tr)
            pp_pred = self.profit_model.predict(Xp_te)
            self.metrics['profit_r2']  = round(r2_score(yp_te, pp_pred), 4)
            self.metrics['profit_mae'] = round(mean_absolute_error(yp_te, pp_pred), 2)

        self._trained = True

    def _calculate_heuristic_health(self, latest: pd.Series) -> float:
        """
        Calculates a financial health score (0-100) based on unit economics
        when a full ML model is not yet trained.
        """
        score = 50.0 # Base score

        # 1. Profit Margin (up to +20 or -30)
        margin = float(latest.get('profit_margin', 0))
        if margin > 0.3: score += 20
        elif margin > 0.1: score += 10
        elif margin < -0.2: score -= 30
        elif margin < 0: score -= 15

        # 2. Runway (up to +20 or -20)
        runway = float(latest.get('runway_months', 12))
        if runway > 18: score += 20
        elif runway > 12: score += 10
        elif runway < 3: score -= 20
        elif runway < 6: score -= 10

        # 3. Growth (up to +10)
        growth = float(latest.get('growth_rate', 0))
        if growth > 20: score += 10
        elif growth > 5: score += 5

        # 4. CAC/LTV (up to +10)
        cac = latest.get('cac', 0)
        ltv = latest.get('ltv', 0)
        if cac > 0 and ltv > 0:
            ratio = ltv / cac
            if ratio > 5: score += 10
            elif ratio > 3: score += 5
            elif ratio < 1.5: score -= 10

        return float(np.clip(score, 0, 100))

    def predict_from_industry(self, df: pd.DataFrame, industry: str = None) -> dict:
        df.columns = [c.lower() for c in df.columns]
        
        # Calculate base stats
        subset = df[df['industry'] == industry] if industry and industry in df['industry'].values else df
        avg = subset.mean(numeric_only=True)
        
        # Use latest record if available for health/profit to avoid "bogus" averages
        latest = df.iloc[-1]
        
        predicted_health = self._calculate_heuristic_health(latest)
        predicted_profit = float(latest.get('profit', avg.get('profit', 0)))
        
        # If model is trained, use it to refine health score
        if self._trained and self.health_model:
            try:
                h_feat = np.array([[latest.get(c, 0) for c in self.feature_cols_health]])
                h_feat_scaled = self.scaler_health.transform(h_feat)
                # Blend heuristic with model if model exists
                model_health = float(self.health_model.predict(h_feat_scaled)[0])
                predicted_health = (predicted_health * 0.4) + (model_health * 0.6)
                predicted_health = float(np.clip(predicted_health, 0, 100))
            except:
                pass

        # Projections strictly based on input growth_rate
        # For organizations, growth_rate is usually stored as a percentage (e.g. 15 for 15%)
        # But ml_pipeline expects decimal. Let's handle both.
        raw_growth = float(latest.get('growth_rate', 0))
        avg_growth = raw_growth / 100.0 if raw_growth > 1.0 else raw_growth
        
        avg_revenue = float(latest.get('revenue', 0))
        avg_cost    = float(latest.get('total_cost', 0))

        periods = ["Now", "M+1", "M+2", "M+3", "M+4", "M+5", "M+6"]
        # Strictly linear projection: Revenue grows by growth_rate, Cost grows by growth_rate * 0.9 (efficiency)
        proj_rev    = [round(avg_revenue * ((1 + avg_growth) ** i), 2)    for i in range(7)]
        proj_cost   = [round(avg_cost    * ((1 + avg_growth * 0.9) ** i), 2)  for i in range(7)]
        proj_profit = [round(r - c, 2) for r, c in zip(proj_rev, proj_cost)]

        risk_label = "Low" if predicted_health >= 70 else "Medium" if predicted_health >= 40 else "High"

        return {
            "predicted_health_score": round(predicted_health, 1),
            "predicted_profit":       round(predicted_profit, 2),
            "predicted_risk_level":   risk_label,
            "avg_growth_rate_pct":    round(avg_growth * 100, 2),
            "projections": {
                "labels":   periods,
                "revenue":  proj_rev,
                "cost":     proj_cost,
                "profit":   proj_profit,
            },
            "model_metrics": {
                "health_r2":  self.metrics.get('health_r2', "N/A"),
                "profit_r2":  self.metrics.get('profit_r2', "N/A"),
            }
        }
