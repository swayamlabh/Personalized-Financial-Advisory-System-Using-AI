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
        df = df.copy()

        # Ensure numeric columns are correctly typed
        for col in self.NUMERIC_COLS:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # Fill numeric nulls with median per industry group
        for col in self.NUMERIC_COLS:
            if col in df.columns and df[col].isnull().any():
                df[col] = df.groupby('industry')[col].transform(
                    lambda x: x.fillna(x.median())
                )
                df[col] = df[col].fillna(df[col].median())

        # Fill categorical nulls
        for col in self.CATEGORICAL_COLS:
            if col in df.columns:
                df[col] = df[col].fillna('Unknown')

        # Clip extreme outliers (>= 5 std from mean) for numeric cols
        for col in ['revenue', 'total_cost', 'profit']:
            if col in df.columns:
                mean, std = df[col].mean(), df[col].std()
                df[col] = df[col].clip(mean - 5*std, mean + 5*std)

        return df
