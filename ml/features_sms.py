"""6-тапсырма: мәтіннен белгілер (TF-IDF сөз + символ N-грамм + қолмен белгілер).

Пайдалану:  python -m ml.features_sms
Нәтиже: data/processed/sms_split.json және консольге өлшемдер, топ-15 белгі.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.preprocessing import FunctionTransformer, StandardScaler

from .data.paths import PROCESSED
from .preprocessing import normalize_sms
from .rules import count_groups

RANDOM_STATE = 42


# ---- модуль деңгейіндегі функциялар (joblib/pickle үшін lambda болмауы керек) ----
def _normalize_many(texts):
    return [normalize_sms(t) for t in texts]


def _normalize_many_nostop(texts):
    return [normalize_sms(t, remove_stopwords=True) for t in texts]


class ManualFeatures(BaseEstimator, TransformerMixin):
    """Шикі мәтіннен 6 қолмен белгі: ұзындық, бас әріп үлесі, '!' саны,
    <url> бар ма, <money> бар ма, сөздік топтарының саны."""

    names = ["length", "upper_ratio", "num_exclaim", "has_url", "has_money", "rule_groups"]

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        rows = []
        for raw in X:
            raw = raw if isinstance(raw, str) else ""
            clean = normalize_sms(raw)
            letters = [c for c in raw if c.isalpha()]
            upper = sum(c.isupper() for c in letters) / len(letters) if letters else 0.0
            rows.append([
                len(raw), upper, raw.count("!"),
                int("<url>" in clean), int("<money>" in clean), count_groups(raw),
            ])
        return np.asarray(rows, dtype=float)

    def get_feature_names_out(self, input_features=None):
        return np.asarray(self.names)


def build_sms_vectorizer(use_char: bool = True, remove_stopwords: bool = False) -> Pipeline:
    """Шикі мәтін -> белгілер матрицасы. Бәрі Pipeline ішінде: fit тек train-де жасалады."""
    norm = _normalize_many_nostop if remove_stopwords else _normalize_many
    word = Pipeline([
        ("norm", FunctionTransformer(norm, validate=False)),
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_df=0.95, sublinear_tf=True)),
    ])
    parts = [("word", word)]
    if use_char:
        char = Pipeline([
            ("norm", FunctionTransformer(norm, validate=False)),
            ("tfidf", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=2, sublinear_tf=True)),
        ])
        parts.append(("char", char))
    manual = Pipeline([("feat", ManualFeatures()), ("scale", StandardScaler())])
    parts.append(("manual", manual))
    return Pipeline([("features", FeatureUnion(parts))])


def make_split(df: pd.DataFrame) -> dict:
    """Стратификацияланған 70/15/15, random_state=42. Индекстер df.index бойынша."""
    idx = df.index.to_numpy()
    train_idx, rest_idx = train_test_split(
        idx, test_size=0.30, stratify=df["label"], random_state=RANDOM_STATE)
    val_idx, test_idx = train_test_split(
        rest_idx, test_size=0.50, stratify=df.loc[rest_idx, "label"], random_state=RANDOM_STATE)
    return {"train": sorted(map(int, train_idx)), "val": sorted(map(int, val_idx)),
            "test": sorted(map(int, test_idx))}


def top_features_by_class(vec: Pipeline, X_train, y_train, k: int = 15) -> dict:
    """Әр класс үшін орташа TF-IDF жоғары k сөздік белгі."""
    word_block = vec.named_steps["features"].transformer_list[0][1]
    Xw = word_block.transform(X_train)
    names = word_block.named_steps["tfidf"].get_feature_names_out()
    y = np.asarray(y_train)
    out = {}
    for cls, name in [(0, "ham"), (1, "spam")]:
        mean = np.asarray(Xw[y == cls].mean(axis=0)).ravel()
        out[name] = [(names[i], round(float(mean[i]), 4)) for i in mean.argsort()[::-1][:k]]
    return out


def main() -> None:
    src = PROCESSED / "sms_clean.csv"
    if not src.exists():
        raise FileNotFoundError("Алдымен `python -m ml.preprocess_sms` орындаңыз.")
    df = pd.read_csv(src, encoding="utf-8", keep_default_na=False)
    split = make_split(df)
    (PROCESSED / "sms_split.json").write_text(json.dumps(split), encoding="utf-8")

    X, y = df["text_raw"], df["label"]
    Xtr, ytr = X.loc[split["train"]], y.loc[split["train"]]
    vec = build_sms_vectorizer()
    Xtr_m = vec.fit_transform(Xtr)                      # fit тек train-де
    Xva_m = vec.transform(X.loc[split["val"]])
    Xte_m = vec.transform(X.loc[split["test"]])
    print("Өлшемдер:", "train", Xtr_m.shape, "| val", Xva_m.shape, "| test", Xte_m.shape)
    for cls, items in top_features_by_class(vec, Xtr, ytr).items():
        print(f"\nТоп-15 ({cls}):")
        for term, val in items:
            print(f"  {term:<25} {val}")


if __name__ == "__main__":
    main()
