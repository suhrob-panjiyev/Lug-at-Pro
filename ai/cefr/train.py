# ai/cefr/train.py
from __future__ import annotations
from pathlib import Path
import re
import argparse

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score
import joblib

LEVEL_ORDER = ["A1", "A2", "B1", "B2", "C1", "C2"]

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DATA = BASE_DIR / "data" / "ENGLISH_CERF_WORDS.csv"
DEFAULT_MODEL = BASE_DIR / "models" / "cefr_model.joblib"


def clean_word(w: str) -> str:
    w = (w or "").strip().lower()
    w = re.sub(r"\s+", " ", w)
    w = re.sub(r"[^a-z0-9'\- ]", "", w)
    return w.strip()


def main(data_path: Path, out_path: Path):
    df = pd.read_csv(data_path)

    if "headword" not in df.columns or "CEFR" not in df.columns:
        raise ValueError(f"Kerakli ustun topilmadi. Kerak: headword, CEFR. Bor: {list(df.columns)}")

    df = df[["headword", "CEFR"]].copy()
    df["headword"] = df["headword"].astype(str).map(clean_word)
    df["CEFR"] = df["CEFR"].astype(str).str.strip().str.upper()

    df = df[df["CEFR"].isin(LEVEL_ORDER)]
    df = df[df["headword"].str.len() > 0]
    df = df.drop_duplicates(subset=["headword", "CEFR"])

    X = df["headword"].tolist()
    y = df["CEFR"].tolist()

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.15, random_state=42, stratify=y
    )

    pipe = Pipeline(
        steps=[
            ("tfidf", TfidfVectorizer(
                analyzer="char_wb",
                ngram_range=(3, 6),
                min_df=2
            )),
            ("clf", LogisticRegression(
                max_iter=4000,
                class_weight="balanced",
                solver="lbfgs"
            )),
        ]
    )

    pipe.fit(X_train, y_train)

    preds = pipe.predict(X_test)
    acc = accuracy_score(y_test, preds)

    print(f" Accuracy: {acc:.4f}")
    print(classification_report(y_test, preds, digits=4))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipe, out_path)
    print(f"\n Saved model: {out_path}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(DEFAULT_DATA), help="Dataset path")
    ap.add_argument("--out", default=str(DEFAULT_MODEL), help="Model output path")
    args = ap.parse_args()

    main(Path(args.data), Path(args.out))