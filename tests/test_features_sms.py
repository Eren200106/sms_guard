import pandas as pd

from ml.features_sms import ManualFeatures, build_sms_vectorizer, make_split
from ml.rules import detect_groups


def _df():
    ham = [f"see you at the cafe number {i} tomorrow" for i in range(40)]
    spam = [f"WIN a prize now!!! claim your gift card {i} at www.x{i}.example" for i in range(40)]
    return pd.DataFrame({"text_raw": ham + spam, "label": [0] * 40 + [1] * 40})


def test_split_sizes_and_disjoint():
    df = _df()
    s = make_split(df)
    assert len(s["train"]) + len(s["val"]) + len(s["test"]) == len(df)
    assert not set(s["train"]) & set(s["test"])
    assert not set(s["train"]) & set(s["val"])


def test_vectorizer_fit_on_train_only_shapes():
    df = _df()
    s = make_split(df)
    vec = build_sms_vectorizer()
    Xtr = vec.fit_transform(df.text_raw.loc[s["train"]])
    Xva = vec.transform(df.text_raw.loc[s["val"]])
    assert Xtr.shape[0] == len(s["train"]) and Xva.shape[0] == len(s["val"])
    assert Xtr.shape[1] == Xva.shape[1]


def test_manual_features_count_and_values():
    m = ManualFeatures().fit([""])
    out = m.transform(["URGENT!!! Your card is blocked: http://x.example"])
    assert out.shape == (1, 6)
    assert out[0, 2] == 3        # '!' саны
    assert out[0, 3] == 1        # <url> бар
    assert out[0, 5] >= 2        # URGENCY + ACCOUNT_BLOCK/BANK_CARD


def test_rules_detect_code_request_ru_kk_en():
    assert "CODE_REQUEST" in detect_groups("Назовите код из SMS")
    assert "CODE_REQUEST" in detect_groups("Кодты айтыңыз")
    assert "CODE_REQUEST" in detect_groups("Please share the code")
    assert detect_groups("Привет, как дела?") == []
