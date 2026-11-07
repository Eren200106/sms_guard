"""4-тапсырма: SMS жиынын тазалау.

Пайдалану:  python -m ml.preprocess_sms
Кіріс:  data/processed/sms_raw.csv
Шығыс:  data/processed/sms_clean.csv  (id, text_raw, text_clean, label)
        docs/preprocessing_report.md   ("қадам - әсер еткен жазбалар саны")
"""
from __future__ import annotations

import pandas as pd

from .data.paths import DOCS, PROCESSED
from .preprocessing import normalize_sms


def run(remove_stopwords: bool = False) -> pd.DataFrame:
    src = PROCESSED / "sms_raw.csv"
    if not src.exists():
        raise FileNotFoundError("Алдымен `python -m ml.data.load_sms` орындаңыз.")
    df = pd.read_csv(src, encoding="utf-8", dtype={"text": str}, keep_default_na=False)
    report: list[tuple[str, str]] = [("Бастапқы жол саны", str(len(df)))]

    df = df.rename(columns={"text": "text_raw"})
    df["text_clean"] = df["text_raw"].map(lambda t: normalize_sms(t, remove_stopwords))

    n_changed = int((df["text_raw"] != df["text_clean"]).sum())
    report.append(("Мәтіні өзгерген жазбалар (нормализация)", str(n_changed)))
    for token in ["<url>", "<email>", "<phone>", "<money>", "<num>"]:
        report.append((f"Құрамында {token} бар", str(int(df["text_clean"].str.contains(token, regex=False).sum()))))

    empty = df["text_clean"].str.strip() == ""
    report.append(("Бос мәтін -> жойылды", str(int(empty.sum()))))
    df = df[~empty]

    dup_mask = df.duplicated(subset="text_clean", keep="first")
    by_class = df[dup_mask].label.value_counts().to_dict()
    report.append(("Дубликат (text_clean бойынша) -> жойылды, ham", str(by_class.get(0, 0))))
    report.append(("Дубликат (text_clean бойынша) -> жойылды, spam", str(by_class.get(1, 0))))
    df = df[~dup_mask]
    report.append(("Қорытынды жол саны", str(len(df))))

    out = PROCESSED / "sms_clean.csv"
    df[["id", "text_raw", "text_clean", "label"]].to_csv(out, index=False, encoding="utf-8")

    lines = ["# Предобработка SMS: отчёт о преобразованиях", "",
             "| Шаг | Число записей |", "|---|---|"]
    lines += [f"| {a} | {b} |" for a, b in report]
    DOCS.mkdir(exist_ok=True)
    (DOCS / "preprocessing_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print(f"\nСақталды: {out}")
    return df


if __name__ == "__main__":
    run()
