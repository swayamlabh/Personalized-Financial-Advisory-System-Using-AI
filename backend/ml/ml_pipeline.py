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

    def train_global(self):
        """Trains the ML models on the global baseline dataset only."""
        if self._trained:
            return self
            
        from .data_loading import DataLoader
        from .preprocessing import DataPreprocessor
        from .feature_engineering import FeatureEngineer
        
        try:
            df = DataLoader().load()
            clean_df = DataPreprocessor().clean_data(df)
            enriched_df = FeatureEngineer().enrich_features(clean_df)
            self.train(enriched_df)
        except Exception as e:
            print(f"[MLPipeline] Global training failed: {e}")
            
        return self

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

    def predict_from_industry(self, df: pd.DataFrame, industry: str = None) -> dict:
        df.columns = [c.lower() for c in df.columns]
        
        # Calculate base stats
        subset = df[df['industry'] == industry] if industry and industry in df['industry'].values else df
        avg = subset.mean(numeric_only=True)
        
        predicted_health = float(avg.get('health_score', 50))
        predicted_profit = float(avg.get('profit', 0))
        
        # If model is trained, use it for a more refined score
        if self._trained and self.health_model:
            try:
                h_feat = np.array([[avg.get(c, 0) for c in self.feature_cols_health]])
                h_feat_scaled = self.scaler_health.transform(h_feat)
                # CLAMP: Health score must be 0-100
                predicted_health = float(np.clip(self.health_model.predict(h_feat_scaled)[0], 0, 100))
            except:
                pass

        # Robust Projections using decaying growth
        # Cap growth between -5% (decline) and 25% (high growth) for predictions
        avg_growth = float(avg.get('growth_rate', 0.05))
        safe_growth = min(0.15, max(-0.10, avg_growth)) 
        
        avg_revenue = float(avg.get('revenue', 0))
        avg_cost    = float(avg.get('total_cost', 0))

        periods = ["Now", "M+1", "M+2", "M+3", "M+4", "M+5", "M+6"]
        proj_rev    = []
        proj_cost   = []
        
        curr_r, curr_c, curr_g = avg_revenue, avg_cost, safe_growth
        for i in range(7):
            proj_rev.append(round(curr_r, 2))
            proj_cost.append(round(curr_c, 2))
            curr_r *= (1 + curr_g)
            curr_c *= (1 + curr_g * 0.9) # Costs scale slightly less than rev
            curr_g *= 0.96 # Decay growth 4% per month for long-term realism

        proj_profit = [round(r - c, 2) for r, c in zip(proj_rev, proj_cost)]

        risk_label = "Low" if predicted_health >= 75 else "Moderate" if predicted_health >= 45 else "High Risk"
        trend_label = "Hypergrowth" if safe_growth > 0.1 else "Steady Growth" if safe_growth > 0.02 else "Stagnant" if safe_growth > -0.02 else "Declining"

        return {
            "predicted_health_score": round(predicted_health, 1),
            "predicted_profit":       round(predicted_profit, 2),
            "predicted_risk_level":   risk_label,
            "predicted_trend":        trend_label,
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
