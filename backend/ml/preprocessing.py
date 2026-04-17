import pandas as pd
import numpy as np

class DataPreprocessor:
    """Cleans and prepares the advisory dataset for feature engineering and ML."""

    NUMERIC_COLS = [
        'revenue', 'fixed_cost', 'variable_cost', 'total_cost', 'profit',
        'cash_reserve', 'debt', 'growth_rate', 'customer_count', 'cac', 'ltv',
        'profit_margin', 'burn_rate', 'runway_months', 'debt_ratio', 'health_score'
    ]
    CATEGORICAL_COLS = ['industry', 'stage', 'goal', 'risk_level', 'recommendation']

    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        print(f"[DEBUG] Preprocessing {len(df)} rows. Columns: {df.columns.tolist()}")
        df = df.copy()
        df.columns = [c.lower() for c in df.columns]

        # Ensure numeric columns are correctly typed
        for col in self.NUMERIC_COLS:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # Fill numeric nulls with median per industry group
        for col in self.NUMERIC_COLS:
            if col in df.columns and df[col].isnull().any():
                if 'industry' in df.columns:
                    df[col] = df.groupby('industry')[col].transform(
                        lambda x: x.fillna(x.median())
                    )
                df[col] = df[col].fillna(df[col].median() if not df[col].empty else 0)

        # Fill categorical nulls
        for col in self.CATEGORICAL_COLS:
            if col in df.columns:
                df[col] = df[col].fillna('Unknown')

        # --- NEW: Sanity Capping for Realistic Modeling ---
        if 'growth_rate' in df.columns:
            # Cap growth between -80% and +150% (realistic bounds)
            df['growth_rate'] = df['growth_rate'].clip(-0.8, 1.5)
        
        if 'profit_margin' in df.columns:
            # Cap margins to prevent absurd LTV/CAC effects
            df['profit_margin'] = df['profit_margin'].clip(-1.0, 0.9)

        # Ensure Revenue and Cost are non-negative
        for col in ['revenue', 'total_cost', 'fixed_cost', 'variable_cost']:
            if col in df.columns:
                df[col] = df[col].apply(lambda x: max(0, x))

        # Handle Data Inconsistency: If cost is 0 but revenue > 10k, flag/fix
        if 'total_cost' in df.columns and 'revenue' in df.columns:
            mask = (df['total_cost'] == 0) & (df['revenue'] > 10000)
            if mask.any():
                # Estimate cost at 50% margin if totally missing but high rev
                df.loc[mask, 'total_cost'] = df.loc[mask, 'revenue'] * 0.5

        # Clip extreme outliers (>= 5 std from mean) for core metrics
        for col in ['revenue', 'total_cost', 'profit']:
            if col in df.columns and len(df) > 5:
                mean, std = df[col].mean(), df[col].std()
                if std > 0:
                    df[col] = df[col].clip(mean - 5*std, mean + 5*std)

        return df
