import pandas as pd
import os

class DataLoader:
    """Loads the financial advisory dataset once and caches it in memory."""
    
    def __init__(self, file_path=None):
        if file_path is None:
            _dir = os.path.dirname(os.path.abspath(__file__))
            file_path = os.path.join(_dir, '..', 'data', 'financial_advisory_dataset.csv')
        self.file_path = os.path.abspath(file_path)
        self._data = None

    def load(self) -> pd.DataFrame:
        if self._data is None:
            if not os.path.exists(self.file_path):
                raise FileNotFoundError(f"Dataset not found at: {self.file_path}")
            self._data = pd.read_csv(self.file_path)
            print(f"[DataLoader] Loaded {len(self._data)} rows from {self.file_path}")
        return self._data.copy()

    def reload(self) -> pd.DataFrame:
        self._data = None
        return self.load()
