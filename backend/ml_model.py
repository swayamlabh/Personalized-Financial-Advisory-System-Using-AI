import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
import joblib
import os

MODEL_PATH = os.path.join(os.path.dirname(__file__), "kmeans_model.joblib")

def generate_and_train():
    np.random.seed(42)
    n_samples = 500
    
    income = np.random.uniform(30000, 500000, n_samples)
    
    fractions = []
    for _ in range(n_samples):
        r = np.random.rand()
        if r < 0.3:
            fractions.append(np.random.uniform(0.3, 0.5)) 
        elif r < 0.7:
            fractions.append(np.random.uniform(0.5, 0.8)) 
        else:
            fractions.append(np.random.uniform(0.8, 1.1)) 
            
    fractions = np.array(fractions)
    expenses = income * fractions
    savings = income - expenses
    savings_rate = np.where(income > 0, savings / income, 0)
    
    df = pd.DataFrame({
        "income": income,
        "expenses": expenses,
        "savings_rate": savings_rate
    })
    
    from sklearn.preprocessing import StandardScaler
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(df[['income', 'expenses', 'savings_rate']])
    
    kmeans = KMeans(n_clusters=3, random_state=42)
    kmeans.fit(scaled_features)
    
    centers = scaler.inverse_transform(kmeans.cluster_centers_)
    savings_centers = centers[:, 2]
    
    sorted_idx = np.argsort(savings_centers)
    spender_label = sorted_idx[0]
    balanced_label = sorted_idx[1]
    saver_label = sorted_idx[2]
    
    label_map = {
        spender_label: "High Spender",
        balanced_label: "Balanced User",
        saver_label: "High Saver"
    }
    
    model_data = {
        "kmeans": kmeans,
        "scaler": scaler,
        "label_map": label_map
    }
    
    joblib.dump(model_data, MODEL_PATH)
    print(f"Model trained and saved to {MODEL_PATH}")

def predict_category(income, expenses):
    if not os.path.exists(MODEL_PATH):
        generate_and_train()
        
    model_data = joblib.load(MODEL_PATH)
    kmeans = model_data["kmeans"]
    scaler = model_data["scaler"]
    label_map = model_data["label_map"]
    
    savings = income - expenses
    savings_rate = savings / income if income > 0 else 0
    
    features = np.array([[income, expenses, savings_rate]])
    scaled = scaler.transform(features)
    
    cluster = kmeans.predict(scaled)[0]
    return label_map[cluster]

if __name__ == "__main__":
    generate_and_train()
