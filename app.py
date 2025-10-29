# app.py
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import pandas as pd
import numpy as np
import pickle

BUNDLE_PATH = "laptop_price_bundle.pkl"

with open(BUNDLE_PATH, "rb") as f:
    saved = pickle.load(f)

model          = saved["model"]
encoder        = saved["encoder"]
scaler         = saved["scaler"]
categorical_cols = saved["categorical_cols"]
numeric_cols     = saved["numeric_cols"]

app = FastAPI()
templates = Jinja2Templates(directory="templates")

class LaptopFeatures(BaseModel):
    Company: str
    TypeName: str
    Ram: int
    Weight: float
    TouchScreen: int
    Ips: int
    Ppi: float
    Cpu_brand: str
    HDD: int
    SSD: int
    Gpu_brand: str
    Os: str

def prepare(df: pd.DataFrame) -> np.ndarray:
    # kolonları beklenen sıraya sabitle
    df = df.reindex(columns=categorical_cols + numeric_cols)

    # tip düzeltmeleri
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # basit doldurma
    df[numeric_cols] = df[numeric_cols].fillna(0)
    df[categorical_cols] = df[categorical_cols].fillna("Unknown")

    # encode + scale
    X_cat = encoder.transform(df[categorical_cols])
    X_num = scaler.transform(df[numeric_cols])
    X_ready = np.hstack([X_cat, X_num])
    return X_ready

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/predict")
async def predict(features: LaptopFeatures):
    df_new = pd.DataFrame([features.model_dump()])
    X_ready = prepare(df_new)
    raw = model.predict(X_ready)[0]
    final_price = np.expm1(raw)
    return {"predicted_price": float(final_price)}