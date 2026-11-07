"""10-тапсырма: URL деректер жиынын дайындау.

Қолдау: PhiUSIIL (бағандар URL, label; 1=заңды, 0=фишинг) - негізгі нұсқа
        Kaggle Malicious URLs (url, type: benign/phishing/defacement/malware) - балама.
Пайдалану:
    python -m ml.data.prepare_url                 # data/raw/ ішіндегі файлды өзі табады
    python -m ml.data.prepare_url --max-rows 80000
Нәтиже:
    data/processed/url_features.parquet (pyarrow жоқ болса .csv)
    data/processed/url_split.json       (бөлу индекстері)
    docs/url_eda.md                     (баланс + 6 негізгі белгі бойынша орташалар)
"""
from __future__ import annotations

import argparse
import json
import re

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit

from ml.url_features import (
    FEATURE_NAMES, URLValidationError, extract_url_features, registered_domain, validate_url,
)

from .paths import DOCS, PROCESSED, RAW

# Белгілеу артефакттары: PhiUSIIL-де заңды URL-дар көбіне https://www., фишингтер - жоқ.
# Модель "https/www" белгісін жаттап алмауы үшін схема мен www. алынып тасталады
# (бір түрге келтіру) және is_https белгісі модельден шығарылады.
ARTIFACT_PRONE_FEATURES = ["is_https"]

KEY_FEATURES = ["url_length", "num_subdomains", "num_suspicious_words",
                "domain_entropy", "num_special_chars", "has_ip"]


def find_raw_file():
    for name in ("PhiUSIIL_Phishing_URL_Dataset.csv", "malicious_phish.csv"):
        p = RAW / name
        if p.exists():
            return p
    raise FileNotFoundError(
        "data/raw/ ішінде URL жиыны жоқ. `python -m ml.data.download_datasets url` "
        "орындаңыз немесе PhiUSIIL / malicious_phish.csv файлын қолмен салыңыз."
    )


def load_labeled(path) -> pd.DataFrame:
    """Белгілерді екілік түрге келтіреді: 0 - қауіпсіз, 1 - фишинг/зиянды."""
    df = pd.read_csv(path, usecols=lambda c: c.lower() in {"url", "label", "type"})
    df.columns = [c.lower() for c in df.columns]
    if "label" in df.columns:          # PhiUSIIL: 1 = заңды, 0 = фишинг -> инверсия
        df["target"] = 1 - df["label"].astype(int)
    elif "type" in df.columns:         # Kaggle: benign -> 0, qалғаны -> 1
        # Негіздеме: phishing, malware, defacement - барлығы қауіпті сайттар.
        df["target"] = (df["type"].str.lower() != "benign").astype(int)
    else:
        raise ValueError("label немесе type бағаны табылмады")
    return df[["url", "target"]]


def unify_url(url: str) -> str:
    """Схема мен 'www.' алынады, домен кіші әріпке келтіріледі."""
    u = re.sub(r"^[a-zA-Z]+://", "", url.strip())
    u = re.sub(r"^www\.", "", u, flags=re.I)
    host, sep, rest = u.partition("/")
    return host.lower() + sep + rest


def clean(df: pd.DataFrame, max_rows: int | None, seed: int = 42) -> tuple[pd.DataFrame, dict]:
    log = {"initial": len(df)}
    df = df.dropna(subset=["url"])
    df["url"] = df["url"].astype(str).map(unify_url)
    log["after_dropna"] = len(df)

    def valid(u: str) -> bool:
        try:
            validate_url(u)
            return True
        except URLValidationError:
            return False

    df = df[df["url"].map(valid)]
    log["after_validation"] = len(df)
    df = df.drop_duplicates(subset="url")
    log["after_dedup"] = len(df)

    if max_rows and len(df) > max_rows:  # стратификацияланған ішкі таңдау
        df = df.groupby("target", group_keys=False).sample(frac=max_rows / len(df), random_state=seed)
        log["after_subsample"] = len(df)
    return df.reset_index(drop=True), log


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    feats = pd.DataFrame([extract_url_features(u) for u in df["url"]], columns=list(FEATURE_NAMES))
    out = pd.concat([df.reset_index(drop=True), feats], axis=1)
    out["domain"] = out["url"].map(registered_domain)
    return out.drop(columns=ARTIFACT_PRONE_FEATURES)


def group_split(df: pd.DataFrame, seed: int = 42) -> dict:
    """70/15/15, бір домен тек бір бөлікте (GroupShuffleSplit)."""
    groups = df["domain"].values
    gss1 = GroupShuffleSplit(n_splits=1, test_size=0.15, random_state=seed)
    trainval_idx, test_idx = next(gss1.split(df, groups=groups))
    gss2 = GroupShuffleSplit(n_splits=1, test_size=0.15 / 0.85, random_state=seed)
    tr_rel, val_rel = next(gss2.split(df.iloc[trainval_idx], groups=groups[trainval_idx]))
    split = {
        "train": sorted(int(i) for i in trainval_idx[tr_rel]),
        "val": sorted(int(i) for i in trainval_idx[val_rel]),
        "test": sorted(int(i) for i in test_idx),
    }
    # Домен қиылыспауын тексеру
    d = {k: set(groups[v]) for k, v in split.items()}
    assert not (d["train"] & d["test"]) and not (d["train"] & d["val"]) and not (d["val"] & d["test"]), \
        "Бөліктер арасында домен қиылысты!"
    return split


def write_eda(df: pd.DataFrame, split: dict, log: dict) -> None:
    lines = ["# EDA: URL жиыны", "", "## Тазалау журналы", "", "| Қадам | Жол саны |", "|---|---|"]
    lines += [f"| {k} | {v} |" for k, v in log.items()]
    lines += ["", "## Класс балансы", "", "| Класс | Саны | % |", "|---|---|---|"]
    vc = df["target"].value_counts()
    for cls, name in [(0, "0 - қауіпсіз"), (1, "1 - фишинг/зиянды")]:
        lines.append(f"| {name} | {vc.get(cls, 0)} | {vc.get(cls, 0) / len(df) * 100:.2f} |")
    lines += ["", "## 6 негізгі белгінің орташа мәні (класс бойынша)", "",
              "| Белгі | Қауіпсіз (0) | Фишинг (1) |", "|---|---|---|"]
    means = df.groupby("target")[KEY_FEATURES].mean().round(3)
    for f in KEY_FEATURES:
        lines.append(f"| {f} | {means.loc[0, f]} | {means.loc[1, f]} |")
    lines += ["", "## Бөліктер", "", "| Бөлік | Жол | Домен |", "|---|---|---|"]
    for k, idx in split.items():
        lines.append(f"| {k} | {len(idx)} | {df.iloc[idx]['domain'].nunique()} |")
    lines += ["", f"`{', '.join(ARTIFACT_PRONE_FEATURES)}` белгісі модельден шығарылды "
              "(схема/www бір түрге келтірілген: белгілеу артефактісі)."]
    DOCS.mkdir(exist_ok=True)
    (DOCS / "url_eda.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-rows", type=int, default=100_000)
    args = ap.parse_args()

    raw = load_labeled(find_raw_file())
    df, log = clean(raw, args.max_rows)
    df = build_features(df)
    split = group_split(df)

    PROCESSED.mkdir(parents=True, exist_ok=True)
    try:
        df.to_parquet(PROCESSED / "url_features.parquet", index=False)
        print("Сақталды: url_features.parquet")
    except ImportError:
        df.to_csv(PROCESSED / "url_features.csv", index=False)
        print("pyarrow жоқ: url_features.csv сақталды (pip install pyarrow)")
    (PROCESSED / "url_split.json").write_text(json.dumps(split), encoding="utf-8")
    write_eda(df, split, log)


if __name__ == "__main__":
    main()
