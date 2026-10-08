"""
train_models.py — Train all 4 ML models (v2)

Models upgraded:
  Authenticity  : Isolation Forest → XGBoost binary classifier (AUC-based)
  Growth        : Gradient Boosting → XGBoost + 5 trend-decomposition features
  Brand Match   : TF-IDF cosine → sentence-transformers semantic embeddings
  Ratefluencer  : XGBoost → XGBoost + 8 interaction features + hyperparameter search

Run once before starting the server:
  python train_models.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import pandas as pd

from models.authenticity       import train as train_auth
from models.growth             import train as train_growth
from models.brand_match        import train as train_brand
from models.ratefluencer_score import train as train_rf


def main():
    print("=" * 60)
    print("RATEFLUENCER v2 — Training upgraded ML models")
    print("=" * 60)

    df = pd.read_csv(os.path.join(os.path.dirname(__file__), "influencer_dataset.csv"))
    print(f"\nDataset: {len(df)} profiles, {len(df.columns)} columns\n")

    print("[1/4] Authenticity — XGBoost binary classifier (12 features)...")
    train_auth(df)

    print("\n[2/4] Growth — XGBoost + trend decomposition (16 features)...")
    train_growth(df)

    print("\n[3/4] Brand Match — sentence-transformer semantic embeddings...")
    train_brand(df)

    print("\n[4/4] Ratefluencer Score — XGBoost + interaction features (24 total)...")
    train_rf(df)

    print("\n" + "=" * 60)
    print("All models trained and saved!")
    print("Start server:  python -m uvicorn main:app --reload --port 8001")
    print("API docs:      http://localhost:8001/docs")
    print("=" * 60)


if __name__ == "__main__":
    main()
