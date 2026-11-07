"""3-тапсырма: UCI SMS Spam Collection жүктеу.

Пайдалану:  python -m ml.data.load_sms
Нәтиже: data/processed/sms_raw.csv  (id, text, label; 0=ham, 1=spam)
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from .paths import PROCESSED, RAW

DEFAULT_FILE = RAW / "SMSSpamCollection"


def load_sms(path: Path | str = DEFAULT_FILE, encoding: str | None = None) -> pd.DataFrame:
    """Файлды оқиды (бөлгіш - табуляция) және id, text, label бағандарын қайтарады.

    Кодировка анық тексеріледі: алдымен utf-8, болмаса latin-1 (қате болса да құлап қалмайды).
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"{path} табылмады. `python -m ml.data.download_datasets sms` орындаңыз "
            "немесе файлды data/raw/ ішіне қолмен салыңыз."
        )
    encodings = [encoding] if encoding else ["utf-8", "latin-1"]
    last_err = None
    for enc in encodings:
        try:
            df = pd.read_csv(
                path, sep="\t", header=None, names=["label_str", "text"],
                encoding=enc, quoting=3, dtype=str, keep_default_na=False,
            )
            break
        except UnicodeDecodeError as err:
            last_err = err
    else:
        raise last_err  # type: ignore[misc]

    df["label"] = df["label_str"].str.strip().str.lower().map({"ham": 0, "spam": 1})
    if df["label"].isna().any():
        bad = df.loc[df["label"].isna(), "label_str"].unique()[:5]
        raise ValueError(f"Белгісіз белгілер табылды: {list(bad)}")
    df["label"] = df["label"].astype(int)
    df.insert(0, "id", range(len(df)))
    return df[["id", "text", "label"]]


def describe(df: pd.DataFrame) -> None:
    print("Жол саны:", len(df))
    print("\nБағандар типтері:\n", df.dtypes)
    for lab, name in [(0, "ham (қауіпсіз)"), (1, "spam (алаяқтық)")]:
        print(f"\n--- {name}: 5 мысал ---")
        for t in df[df.label == lab].text.head(5):
            print(" •", t[:120])
    print("\nКласс таралуы:\n", df.label.value_counts().rename({0: "ham", 1: "spam"}))
    print("\nПайыз:\n", (df.label.value_counts(normalize=True) * 100).round(2))


def main() -> None:
    df = load_sms()
    describe(df)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    out = PROCESSED / "sms_raw.csv"
    df.to_csv(out, index=False, encoding="utf-8")
    print(f"\nСақталды: {out}")


if __name__ == "__main__":
    main()
