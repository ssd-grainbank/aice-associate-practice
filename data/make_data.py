#!/usr/bin/env python3
"""시험용 데이터셋 생성기. 한 번 실행하면 data/ 안에 CSV들이 만들어집니다."""
import numpy as np
import pandas as pd
from pathlib import Path

OUT = Path(__file__).resolve().parent
rng = np.random.default_rng(42)


def customers(n=300):
    """분류용 — 이탈 예측. 결측치·이상치·범주형 포함."""
    region = rng.choice(["Seoul", "Busan", "Daegu", "Incheon"], n, p=[.45, .25, .17, .13])
    grade = rng.choice(["bronze", "silver", "gold"], n, p=[.5, .35, .15])
    age = rng.normal(41, 13, n).clip(19, 78).round()
    visits = rng.poisson(6, n)
    spend = (age * 900 + visits * 4200 + rng.normal(0, 12000, n)).clip(5000).round(-2)
    satisfaction = rng.integers(1, 6, n)
    tenure = rng.integers(1, 73, n)

    score = (-0.05 * age + 0.35 * (5 - satisfaction) - 0.12 * visits
             - 0.00002 * spend + 0.03 * (72 - tenure) + rng.normal(0, .8, n))
    churn = (score > np.percentile(score, 72)).astype(int)

    df = pd.DataFrame({
        "customer_id": [f"C{i:04d}" for i in range(1, n + 1)],
        "age": age, "region": region, "grade": grade,
        "tenure_months": tenure, "visits": visits,
        "monthly_spend": spend, "satisfaction": satisfaction,
        "churn": churn,
    })

    # 결측치 심기 (전처리 문제용)
    for col, k in [("age", 18), ("monthly_spend", 12), ("satisfaction", 9), ("region", 6)]:
        df.loc[rng.choice(n, k, replace=False), col] = np.nan
    # 이상치 심기 (IQR 문제용)
    df.loc[rng.choice(n, 5, replace=False), "monthly_spend"] = rng.uniform(900000, 1500000, 5).round(-2)
    # 중복행 심기 (품질 점검 문제용)
    df = pd.concat([df, df.iloc[[3, 17, 42]]], ignore_index=True)
    return df


def houses(n=250):
    """회귀용 — 집값 예측."""
    area = rng.normal(84, 26, n).clip(29, 190).round(1)
    rooms = np.clip((area / 26 + rng.normal(0, .7, n)).round(), 1, 6).astype(int)
    age_y = rng.integers(0, 36, n)
    dist = rng.exponential(1.6, n).clip(.1, 9).round(2)
    floor = rng.integers(1, 26, n)
    price = (area * 780 + rooms * 2400 - age_y * 640 - dist * 3100
             + floor * 190 + rng.normal(0, 5200, n) + 42000).clip(15000).round(-2)

    df = pd.DataFrame({
        "area": area, "rooms": rooms, "building_age": age_y,
        "distance_station": dist, "floor": floor, "price": price,
    })
    df.loc[rng.choice(n, 11, replace=False), "area"] = np.nan
    df.loc[rng.choice(n, 7, replace=False), "distance_station"] = np.nan
    return df


def sales(n=400):
    """집계용 — groupby·정렬 연습."""
    dates = pd.date_range("2025-01-01", periods=120)
    df = pd.DataFrame({
        "date": rng.choice(dates, n),
        "store": rng.choice(["강남점", "홍대점", "부산점", "대구점"], n),
        "category": rng.choice(["음료", "베이커리", "샌드위치", "디저트"], n),
        "quantity": rng.integers(1, 25, n),
        "unit_price": rng.choice([3500, 4200, 5800, 6500, 8900], n),
    })
    df["amount"] = df["quantity"] * df["unit_price"]
    df.loc[rng.choice(n, 14, replace=False), "quantity"] = np.nan
    return df.sort_values("date").reset_index(drop=True)


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    files = {"customers.csv": customers(), "houses.csv": houses(), "sales.csv": sales()}
    for name, df in files.items():
        df.to_csv(OUT / name, index=False)
        print(f"{name:16} {df.shape[0]:>4}행 {df.shape[1]:>2}열  결측 {int(df.isnull().sum().sum()):>3}개")
